"""Shortcuts for setting up test data through the API."""

import psycopg

from tests.conftest import TEST_DATABASE_URL

def make_user(client, name="alice") -> int:
    r = client.post("/users", json={
        "username": name,
        "email": f"{name}@example.com",
        "password": "correct-horse",
        "shipping_addr": "1 Main St",
        "billing_addr": "1 Main St",
    })
    assert r.status_code == 201, r.text
    return r.json()["user_id"]

def make_seller(client, user_id, store_name="Alice's Shop") -> int:
    r = client.post("/sellers", json={
        "user_id": user_id, "store_name": store_name, "bank_acc_number": "123456789",
    })
    assert r.status_code == 201, r.text
    return r.json()["seller_id"]

def make_item(client, seller_id, name="Blue mug", description="Holds coffee", price=12.5) -> int:
    r = client.post("/items", json={
        "seller_id": seller_id, "name": name, "description": description, "price": price,
    })
    assert r.status_code == 201, r.text
    return r.json()["item_id"]

def run_sql(query, params=()):
    with psycopg.connect(TEST_DATABASE_URL) as conn:
        cur = conn.execute(query, params)
        return cur.fetchall() if cur.description else None
