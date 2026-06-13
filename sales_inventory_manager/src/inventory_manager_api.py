from fastapi import FastAPI
import os
from sales import handle_sale
from purchases import handle_new_purchases
from restaurant_models.inventory_classes import Sale, PurchasedIngrs
import logging
from logging import getLogger, Logger


log_level: str = os.getenv("LOG_LEVEL", "WARN").upper()
logging.basicConfig(
    level=log_level,
    force=True
)
LOG: Logger = getLogger(__name__)
LOG.info("Inventory Manager api starting...")
app = FastAPI(title="InventoryManager Service")


@app.post("/sale")
def sale(sale: Sale):
    return handle_sale(sale)


@app.post("/ingredients/purchase")
def new_purchase(ingr_purchase: PurchasedIngrs):
    return handle_new_purchases(ingr_purchase)