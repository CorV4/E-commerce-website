from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import Money

OrderStatus = Literal["pending", "shipped", "delivered", "cancelled"]

class OrderStatusUpdate(BaseModel):
    order_status: OrderStatus

class OrderOut(BaseModel):
    order_id: int
    user_id: int
    item_id: int
    item_name: str
    store_name: str
    quantity: int
    order_date: datetime
    total: Money        # price * quantity at the time of checkout
    order_status: OrderStatus
