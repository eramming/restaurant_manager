from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, List
from datetime import date

from src.sales import handle_sale
from purchases import handle_new_purchases


app = FastAPI(title="InventoryManager Service")


class SaleRequest(BaseModel):
    order: List[MenuItem]

class MenuItem(BaseModel):
    name: str
    quantity_sold: int = Field(gt=0)

class PurchasedIngredient(BaseModel):
    name: str
    quantity: float = Field(gt=0)
    unit: str
    expiration_date: date | None = None


class PurchaseRequest(BaseModel):
    ingredients: List[PurchasedIngredient]


@app.post("/sale")
def sale(request: SaleRequest):
    return handle_sale(request)


@app.post("/ingredients/purchase")
def new_purchase(request: PurchaseRequest):
    return handle_new_purchases(request)