"""
Sellers endpoints: register a store, view stores, edit a store, and view a store's listings.
A seller is a user who also sells.
Sellers whose user account is closed (users.is_active = false) are hidden.
"""

from fastapi import APIRouter, HTTPException, Query, status
from psycopg import errors

from app.db import Conn
from app.schemas.items import ItemOut
from app.schemas.sellers import SellerCreate, SellerOut, SellerUpdate

router = APIRouter(prefix="/sellers", tags=["sellers"])

def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Seller not found")

@router.post("", response_model=SellerOut, status_code=status.HTTP_201_CREATED)
def register_seller(body: SellerCreate, conn: Conn):
    try:
        row = conn.execute(
            """
            INSERT INTO sellers (user_id, store_name, bank_acc_number)
            SELECT user_id, %s, %s
            FROM users
            WHERE user_id = %s AND is_active
            RETURNING seller_id, user_id, store_name
            """,
            (body.store_name, body.bank_acc_number, body.user_id),
        ).fetchone()
    except errors.UniqueViolation:
        raise HTTPException(status.HTTP_409_CONFLICT, "This user already has a store")
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return row

@router.get("", response_model=list[SellerOut])
def list_sellers(
    conn: Conn,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return conn.execute(
        """
        SELECT s.seller_id, s.user_id, s.store_name
        FROM sellers s
        JOIN users u ON u.user_id = s.user_id
        WHERE u.is_active
        ORDER BY s.seller_id
        LIMIT %s OFFSET %s
        """,
        (limit, offset),
    ).fetchall()

@router.get("/{seller_id}", response_model=SellerOut)
def get_seller(seller_id: int, conn: Conn):
    row = conn.execute(
        """
        SELECT s.seller_id, s.user_id, s.store_name
        FROM sellers s
        JOIN users u ON u.user_id = s.user_id
        WHERE s.seller_id = %s AND u.is_active
        """,
        (seller_id,),
    ).fetchone()
    if row is None:
        raise _not_found()
    return row

@router.patch("/{seller_id}", response_model=SellerOut)
def update_seller(seller_id: int, body: SellerUpdate, conn: Conn):
    row = conn.execute(
        """
        UPDATE sellers s
        SET store_name      = COALESCE(%s, s.store_name),
            bank_acc_number = COALESCE(%s, s.bank_acc_number)
        FROM users u
        WHERE s.seller_id = %s AND u.user_id = s.user_id AND u.is_active
        RETURNING s.seller_id, s.user_id, s.store_name
        """,
        (body.store_name, body.bank_acc_number, seller_id),
    ).fetchone()
    if row is None:
        raise _not_found()
    return row

@router.get("/{seller_id}/items", response_model=list[ItemOut])
def list_seller_items(seller_id: int, conn: Conn):
    get_seller(seller_id, conn)  # raise 404 error if the seller doesn't exist or is closed
    return conn.execute(
        """
        SELECT i.item_id, i.seller_id, s.store_name, i.name, i.description, i.price, i.is_listed
        FROM items i
        JOIN sellers s ON s.seller_id = i.seller_id
        WHERE i.seller_id = %s
        ORDER BY i.item_id
        """,
        (seller_id,),
    ).fetchall()
