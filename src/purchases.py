import os
import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from fastapi import HTTPException
from botocore.exceptions import ClientError
from inventory_classes import PurchasedIngrs


INVENTORY_TABLE = os.getenv("INVENTORY_TABLE", "dev-Inventory")

dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
inventory_table: Table = dynamodb.Table(INVENTORY_TABLE)


def handle_new_purchases(purchase: PurchasedIngrs):
    for ingredient in purchase.ingredients:
        ingr_key = ingredient.name.lower()

        try:
            inventory_table.update_item(
                Key={"ingredient": ingr_key},
                UpdateExpression="""
                    ADD quantity :quantity
                    SET unit = :unit,
                        expiration_date = :expiration_date,
                        latest_price = :latest_price
                """,
                ExpressionAttributeValues={
                    ":quantity": ingredient.quantity,
                    ":unit": ingredient.unit,
                    ":expiration_date": (
                        ingredient.expiration_date.isoformat()
                        if ingredient.expiration_date
                        else None
                    ),
                    ":latest_price": ingredient.latest_price
                }
            )
        except ClientError:
            raise HTTPException(status_code=500, detail=f"Failed to update ingredient: {ingr_key}")

    return {
        "message": "Purchased ingredients added successfully"
    }