import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
import os
from typing import List
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import random
from decimal import Decimal


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
        "expiration_date": tomorrow.strftime("YYYY-MM-dd")
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
        "quantity": 5,
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
    sales_per_day: int = random.randint(0, 4)
    for sale in range(sales_per_day):
        dish: str = random.choice(["spaghetti", "pizza", "italian_sub"])
        sale_history.append({
            "sale_id": uuid4(),
            "dish": dish,
            "amount": 1,
            "dayOfWeek": date.strftime("%A").lower(),
            "date": date.strftime("YYYY-MM-dd")
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
    seed_inventory_db()
    seed_menu_db()
    seed_sales_db()


if __name__ == "__main__":
    main()