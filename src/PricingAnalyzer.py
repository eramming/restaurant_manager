from __future__ import annotations
import json
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_sns.client import SNSClient
from KrogerClient import KrogerClient, PriceResult


INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "dev-Inventory")
MENU_TABLE = os.getenv("MENU_TABLE", "dev-Menu")
SNS_ARN = os.getenv("PRICE_REPORT_SNS_ARN", None)

class PricingAnalyzer:

    def __init__(self):
        self.sns: SNSClient = boto3.client("sns")
        self.sns_topic_arn: str = SNS_ARN
        dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
        self.inventory_table: Table = dynamodb.Table(INVENTORY_TABLE)
        self.menu_table: Table = dynamodb.Table(MENU_TABLE)
        self.kroger_client: KrogerClient = KrogerClient()
        
    
    def analyze_and_send(self, recommendations: dict[str, dict[str, float]]) -> dict[str, Any]:
        needed_report = self._analyze_needed_ingredients(recommendations.get("need", {}))
        expiring_report = self._analyze_expiring_ingredients(recommendations.get("expiring", {}))

        final_report = {
            "neededPriceChanges": needed_report,
            "expiringLosses": expiring_report,
        }

        self._send_sns_message(subject="Inventory Pricing Analysis", message=final_report)
        return final_report

    def _analyze_needed_ingredients(self, needed: dict[str, float]) -> list[dict[str, Any]]:
        report = []

        for ingredient, quantity in needed.items():
            price_result: PriceResult = self.kroger_client.price_of(ingredient)
            previous_price = self._get_previous_price(ingredient)

            price_difference = None
            percent_change = None

            if previous_price is not None:
                price_difference = self._money(price_result.unit_price - previous_price)
                percent_change = self._money(
                    (price_difference / previous_price) * Decimal("100")
                )

            self._update_latest_price(ingredient, price_result.unit_price)
            report.append(
                {
                    "ingredient": ingredient,
                    "quantityNeeded": float(quantity),
                    "currentUnitPrice": float(price_result.unit_price),
                    "previousUnitPrice": float(previous_price) if previous_price is not None else None,
                    "priceDifference": float(price_difference) if price_difference is not None else None,
                    "percentChange": float(percent_change) if percent_change is not None else None,
                    "matchedProduct": price_result.product_description,
                }
            )

        return report

    def _analyze_expiring_ingredients(self, expiring: dict[str, float]) -> list[dict[str, Any]]:
        report = []

        for ingredient, quantity in expiring.items():
            quantity_decimal = Decimal(str(quantity))
            price_result: PriceResult = self.kroger_client.price_of(ingredient)
            potential_loss = self._money(quantity_decimal * price_result.unit_price)

            report.append(
                {
                    "ingredient": ingredient,
                    "quantityExpiring": float(quantity_decimal),
                    "currentUnitPrice": float(price_result.unit_price),
                    "potentialLoss": float(potential_loss),
                    "matchedProduct": price_result.product_description,
                }
            )

        return report

    

    def _get_previous_price(self, ingredient: str) -> Decimal | None:
        response = self.inventory_table.get_item(
            Key={"ingredient": ingredient}
        )

        item = response.get("Item")
        if not item:
            return None
        previous_price = item.get("latest_price")

        if previous_price is None:
            return None

        return Decimal(str(previous_price))

    def _update_latest_price(self, ingredient: str, unit_price: Decimal) -> None:
        self.inventory_table.update_item(
            Key={"ingredient": ingredient},
            UpdateExpression="SET latest_price = :price",
            ExpressionAttributeValues={
                ":price": unit_price,
            }
        )

    def _send_sns_message(self, subject: str, message: dict[str, Any]) -> str:
        response = self.sns.publish(
            TopicArn=self.sns_topic_arn,
            Subject=subject,
            Message=json.dumps(message, indent=2, default=str),
        )

        return response["MessageId"]

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


if __name__ == "__main__":
    analyzer = PricingAnalyzer()

    sample_recommendations = {
        "need": {
            "tomatoes": 7,
            "squash": 3,
        },
        "expiring": {
            "lettuce": 5,
        },
    }

    result = analyzer.analyze_and_send(sample_recommendations)
    print(json.dumps(result, indent=2))
