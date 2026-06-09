import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
import os
from typing import List
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import random
from decimal import Decimal
from logging import Logger, getLogger

LOG: Logger = getLogger(__name__)


INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "dev-Inventory")
MENU_TABLE = os.getenv("MENU_TABLE", "dev-Menu")
SALES_TABLE = os.getenv("SALES_TABLE", "dev-Sales")
dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
inventory_table: Table = dynamodb.Table(INVENTORY_TABLE)
menu_table: Table = dynamodb.Table(MENU_TABLE)
sales_table: Table = dynamodb.Table(SALES_TABLE)

today: datetime = datetime.now(timezone.utc).date()
tomorrow: datetime = today + timedelta(days=1)

def decimal(x: float) -> Decimal:
    return Decimal(str(x))

inventory = [
    {
        "ingredient": "noodles",
        "quantity": 25,
        "unit": "boxes",
        "latest_price": decimal(3.25),
        "expiration_date": tomorrow.strftime("%Y-%m-%d")
    },
    {
        "ingredient": "sauce",
        "quantity": 4,
        "unit": "jars",
        "latest_price": decimal(4.75),
        "expiration_date": "2026-06-12"
    },
    {
        "ingredient": "cheese",
        "quantity": 1,
        "unit": "lb",
        "latest_price": decimal(4.00),
        "expiration_date": "2026-06-12"
    },
    {
        "ingredient": "pepperoni",
        "quantity": 3,
        "unit": "lb",
        "latest_price": decimal(7.50),
        "expiration_date": "2026-06-12"
    },
    {
        "ingredient": "ham",
        "quantity": 7,
        "unit": "lb",
        "latest_price": decimal(9.50),
        "expiration_date": "2026-06-12"
    },
    {
        "ingredient": "salami",
        "quantity": 30,
        "unit": "lb",
        "latest_price": decimal(11.25),
        "expiration_date": "2026-06-12"
    },
    {
        "ingredient": "bread",
        "quantity": 12,
        "unit": "loaf",
        "latest_price": decimal(3),
        "expiration_date": "2026-06-12"
    }
]

sale_history = []
date = today - timedelta(days=28)
while date != today:
    sales_per_day: int = random.randint(2, 6)
    for sale in range(sales_per_day):
        dish: str = random.choice(["spaghetti", "pizza", "italian_sub"])
        sale_history.append({
            "sale_id": str(uuid4()),
            "dish": dish,
            "amount": 1,
            "dayOfWeek": date.strftime("%A").lower(),
            "date": date.strftime("%Y-%m-%d")
        })
    date = date + timedelta(days=1)

menu = [
    {
       "menu_item": "spaghetti",
        "recipe":
            {
                "sauce": 1,
                "noodles": 2
            }
    },
    {
        "menu_item": "pizza",
        "recipe":
            {
                "sauce": 1,
                "cheese": 2,
                "pepperoni": 1
            }
    },
    {
        "menu_item": "italian_sub",
        "recipe":
            {
                "bread": 1,
                "pepperoni": 2,
                "salami": 2,
                "ham": 2,
                "cheese": 1
            }
    }
]


def clear_table(table: Table, key_names: List[str]):
    scan_kwargs = {}

    with table.batch_writer() as batch:
        while True:
            response = table.scan(**scan_kwargs)

            for item in response.get("Items", []):
                key = {
                    key_name: item[key_name]
                    for key_name in key_names
                }

                batch.delete_item(Key=key)

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

            scan_kwargs["ExclusiveStartKey"] = last_key

    LOG.info(f"Cleared table {table.name}")

def insert(items: List[dict], table: Table) -> None:
    for item in items:
        table.put_item(Item=item)

def seed_inventory_db() -> None:
    insert(inventory, inventory_table)

def seed_menu_db() -> None:
    insert(menu, menu_table)

def seed_sales_db() -> None:
    insert(sale_history, sales_table)

def main():
    clear_table(inventory_table, ["ingredient"])
    clear_table(menu_table, ["menu_item"])
    clear_table(sales_table, ["sale_id"])
    
    seed_inventory_db()
    seed_menu_db()
    seed_sales_db()


if __name__ == "__main__":
    main()