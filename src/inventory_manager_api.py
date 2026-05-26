from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
from datetime import date
from decimal import Decimal

from src.sales import handle_sale
from purchases import handle_new_purchases


app = FastAPI(title="InventoryManager Service")


class Sale(BaseModel):
    order: List[MenuItem]

class MenuItem(BaseModel):
    name: str
    quantity_sold: int = Field(gt=0)

class PurchasedIngredient(BaseModel):
    name: str
    quantity: float = Field(gt=0)
    unit: str
    expiration_date: date | None = None
    latest_price: Decimal = Field(gt=0)


class PurchasedIngrs(BaseModel):
    ingredients: List[PurchasedIngredient]


@app.post("/sale")
def sale(request: Sale):
    return handle_sale(request)


@app.post("/ingredients/purchase")
def new_purchase(request: PurchasedIngrs):
    return handle_new_purchases(request)