from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from mypy_boto3_sqs.client import SQSClient
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from DemandForecaster import DemandForecaster
import boto3
from models.src.restaurant_models.inventory_classes import PurchasedIngredient
from typing import List
from datetime import date
from logging import Logger, getLogger

LOG: Logger = getLogger(__name__)

INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "dev-Inventory")
MENU_TABLE = os.getenv("MENU_TABLE", "dev-Menu")
SUPPLY_GAP_QUEUE = os.getenv("SUPPLY_GAP_QUEUE_URL", "dev-supply-gap-queue")


class SupplyGapAnalyzer:

    def __init__(self):
        self.sqs: SQSClient = boto3.client("sqs")
        dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
        self.inventory_table: Table = dynamodb.Table(INVENTORY_TABLE)
        self.menu_table: Table = dynamodb.Table(MENU_TABLE)

    def send_supply_gap(self) -> dict:
        predicted_sales: dict = DemandForecaster().predict_tmr_sales()
        supply_gap_report: dict = self.calculate_supply_gap(predicted_sales)
        LOG.info(f"Supply Gap Report:\n{supply_gap_report}")
        self.notify(supply_gap_report)


    def notify(self, payload: dict) -> None:
        self.sqs.send_message(
            QueueUrl=SUPPLY_GAP_QUEUE,
            MessageBody=json.dumps(payload)
        )

    def calculate_supply_gap(self, predicted_sales: dict[str, float]) -> dict:
        ingredient_demand: dict[str, Decimal] = self.calculate_ingredient_demand(predicted_sales)
        LOG.info(f"Ingr Demand: {ingredient_demand}")
        inventory: List[PurchasedIngredient] = self.get_full_inventory()
        LOG.info(f"Current Ingr Inventory: {inventory}")

        message = {
            "need": {},
            "expiring": {}
        }

        for ingr_obj in inventory:
            required_amnt: Decimal = ingredient_demand.get(ingr_obj.ingredient, Decimal("0"))
            available_amnt = Decimal(ingr_obj.quantity)

            if available_amnt < required_amnt:
                shortage = required_amnt - available_amnt
                message["need"][ingr_obj.ingredient] = float(shortage)
            elif available_amnt == required_amnt:
                continue
            elif self.expires_within_one_day(ingr_obj.expiration_date):
                delta = available_amnt - required_amnt
                message["expiring"][ingr_obj.ingredient] = float(delta)

        return message


    def calculate_ingredient_demand(self, predicted_sales: dict[str, float]) -> dict[str, Decimal]:
        ingredient_demand = defaultdict(Decimal)

        for menu_item, predicted_quantity in predicted_sales.items():
            if predicted_quantity <= 0:
                continue

            recipe = self.get_recipe(menu_item)
            LOG.info(f"Recipe: {recipe}")

            for ingredient, amount_per_menu_item in recipe.items():
                ingredient_demand[ingredient] += (
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

        return item.get("recipe", {})


    def get_full_inventory(self) -> List[PurchasedIngredient]:
        items: List[PurchasedIngredient] = []

        response = self.inventory_table.scan()
        items.extend(response.get("Items", []))

        while "LastEvaluatedKey" in response:
            response = self.inventory_table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))
        return [PurchasedIngredient(**item) for item in items]


    def expires_within_one_day(self, expiration_date: date | None) -> bool:
        if not expiration_date:
            return False
        return expiration_date <= (datetime.now(timezone.utc).date() + timedelta(days=1))
