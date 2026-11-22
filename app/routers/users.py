"""Users endpoints: register, log in, view, edit, close account.

Pattern for every router:
  - SQL is written by hand and run with conn.execute(sql, params).
  - Values are always passed as %s parameters, never formatted into the string.
  - Database constraint errors are turned into clear HTTP errors.
"""

from fastapi import APIRouter, HTTPException, Query, status
from psycopg import errors

from app.db import Conn
from app.schemas.users import UserCreate, UserLogin, UserOut, UserUpdate
from app.security import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])


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
        WHERE username = %s
        """,
        (body.username,),
    ).fetchone()
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
        WHERE user_id = %s
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        raise _not_found()
    return row


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, conn: Conn):
    # COALESCE(new, old): a field left out of the request (None) keeps its old value.
    new_hash = hash_password(body.password) if body.password is not None else None
    try:
        row = conn.execute(
            """
            UPDATE users
            SET username      = COALESCE(%s, username),
                email         = COALESCE(%s, email),
                password_hash = COALESCE(%s, password_hash),
                shipping_addr = COALESCE(%s, shipping_addr),
                billing_addr  = COALESCE(%s, billing_addr)
            WHERE user_id = %s
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
    try:
        row = conn.execute(
            "DELETE FROM users WHERE user_id = %s RETURNING user_id",
            (user_id,),
        ).fetchone()
    except errors.ForeignKeyViolation:
        # orders.item_id has no ON DELETE rule, so a seller whose items
        # have been ordered can't be deleted (the cascade would hit orders).
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Account can't be closed: this seller's items appear in existing orders",
        )
    if row is None:
        raise _not_found()
