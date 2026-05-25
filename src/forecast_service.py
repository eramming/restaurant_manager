from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from boto3.dynamodb.conditions import Key
import os
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
import boto3


MENU_TABLE = os.getenv("MENU_TABLE", "dev-Menu")
SALES_TABLE = os.getenv("SALES_TABLE", "dev-Sales")

dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")
menu_table: Table = dynamodb.Table(MENU_TABLE)
sales_table: Table = dynamodb.Table(SALES_TABLE)



# Example query for relevant forecasting data:
threshold = datetime.now(ZoneInfo("America/New_York")) - timedelta(days=30)
day_of_week: str = "monday"
response = sales_table.query(
    IndexName="SalesByDayOfWeek",
    KeyConditionExpression=(
        Key("day_of_week").eq(day_of_week) &
        Key("date").gte(threshold.isoformat())
    )
)