"""
Main FastAPI app. It creates the app, opens/closes the DB connection pool, and registers routers.

"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db import Conn, pool
from app.routers import cards, cart, items, orders, reviews, sellers, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True, timeout=10)  # fail fast at startup if the database is unreachable
    yield
    pool.close()

app = FastAPI(title="E-commerce Platform", lifespan=lifespan)

app.include_router(users.router)
app.include_router(sellers.router)
app.include_router(items.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(cards.router)
app.include_router(reviews.router)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health/db")
def health_db(conn: Conn):
    conn.execute("SELECT 1")
    return {"database": "ok"}
