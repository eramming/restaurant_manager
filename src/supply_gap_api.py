from fastapi import FastAPI
from SupplyGapAnalyzer import SupplyGapAnalyzer
from logging import getLogger, Logger
import logging
import os

log_level: str = os.getenv("LOG_LEVEL", "WARN").upper()
logging.basicConfig(
    level=log_level,
    force=True
)
LOG: Logger = getLogger(__name__)
app = FastAPI(title="Forecasted Supply Gap Service")

LOG.info("Supply Gap API starting...")


@app.get("/supply_gap")
def supply_gap():
    SupplyGapAnalyzer().send_supply_gap()
    return {"message": "Successfully generated and sent supply gap analysis."}