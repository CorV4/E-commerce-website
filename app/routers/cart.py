"""
Cart endpoints: view the cart, add an item, change a quantity, remove an item, and clear the cart.
"""

from decimal import Decimal

from fastapi import APIRouter, HTTPException, status

from app.db import Conn
from app.schemas.cart import CartAdd, CartOut, CartUpdate

router = APIRouter(prefix="/users/{user_id}/cart", tags=["cart"])

# Helper functions

# Make sure account is not closed
def _require_active_user(conn, user_id: int) -> None:
    row = conn.execute(
        "SELECT 1 FROM users WHERE user_id = %s AND is_active", (user_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

# Check item's existence in cart
def _not_in_cart() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Item not in cart")

@router.get("", response_model=CartOut)
def view_cart(user_id: int, conn: Conn):
    _require_active_user(conn, user_id)
    rows = conn.execute(
        """
        SELECT c.item_id, i.name, s.store_name, i.price, c.quantity,
               i.price * c.quantity AS line_total
        FROM cart c
        JOIN items i   ON i.item_id = c.item_id
        JOIN sellers s ON s.seller_id = i.seller_id
        WHERE c.user_id = %s
        ORDER BY c.item_id
        """,
        (user_id,),
    ).fetchall()
    total = sum((r["line_total"] for r in rows), Decimal("0"))
    return {"user_id": user_id, "items": rows, "total": total}

@router.post("", response_model=CartOut)
def add_to_cart(user_id: int, body: CartAdd, conn: Conn):
    """Add an item. If it's already in the cart, the quantities are added together."""
    _require_active_user(conn, user_id)

    item = conn.execute(
        """
        SELECT i.is_listed, s.user_id AS seller_user_id
        FROM items i
        JOIN sellers s ON s.seller_id = i.seller_id
        WHERE i.item_id = %s
        FOR SHARE
        """,
        (body.item_id,),
    ).fetchone()
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    if not item["is_listed"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Item is not for sale")
    if item["seller_user_id"] == user_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "You can't buy your own item")

    # cart's primary key is (user_id, item_id). If this item is
    # already in the cart, add to its quantity instead of failing.
    # EXCLUDED is the row we tried to insert.
    conn.execute(
        """
        INSERT INTO cart (user_id, item_id, quantity)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, item_id)
        DO UPDATE SET quantity = cart.quantity + EXCLUDED.quantity
        """,
        (user_id, body.item_id, body.quantity),
    )
    return view_cart(user_id, conn)

@router.patch("/{item_id}", response_model=CartOut)
def change_quantity(user_id: int, item_id: int, body: CartUpdate, conn: Conn):
    _require_active_user(conn, user_id)
    row = conn.execute(
        """
        UPDATE cart SET quantity = %s
        WHERE user_id = %s AND item_id = %s
        RETURNING item_id
        """,
        (body.quantity, user_id, item_id),
    ).fetchone()
    if row is None:
        raise _not_in_cart()
    return view_cart(user_id, conn)

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(user_id: int, item_id: int, conn: Conn):
    _require_active_user(conn, user_id)
    row = conn.execute(
        "DELETE FROM cart WHERE user_id = %s AND item_id = %s RETURNING item_id",
        (user_id, item_id),
    ).fetchone()
    if row is None:
        raise _not_in_cart()

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(user_id: int, conn: Conn):
    _require_active_user(conn, user_id)
    conn.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
