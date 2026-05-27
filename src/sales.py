import os
from uuid import uuid4
from inventory_classes import Sale, MenuItem
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from typing import Dict, List
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from datetime import datetime, timezone


INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "dev-Inventory")
MENU_TABLE = os.getenv("MENU_TABLE", "dev-Menu")
SALES_TABLE = os.getenv("SALES_TABLE", "dev-Sales")

dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
inventory_table: Table = dynamodb.Table(INVENTORY_TABLE)
menu_table: Table = dynamodb.Table(MENU_TABLE)
sales_table: Table = dynamodb.Table(SALES_TABLE)


def handle_sale(request: Sale) -> dict:
    for item in request.order:
        dish_name = item.name.lower()
        amount = item.quantity_sold

        recipe: Dict[str, float] = get_recipe(dish_name)
        update_inventory(recipe, amount)
    record_sales(request.order)

    return {
        "message": "Sales handled successfully",
        "order": request.order,
    }


def get_recipe(name: str) -> Dict[str, float]:
    response = menu_table.get_item(
        Key={"menu_item": name}
    )

    item = response.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail=f"Menu item not found: {name}")

    ingredients = item.get("ingredients")
    if not ingredients:
        raise HTTPException(status_code=400, detail=f"Menu item has no listed ingredients: {name}")

    return ingredients


def update_inventory(recipe: Dict[str, float], quantity_sold: int) -> None:
    for ingr, amount_per in recipe.items():
        total_used: float = amount_per * quantity_sold
        ingr_key = ingr.lower()
        dynamo_update(ingr_key, total_used)

def dynamo_update(ingr_key: str, total_used: float) -> None:
    try:
        inventory_table.update_item(
            Key={"ingredient": ingr_key},
            UpdateExpression="SET quantity = quantity - :used",
            ConditionExpression=(
                "attribute_exists(ingredient) "
                "AND quantity >= :used"
            ),
            ExpressionAttributeValues={
                ":used": total_used,
            },
            ReturnValues="None"
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=400,
                detail=f"Not enough inventory for ingredient: {ingr_key}",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update inventory for ingredient: {ingr_key}",
        )

def record_sales(order: List[MenuItem]) -> None:
    now: datetime = datetime.now(timezone.utc)
    day_of_wk: str = now.strftime("%A").lower()
    with sales_table.batch_writer() as batch:
        for dish, amount in order:
            sale_id: str = str(uuid4())
            batch.put_item(
                Item={
                    'sale_id': sale_id,
                    'dish': dish,
                    'amount': amount,
                    'dayOfWeek': day_of_wk,
                    'date': now.strftime("%d-%m-%Y")
                }
            )