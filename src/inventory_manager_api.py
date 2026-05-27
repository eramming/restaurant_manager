from fastapi import FastAPI
from sales import handle_sale
from purchases import handle_new_purchases
from inventory_classes import Sale, PurchasedIngrs

app = FastAPI(title="InventoryManager Service")


@app.post("/sale")
def sale(sale: Sale):
    return handle_sale(sale)


@app.post("/ingredients/purchase")
def new_purchase(ingr_purchase: PurchasedIngrs):
    return handle_new_purchases(ingr_purchase)