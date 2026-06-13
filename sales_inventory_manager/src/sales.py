import os
from uuid import uuid4
from models.src.restaurant_models.inventory_classes import Sale
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_sqs.client import SQSClient
from typing import Dict
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from datetime import datetime, timezone
from logging import Logger, getLogger

LOG: Logger = getLogger(__name__)

INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "dev-Inventory")
MENU_TABLE = os.getenv("MENU_TABLE", "dev-Menu")
SALES_TABLE = os.getenv("SALES_TABLE", "dev-Sales")
SUPPLY_CHANGE_QUEUE = os.getenv("SUPPLY_CHANGE_QUEUE_URL", "dev-supply-change-queue")

dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
inventory_table: Table = dynamodb.Table(INVENTORY_TABLE)
menu_table: Table = dynamodb.Table(MENU_TABLE)
sales_table: Table = dynamodb.Table(SALES_TABLE)
sqs_client: SQSClient = boto3.client("sqs")


def handle_sale(request: Sale) -> dict:
    for item in request.order:
        dish_name = item.name.lower()
        amount = item.quantity_sold

        recipe: Dict[str, float] = get_recipe(dish_name)
        update_inventory(recipe, amount)
        record_sale(dish_name, amount)
    send_sale_msg()

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

    recipe = item.get("recipe")
    if not recipe:
        raise HTTPException(status_code=400, detail=f"Menu item has no listed recipe: {name}")

    return recipe


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
            }
        )
        LOG.info(f"Subtracted {total_used} units from {ingr_key} in inventory.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            LOG.error(f"Not enough inventory for ingredient: {ingr_key}\n"
                      f"{e.response['Error']['Message']}")
            raise HTTPException(
                status_code=400,
                detail=f"Not enough inventory for ingredient: {ingr_key}",
            )
        LOG.error(f"Failed to update inventory for ingredient: {ingr_key}\n"
                      f"{e.response['Error']['Message']}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update inventory for ingredient: {ingr_key}",
        )

def record_sale(dish_name: str, amount: int) -> None:
    now: datetime = datetime.now(timezone.utc)
    day_of_wk: str = now.strftime("%A").lower()
    sale_id: str = str(uuid4())
    try:
        sales_table.put_item(Item={
            'sale_id': sale_id,
            'dish': dish_name,
            'amount': amount,
            'dayOfWeek': day_of_wk,
            'date': now.strftime("%Y-%m-%d")}
        )
        LOG.info(f"Saved sale id={sale_id}, dish={dish_name} to database.")
    except ClientError as e:
        LOG.error(f"Failed to save sale {sale_id} for dish={dish_name}\n"
                  f"{e.response['Error']['Message']}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to  save sale {sale_id} for dish={dish_name}\n",
        )


def send_sale_msg() -> None:
    sqs_client.send_message(
        QueueUrl=SUPPLY_CHANGE_QUEUE,
        MessageBody="SOLD_MENU_ITEM"
    )