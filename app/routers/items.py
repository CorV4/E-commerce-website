"""
Items endpoints: list an item for sale, browse and search, view, edit, and unlist.

Items are never deleted, because orders point to them. "Removing" an item means setting is_listed = false 

The item disappears from browsing and from shopper's carts, but past
orders and the item's own page still work.
"""

from fastapi import APIRouter, HTTPException, status

from app.db import Conn
from app.schemas.items import ItemCreate, ItemOut, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")

def _get_item(conn, item_id: int):
    return conn.execute(
        """
        SELECT i.item_id, i.seller_id, s.store_name, i.name, i.description, i.price, i.is_listed
        FROM items i
        JOIN sellers s ON s.seller_id = i.seller_id
        WHERE i.item_id = %s
        """,
        (item_id,),
    ).fetchone()

# List item for sale
@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def list_item(body: ItemCreate, conn: Conn):
    # INSERT ... SELECT only inserts if the seller exists and their account is active.
    row = conn.execute(
        """
        INSERT INTO items (seller_id, name, description, price)
        SELECT s.seller_id, %s, %s, %s
        FROM sellers s
        JOIN users u ON u.user_id = s.user_id
        WHERE s.seller_id = %s AND u.is_active
        RETURNING item_id
        """,
        (body.name, body.description, body.price, body.seller_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Seller not found")
    return _get_item(conn, row["item_id"])

# search items
@router.get("", response_model=list[ItemOut])
def browse_items(conn: Conn, search: str = ""):
    """Browse items for sale. ?search= matches the name or description, ignoring case."""
    pattern = f"%{search}%"
    return conn.execute(
        """
        SELECT i.item_id, i.seller_id, s.store_name, i.name, i.description, i.price, i.is_listed
        FROM items i
        JOIN sellers s ON s.seller_id = i.seller_id
        WHERE i.is_listed
          AND (i.name ILIKE %s OR i.description ILIKE %s)
        ORDER BY i.item_id
        """,
        (pattern, pattern),
    ).fetchall()

@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, conn: Conn):
    """Works for unlisted items too (is_listed = false), e.g. when opened from an old order."""
    row = _get_item(conn, item_id)
    if row is None:
        raise _not_found()
    return row

@router.patch("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, body: ItemUpdate, conn: Conn):
    # UPDATE ... FROM joins sellers and users so items of a closed account can't be edited or relisted
    row = conn.execute(
        """
        UPDATE items i
        SET name        = COALESCE(%s, i.name),
            description = COALESCE(%s, i.description),
            price       = COALESCE(%s, i.price),
            is_listed   = COALESCE(%s, i.is_listed)
        FROM sellers s
        JOIN users u ON u.user_id = s.user_id
        WHERE i.item_id = %s AND s.seller_id = i.seller_id AND u.is_active
        RETURNING i.item_id
        """,
        (body.name, body.description, body.price, body.is_listed, item_id),
    ).fetchone()
    if row is None:
        raise _not_found()
    if body.is_listed is False:
        conn.execute("DELETE FROM cart WHERE item_id = %s", (item_id,))
    return _get_item(conn, item_id)

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlist_item(item_id: int, conn: Conn):
    """Unlist the item and remove it from every shopper's cart.
    The item row stays because orders may point to it."""
    row = conn.execute(
        "UPDATE items SET is_listed = false WHERE item_id = %s RETURNING item_id",
        (item_id,),
    ).fetchone()
    if row is None:
        raise _not_found()
    conn.execute("DELETE FROM cart WHERE item_id = %s", (item_id,))
