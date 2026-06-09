import os
import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from fastapi import HTTPException
from botocore.exceptions import ClientError
from inventory_classes import PurchasedIngrs
from logging import Logger, getLogger

LOG: Logger = getLogger(__name__)

INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "dev-Inventory")

dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
inventory_table: Table = dynamodb.Table(INVENTORY_TABLE)


def handle_new_purchases(purchase: PurchasedIngrs):
    for ingredient in purchase.ingredients:
        ingr_key = ingredient.ingredient.lower()
        update_expression = """
            ADD quantity :quantity
            SET unit = :unit,
                latest_price = :latest_price
        """
        expression_values = {
            ":quantity": ingredient.quantity,
            ":unit": ingredient.unit,
            ":latest_price": ingredient.latest_price,
        }

        if ingredient.expiration_date:
            update_expression += ", expiration_date = :expiration_date"
            expression_values[":expiration_date"] = ingredient.expiration_date.isoformat()

        try:
            inventory_table.update_item(
                Key={"ingredient": ingr_key},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            LOG.info(f"Added {ingredient.quantity} units of {ingr_key} to inventory.")
        except ClientError:
            LOG.error(f"Failed to update ingredient: {ingr_key} with params {expression_values}.")
            raise HTTPException(status_code=500, detail=f"Failed to update ingredient: {ingr_key}")

    return {
        "message": "Purchased ingredients added successfully"
    }