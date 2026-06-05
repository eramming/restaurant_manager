from pydantic import BaseModel, Field
from typing import List
from datetime import date
from decimal import Decimal


class Sale(BaseModel):
    order: List[MenuItem]

class MenuItem(BaseModel):
    name: str
    quantity_sold: int = Field(gt=0)

class PurchasedIngredient(BaseModel):
    ingredient: str
    quantity: float = Field(gt=0)
    unit: str
    expiration_date: date | None = None
    latest_price: Decimal = Field(gt=0)


class PurchasedIngrs(BaseModel):
    ingredients: List[PurchasedIngredient]