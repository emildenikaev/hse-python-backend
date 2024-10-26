from pydantic import BaseModel
from typing import List

class Item(BaseModel):
    id: str
    name: str
    price: float
    deleted: bool = False


class CartItem(BaseModel):
    id: str
    quantity: int

class Cart(BaseModel):
    id: str
    items: List[CartItem]
    price: float
