"""
Orders endpoints: check out the cart, view a buyer's orders, view a seller's orders,
and change an order's status.
"""

from fastapi import APIRouter, HTTPException, status

from app.db import Conn
from app.routers.sellers import get_seller
from app.routers.users import get_user
from app.schemas.orders import OrderOut, OrderStatusUpdate

router = APIRouter(tags=["orders"])

_SELECT_ORDERS = """
    SELECT o.order_id, o.user_id, o.item_id, i.name AS item_name, s.store_name,
           o.quantity, o.order_date, o.total, o.order_status
    FROM orders o
    JOIN items i   ON i.item_id = o.item_id
    JOIN sellers s ON s.seller_id = i.seller_id
"""

@router.post("/users/{user_id}/checkout", response_model=list[OrderOut],
             status_code=status.HTTP_201_CREATED)
def checkout(user_id: int, conn: Conn):
    """Turn the cart into orders and empty the cart, in one transaction."""
    get_user(user_id, conn)

    rows = conn.execute(
        """
        INSERT INTO orders (user_id, item_id, quantity, total)
        SELECT c.user_id, c.item_id, c.quantity, i.price * c.quantity
        FROM cart c
        JOIN items i ON i.item_id = c.item_id
        WHERE c.user_id = %s AND i.is_listed
        RETURNING order_id
        """,
        (user_id,),
    ).fetchall()
    if not rows:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cart is empty")

    conn.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
    return conn.execute(
        _SELECT_ORDERS + "WHERE o.order_id = ANY(%s) ORDER BY o.order_id",
        ([r["order_id"] for r in rows],),
    ).fetchall()

@router.get("/users/{user_id}/orders", response_model=list[OrderOut])
def list_user_orders(user_id: int, conn: Conn):
    # List buyer order history
    get_user(user_id, conn)
    return conn.execute(
        _SELECT_ORDERS + "WHERE o.user_id = %s ORDER BY o.order_id DESC",
        (user_id,),
    ).fetchall()

@router.get("/sellers/{seller_id}/orders", response_model=list[OrderOut])
def list_seller_orders(seller_id: int, conn: Conn):
    # List all orders for a seller's items
    get_seller(seller_id, conn)
    return conn.execute(
        _SELECT_ORDERS + "WHERE i.seller_id = %s ORDER BY o.order_id DESC",
        (seller_id,),
    ).fetchall()

@router.patch("/orders/{order_id}", response_model=OrderOut)
def update_order_status(order_id: int, body: OrderStatusUpdate, conn: Conn):
    row = conn.execute(
        "UPDATE orders SET order_status = %s WHERE order_id = %s RETURNING order_id",
        (body.order_status, order_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return conn.execute(_SELECT_ORDERS + "WHERE o.order_id = %s", (order_id,)).fetchone()
