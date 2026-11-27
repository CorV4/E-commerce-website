from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import Money

class ItemCreate(BaseModel):
    seller_id: int
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

class ItemUpdate(BaseModel):

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=1000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    is_listed: bool | None = None

class ItemOut(BaseModel):
    item_id: int
    seller_id: int
    store_name: str
    name: str
    description: str
    price: Money
    is_listed: bool
