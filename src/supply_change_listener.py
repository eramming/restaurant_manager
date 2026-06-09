import os
import time
import boto3
from SupplyGapAnalyzer import SupplyGapAnalyzer
from mypy_boto3_sqs.client import SQSClient
import logging
from logging import Logger, getLogger

log_level: str = os.getenv("LOG_LEVEL", "WARN").upper()
logging.basicConfig(
    level=log_level,
    force=True
)
LOG: Logger = getLogger(__name__)
LOG.info("New Purchase Listener starting...")

SUPPLY_CHANGE_QUEUE: str = os.getenv("SUPPLY_CHANGE_QUEUE_URL", "dev-supply-change-queue")
sqs: SQSClient = boto3.client("sqs")
supply_gap_analyzer = SupplyGapAnalyzer()


def listen() -> None:
    while True:
        response = sqs.receive_message(
            QueueUrl=SUPPLY_CHANGE_QUEUE,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=60,
        )

        messages = response.get("Messages", [])
        if len(messages) > 0:
            LOG.info(f"Received {len(messages)} messages from {SUPPLY_CHANGE_QUEUE}. Beginning processing...")

        for message in messages:
            try:
                supply_change = message["Body"]
                if supply_change in ["SOLD_MENU_ITEM", "NEW_INGR_PURCHASE"]:
                    supply_gap_analyzer.send_supply_gap()
                    sqs.delete_message(
                        QueueUrl=SUPPLY_CHANGE_QUEUE,
                        ReceiptHandle=message["ReceiptHandle"],
                    )
            except Exception as e:
                LOG.info(f"Failed to process message: {e}")

        if not messages:
            time.sleep(10)


def main() -> None:
    try:
        listen()
    except KeyboardInterrupt:
        LOG.info("Interrupt received. Shutting down listener.")
    except Exception:
        LOG.exception("Fatal error in listener")
        raise


if __name__ == "__main__":
    main()