from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from mypy_boto3_sqs.client import SQSClient
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from src.DemandForecaster import DemandForecaster
import boto3

INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "dev-Inventory")
MENU_TABLE = os.getenv("MENU_TABLE", "dev-Menu")
FORECAST_QUEUE = os.getenv("FORECAST_QUEUE_URL", None)


class RecommendationEngine:

    def __init__(self):
        self.sqs: SQSClient = boto3.client("sqs")
        dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
        self.inventory_table: Table = dynamodb.Table(INVENTORY_TABLE)
        self.menu_table: Table = dynamodb.Table(MENU_TABLE)

    def recommend(self, predicted_sales: dict) -> dict:
        predicted_sales: dict = DemandForecaster().predict_tmr_sales()
        recommendations: dict = self.generate_recommendations(predicted_sales)
        self.notify(recommendations)


    def notify(self, payload: dict) -> None:
        self.sqs.send_message(
            QueueUrl=FORECAST_QUEUE,
            MessageBody=json.dumps(payload)
        )

    def generate_recommendations(self, predicted_sales: dict[str, float]) -> dict:
        ingredient_demand = self.calculate_ingredient_demand(predicted_sales)
        inventory = self.get_inventory_by_ingredient(ingredient_demand.keys())

        message = {
            "need": {},
            "expiring": {}
        }

        tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)

        for ingredient_name, required_quantity in ingredient_demand.items():
            inventory_item = inventory.get(ingredient_name)

            if inventory_item is None:
                message["need"][ingredient_name] = float(required_quantity)
                continue

            available_quantity = Decimal(str(inventory_item.get("quantity", 0)))
            expiration_date = inventory_item.get("expiration_date")

            if available_quantity < required_quantity:
                shortage = required_quantity - available_quantity
                message["need"][ingredient_name] = float(shortage)
                continue

            if self.expires_within_one_day(expiration_date, tomorrow):
                delta = available_quantity - required_quantity

                if delta > 0:
                    message["expiring"][ingredient_name] = float(delta)

        return message


    def calculate_ingredient_demand(self, predicted_sales: dict[str, float]) -> dict[str, Decimal]:
        ingredient_demand = defaultdict(Decimal)

        for menu_item, predicted_quantity in predicted_sales.items():
            if predicted_quantity <= 0:
                continue

            recipe = self.get_recipe(self, menu_item)

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


    def get_inventory_by_ingredient(self, ingredient_names) -> dict:
        inventory = {}

        for ingredient_name in ingredient_names:
            response = self.inventory_table.get_item(
                Key={"ingredient_name": ingredient_name}
            )

            item = response.get("Item")

            if item:
                inventory[ingredient_name] = item

        return inventory


    def expires_within_one_day(expiration_date: str | None, forecast_date) -> bool:
        if not expiration_date:
            return False

        expiration = datetime.fromisoformat(expiration_date).date()

        return expiration <= forecast_date + timedelta(days=1)
