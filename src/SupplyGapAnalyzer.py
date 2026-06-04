from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from mypy_boto3_sqs.client import SQSClient
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from DemandForecaster import DemandForecaster
import boto3
from typing import Dict, List
from logging import Logger, getLogger

LOG: Logger = getLogger(__name__)

INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "dev-Inventory")
MENU_TABLE = os.getenv("MENU_TABLE", "dev-Menu")
FORECAST_QUEUE = os.getenv("FORECAST_QUEUE_URL", None)


class SupplyGapAnalyzer:

    def __init__(self):
        self.sqs: SQSClient = boto3.client("sqs")
        dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
        self.inventory_table: Table = dynamodb.Table(INVENTORY_TABLE)
        self.menu_table: Table = dynamodb.Table(MENU_TABLE)

    def send_supply_gap(self) -> dict:
        predicted_sales: dict = DemandForecaster().predict_tmr_sales()
        supply_gap_report: dict = self.calculate_supply_gap(predicted_sales)
        LOG.debug(f"Supply Gap Report:\n{supply_gap_report}")
        self.notify(supply_gap_report)


    def notify(self, payload: dict) -> None:
        self.sqs.send_message(
            QueueUrl=FORECAST_QUEUE,
            MessageBody=json.dumps(payload)
        )

    def calculate_supply_gap(self, predicted_sales: dict[str, float]) -> dict:
        ingredient_demand: dict[str, Decimal] = self.calculate_ingredient_demand(predicted_sales)
        inventory: Dict[str, dict] = self.get_full_inventory(list(predicted_sales.keys()))

        message = {
            "need": {},
            "expiring": {}
        }

        tomorrow: datetime = datetime.now(timezone.utc).date() + timedelta(days=1)

        for ingredient, inventory_item in inventory.items():
            required_amnt: Decimal = ingredient_demand.get(ingredient)
            available_amnt = Decimal(inventory_item.get("quantity", 0))
            expiration_date = inventory_item.get("expiration_date")

            if available_amnt < required_amnt:
                shortage = required_amnt - available_amnt
                message["need"][ingredient] = float(shortage)
            elif available_amnt == required_amnt:
                continue
            elif self.expires_within_one_day(expiration_date, tomorrow):
                delta = available_amnt - required_amnt
                message["expiring"][ingredient] = float(delta)

        return message


    def calculate_ingredient_demand(self, predicted_sales: dict[str, float]) -> dict[str, Decimal]:
        ingredient_demand = defaultdict(Decimal)

        for menu_item, predicted_quantity in predicted_sales.items():
            if predicted_quantity <= 0:
                continue

            recipe = self.get_recipe(menu_item)

            for ingredient_name, amount_per_menu_item in recipe.items():
                ingredient_demand[ingredient_name] += (
                    Decimal(str(amount_per_menu_item)) *
                    Decimal(str(predicted_quantity))
                )

        return dict(ingredient_demand)


    def get_recipe(self, menu_item: str) -> dict:
        response = self.menu_table.get_item(
            Key={"menu_item": menu_item}
        )

        item = response.get("Item")

        if not item:
            return {}

        return item.get("ingredients", {})


    def get_full_inventory(self, ingredients: List[str]) -> Dict[str, dict]:
        inventory = {}

        for ingredient in ingredients:
            response = self.inventory_table.get_item(
                Key={"ingredient": ingredient}
            )

            item = response.get("Item")

            if item:
                inventory[ingredient] = item
            else:
                inventory[ingredient] = {
                    "ingredient": ingredient,
                    "quantity": 0,
                    "unit": None,
                    "expiration_date": None
                }
        return inventory


    def expires_within_one_day(expiration_date: str | None, ref_date: datetime) -> bool:
        if not expiration_date:
            return False

        expiration = datetime.fromisoformat(expiration_date).date()
        return expiration <= ref_date + timedelta(days=1)
