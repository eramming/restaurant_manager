from fastapi import FastAPI
from sales import handle_sale
from purchases import handle_new_purchases
from inventory_classes import Sale, PurchasedIngrs

app = FastAPI(title="InventoryManager Service")


@app.post("/sale")
def sale(request: Sale):
    return handle_sale(request)


@app.post("/ingredients/purchase")
def new_purchase(request: PurchasedIngrs):
    return handle_new_purchases(request)