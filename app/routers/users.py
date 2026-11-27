"""
Users endpoints: register, log in, view, edit, and close account.
"""

from fastapi import APIRouter, HTTPException, Query, status
from psycopg import errors

from app.db import Conn
from app.schemas.users import UserCreate, UserLogin, UserOut, UserUpdate
from app.security import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])

# Helper error functions
def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

def _taken() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, "Username or email already taken")

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(body: UserCreate, conn: Conn):
    try:
        row = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, shipping_addr, billing_addr)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id, username, email, shipping_addr, billing_addr
            """,
            (body.username, body.email, hash_password(body.password),
             body.shipping_addr, body.billing_addr),
        ).fetchone()
    except errors.UniqueViolation:
        raise _taken()
    return row

@router.post("/login", response_model=UserOut)
def login(body: UserLogin, conn: Conn):
    row = conn.execute(
        """
        SELECT user_id, username, email, shipping_addr, billing_addr, password_hash
        FROM users
        WHERE username = %s AND is_active
        """,
        (body.username,),
    ).fetchone()

    # Verifies the password by hashing it and comparing against the stored hash
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    return row

@router.get("", response_model=list[UserOut])
def list_users(
    conn: Conn,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return conn.execute(
        """
        SELECT user_id, username, email, shipping_addr, billing_addr
        FROM users
        WHERE is_active
        ORDER BY user_id
        LIMIT %s OFFSET %s
        """,
        (limit, offset),
    ).fetchall()

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, conn: Conn):
    row = conn.execute(
        """
        SELECT user_id, username, email, shipping_addr, billing_addr
        FROM users
        WHERE user_id = %s AND is_active
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        raise _not_found()
    return row

@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, conn: Conn):
    new_hash = hash_password(body.password) if body.password is not None else None
    try:
        # COALESCE(new, old): a field left out of the request (None) keeps its old value.
        # This allows handling of optional fields and only updating what needs to be updated.
        row = conn.execute(
            """
            UPDATE users
            SET username      = COALESCE(%s, username),
                email         = COALESCE(%s, email),
                password_hash = COALESCE(%s, password_hash),
                shipping_addr = COALESCE(%s, shipping_addr),
                billing_addr  = COALESCE(%s, billing_addr)
            WHERE user_id = %s AND is_active
            RETURNING user_id, username, email, shipping_addr, billing_addr
            """,
            (body.username, body.email, new_hash,
             body.shipping_addr, body.billing_addr, user_id),
        ).fetchone()
    except errors.UniqueViolation:
        raise _taken()
    if row is None:
        raise _not_found()
    return row

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def close_account(user_id: int, conn: Conn):
    """
    Soft delete only: the users row stays so existing orders and reviews still point to it,
    but personal data is overwritten and the account is marked inactive.
    """
    
    row = conn.execute(
        "SELECT user_id FROM users WHERE user_id = %s AND is_active FOR UPDATE",
        (user_id,),
    ).fetchone()
    if row is None:
        raise _not_found()

    # Deleting from cards: delete cards only this user was linked to. If
    # the card is shared by another person, keep it.
    conn.execute(
        """
        DELETE FROM cards c
        WHERE EXISTS (SELECT 1 FROM user_cards uc
                      WHERE uc.card_number = c.card_number AND uc.user_id = %s)
          AND NOT EXISTS (SELECT 1 FROM user_cards uc
                          WHERE uc.card_number = c.card_number AND uc.user_id <> %s)
        """,
        (user_id, user_id),
    )
    # Deleting from user_cards: delete user_card that this user was linked to.
    conn.execute("DELETE FROM user_cards WHERE user_id = %s", (user_id,))

    # Empty their cart.
    conn.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))

    # If they're a seller: unlist all their items and remove their bank account number.
    conn.execute(
        """
        UPDATE items SET is_listed = false
        WHERE seller_id IN (SELECT seller_id FROM sellers WHERE user_id = %s)
        """,
        (user_id,),
    )
    # Unlisted items can't be bought, so take them out of other shoppers' carts too.
    conn.execute(
        """
        DELETE FROM cart
        WHERE item_id IN (SELECT i.item_id FROM items i
                          JOIN sellers s ON s.seller_id = i.seller_id
                          WHERE s.user_id = %s)
        """,
        (user_id,),
    )
    conn.execute(
        "UPDATE sellers SET bank_acc_number = 'deleted' WHERE user_id = %s",
        (user_id,),
    )

    # Remove all sensitive info and mark the account closed.
    conn.execute(
        """
        UPDATE users
        SET is_active     = false,
            username      = 'deleted_user_' || user_id,
            email         = 'deleted_' || user_id || '@deleted.invalid',
            password_hash = '!',
            shipping_addr = 'deleted',
            billing_addr  = 'deleted'
        WHERE user_id = %s
        """,
        (user_id,),
    )
