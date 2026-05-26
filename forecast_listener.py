import json
import os
import time
import boto3
from src.PricingAnalyzer import PricingAnalyzer
from mypy_boto3_sqs.client import SQSClient

FORECAST_QUEUE: str = os.getenv("FORECAST_QUEUE_URL", None)
sqs: SQSClient = boto3.client("sqs")
analyzer = PricingAnalyzer()


def listen() -> None:
    while True:
        response = sqs.receive_message(
            QueueUrl=FORECAST_QUEUE,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=60,
        )

        messages = response.get("Messages", [])

        for message in messages:
            try:
                recommendations = json.loads(message["Body"])
                analyzer.analyze(recommendations)
                sqs.delete_message(
                    QueueUrl=FORECAST_QUEUE,
                    ReceiptHandle=message["ReceiptHandle"],
                )
            except Exception as e:
                print(f"Failed to process message: {e}")

        if not messages:
            time.sleep(10)


def main() -> None:
    listen()
    

if __name__ == "__main__":
    main()