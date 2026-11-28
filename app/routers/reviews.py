"""
Reviews endpoints: write a review for an item, list an item's reviews, edit, and delete.
Can only review an item once (UNIQUE (user_id, item_id)).
"""

from fastapi import APIRouter, HTTPException, status
from psycopg import errors

from app.db import Conn
from app.schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate

router = APIRouter(tags=["reviews"])

_SELECT_REVIEWS = """
    SELECT r.review_id, r.item_id, r.user_id, u.username, r.stars, r.title, r.description
    FROM reviews r
    JOIN users u ON u.user_id = r.user_id
"""

def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")

def _get_review(conn, review_id: int):
    return conn.execute(_SELECT_REVIEWS + "WHERE r.review_id = %s", (review_id,)).fetchone()

@router.post("/items/{item_id}/reviews", response_model=ReviewOut,
             status_code=status.HTTP_201_CREATED)
def write_review(item_id: int, body: ReviewCreate, conn: Conn):
    try:
        row = conn.execute(
            """
            INSERT INTO reviews (user_id, item_id, stars, title, description)
            SELECT user_id, %s, %s, %s, %s
            FROM users
            WHERE user_id = %s AND is_active
            RETURNING review_id
            """,
            (item_id, body.stars, body.title, body.description, body.user_id),
        ).fetchone()
    except errors.ForeignKeyViolation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    except errors.UniqueViolation:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already reviewed this item")
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return _get_review(conn, row["review_id"])

@router.get("/items/{item_id}/reviews", response_model=list[ReviewOut])
def list_item_reviews(item_id: int, conn: Conn):
    return conn.execute(
        _SELECT_REVIEWS + "WHERE r.item_id = %s ORDER BY r.review_id",
        (item_id,),
    ).fetchall()

@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, body: ReviewUpdate, conn: Conn):
    row = conn.execute(
        """
        UPDATE reviews
        SET stars       = COALESCE(%s, stars),
            title       = COALESCE(%s, title),
            description = COALESCE(%s, description)
        WHERE review_id = %s
        RETURNING review_id
        """,
        (body.stars, body.title, body.description, review_id),
    ).fetchone()
    if row is None:
        raise _not_found()
    return _get_review(conn, review_id)

@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, conn: Conn):
    row = conn.execute(
        "DELETE FROM reviews WHERE review_id = %s RETURNING review_id", (review_id,)
    ).fetchone()
    if row is None:
        raise _not_found()
