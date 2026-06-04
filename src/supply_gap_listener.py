import json
import os
import time
import boto3
from PricingAnalyzer import PricingAnalyzer
from mypy_boto3_sqs.client import SQSClient
import logging
from logging import Logger, getLogger

log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    force=True
)
LOG: Logger = getLogger(__name__)
LOG.debug("Supply Gap Listener starting...")

SUPPLY_GAP_QUEUE: str = os.getenv("SUPPLY_GAP_QUEUE_URL", None)
sqs: SQSClient = boto3.client("sqs")
pricing_analyzer = PricingAnalyzer()


def listen() -> None:
    while True:
        response = sqs.receive_message(
            QueueUrl=SUPPLY_GAP_QUEUE,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=60,
        )

        messages = response.get("Messages", [])

        for message in messages:
            try:
                supply_gap_report = json.loads(message["Body"])
                pricing_analyzer.analyze_and_send(supply_gap_report)
                sqs.delete_message(
                    QueueUrl=SUPPLY_GAP_QUEUE,
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