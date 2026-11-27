from pydantic import BaseModel, Field

from app.schemas.common import Money

class CartAdd(BaseModel):
    item_id: int
    quantity: int = Field(default=1, ge=1, le=99)

class CartUpdate(BaseModel):
    quantity: int = Field(ge=1, le=99)

class CartItemOut(BaseModel):
    item_id: int
    name: str
    store_name: str
    price: Money        # current price of one item
    quantity: int
    line_total: Money   # price * quantity

class CartOut(BaseModel):
    user_id: int
    items: list[CartItemOut]
    total: Money
