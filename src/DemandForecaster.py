from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key
import os
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
import boto3
from collections import defaultdict
from datetime import timedelta
from boto3.dynamodb.conditions import Key
from typing import List

MENU_TABLE = os.getenv("MENU_TABLE", "dev-Menu")
SALES_TABLE = os.getenv("SALES_TABLE", "dev-Sales")


class DemandForecaster:

    def __init__(self):
        dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
        self.menu_table: Table = dynamodb.Table(MENU_TABLE)
        self.sales_table: Table = dynamodb.Table(SALES_TABLE)

    def get_tomorrows_day_of_week(self) -> str:
        tomorrow_utc = datetime.now(timezone.utc) + timedelta(days=1)
        return tomorrow_utc.strftime("%A").lower()


    def generate_cutoff_day(self, n: int = 4) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=7 * n)


    def get_all_menu_items(self) -> list[str]:
        response = self.menu_table.scan(
            ProjectionExpression="menu_item"
        )

        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = self.menu_table.scan(
                ProjectionExpression="menu_item",
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))

        return [item["menu_item"] for item in items]

    def get_sales(self, day_of_week: str, cutoff_day: datetime) -> list:
        response = self.sales_table.query(
            IndexName="SalesByDayOfWeek",
            KeyConditionExpression=(
                Key("dayOfWeek").eq(day_of_week) &
                Key("date").gte(cutoff_day.isoformat())
            )
        )

        sales_items: list = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = self.sales_table.query(
                IndexName="SalesByDayOfWeek",
                KeyConditionExpression=(
                    Key("day_of_week").eq(day_of_week) &
                    Key("date").gte(cutoff_day.isoformat())
                ),
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            sales_items.extend(response.get("Items", []))
        return sales_items

    def predict_tmr_sales(self) -> dict[str, float]:
        num_samples: int = 4
        day_of_week: str = self.get_tomorrows_day_of_week()
        cutoff_day: datetime = self.generate_cutoff_day(num_samples)
        sales_items: list = self.get_sales(day_of_week, cutoff_day)

        menu_items: List[str] = self.get_all_menu_items()

        totals_by_dish = defaultdict(float)

        for sale in sales_items:
            menu_item = sale["menu_item"]
            quantity = float(sale["quantity"])

            totals_by_dish[menu_item] += quantity

        averages = {}

        for menu_item in menu_items:
            averages[menu_item] = round(totals_by_dish[menu_item] / num_samples)

        return averages