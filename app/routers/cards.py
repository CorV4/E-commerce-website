"""
Payment card endpoints: add, list, edit, and remove a user's cards.

A card can be shared by several users (ex: family members), and a user can have several cards.
The user_cards table links them. Removing a card only deletes the card itself when no one
else still uses it.
"""

from fastapi import APIRouter, HTTPException, status
from psycopg import errors

from app.db import Conn
from app.routers.users import get_user
from app.schemas.cards import CardCreate, CardOut, CardUpdate

router = APIRouter(prefix="/users/{user_id}/cards", tags=["cards"])

def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Card not found")

@router.post("", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def add_card(user_id: int, body: CardCreate, conn: Conn):
    get_user(user_id, conn)  # 404 if the user doesn't exist or is closed

    # If another user already added this card, keep the stored card and just link to it.
    conn.execute(
        """
        INSERT INTO cards (card_number, card_cvv, card_exp_date)
        VALUES (%s, %s, %s)
        ON CONFLICT (card_number) DO NOTHING
        """,
        (body.card_number, body.card_cvv, body.card_exp_date),
    )
    try:
        conn.execute(
            "INSERT INTO user_cards (user_id, card_number) VALUES (%s, %s)",
            (user_id, body.card_number),
        )
    except errors.UniqueViolation:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already added this card")
    return conn.execute(
        "SELECT card_number, card_exp_date FROM cards WHERE card_number = %s",
        (body.card_number,),
    ).fetchone()

@router.get("", response_model=list[CardOut])
def list_cards(user_id: int, conn: Conn):
    get_user(user_id, conn)
    return conn.execute(
        """
        SELECT c.card_number, c.card_exp_date
        FROM user_cards uc
        JOIN cards c ON c.card_number = uc.card_number
        WHERE uc.user_id = %s
        ORDER BY c.card_number
        """,
        (user_id,),
    ).fetchall()

@router.patch("/{card_number}", response_model=CardOut)
def update_card(user_id: int, card_number: str, body: CardUpdate, conn: Conn):
    get_user(user_id, conn)
    # Only update the card if the user is linked to it.
    row = conn.execute(
        """
        UPDATE cards c
        SET card_cvv      = COALESCE(%s, c.card_cvv),
            card_exp_date = COALESCE(%s, c.card_exp_date)
        FROM user_cards uc
        WHERE c.card_number = %s AND uc.card_number = c.card_number AND uc.user_id = %s
        RETURNING c.card_number, c.card_exp_date
        """,
        (body.card_cvv, body.card_exp_date, card_number, user_id),
    ).fetchone()
    if row is None:
        raise _not_found()
    return row

@router.delete("/{card_number}", status_code=status.HTTP_204_NO_CONTENT)
def remove_card(user_id: int, card_number: str, conn: Conn):
    get_user(user_id, conn)
    # Delete the user's linked card from user_cards table first
    row = conn.execute(
        "DELETE FROM user_cards WHERE user_id = %s AND card_number = %s RETURNING card_number",
        (user_id, card_number),
    ).fetchone()
    if row is None:
        raise _not_found()
    # Delete even the card itself from cards table only if no other user is still linked to it.
    conn.execute(
        """
        DELETE FROM cards c
        WHERE c.card_number = %s
          AND NOT EXISTS (SELECT 1 FROM user_cards uc WHERE uc.card_number = c.card_number)
        """,
        (card_number,),
    )
