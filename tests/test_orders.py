from tests.helpers import make_item, make_seller, make_user

def setup(client):
    """alice sells a mug (12.50) and a plate (3.00); bob has 2 mugs and 1 plate in his cart."""
    alice = make_user(client, "alice")
    seller = make_seller(client, alice)
    mug = make_item(client, seller, name="Mug", price=12.5)
    plate = make_item(client, seller, name="Plate", price=3)
    bob = make_user(client, "bob")
    client.post(f"/users/{bob}/cart", json={"item_id": mug, "quantity": 2})
    client.post(f"/users/{bob}/cart", json={"item_id": plate})
    return seller, bob, mug, plate

def test_checkout_creates_orders_and_empties_cart(client):
    seller, bob, mug, plate = setup(client)
    r = client.post(f"/users/{bob}/checkout")
    assert r.status_code == 201
    orders = r.json()
    assert [(o["item_name"], o["quantity"], o["total"], o["order_status"]) for o in orders] == [
        ("Mug", 2, 25.0, "pending"),
        ("Plate", 1, 3.0, "pending"),
    ]
    assert orders[0]["store_name"] == "Alice's Shop"
    assert client.get(f"/users/{bob}/cart").json()["items"] == []

def test_checkout_empty_cart(client):
    bob = make_user(client, "bob")
    assert client.post(f"/users/{bob}/checkout").status_code == 400
    assert client.post("/users/99/checkout").status_code == 404

def test_order_total_keeps_checkout_price(client):
    _, bob, mug, _ = setup(client)
    client.post(f"/users/{bob}/checkout")
    client.patch(f"/items/{mug}", json={"price": 100})
    orders = client.get(f"/users/{bob}/orders").json()
    assert [o["total"] for o in orders] == [3.0, 25.0]  # newest first

def test_order_history_includes_unlisted_items(client):
    _, bob, mug, _ = setup(client)
    client.post(f"/users/{bob}/checkout")
    client.delete(f"/items/{mug}")
    assert len(client.get(f"/users/{bob}/orders").json()) == 2

def test_seller_orders(client):
    seller, bob, _, _ = setup(client)
    other = make_seller(client, make_user(client, "carol"), "Carol's Shop")
    client.post(f"/users/{bob}/checkout")
    assert len(client.get(f"/sellers/{seller}/orders").json()) == 2
    assert client.get(f"/sellers/{other}/orders").json() == []
    assert client.get("/sellers/99/orders").status_code == 404

def test_update_status(client):
    _, bob, _, _ = setup(client)
    order = client.post(f"/users/{bob}/checkout").json()[0]["order_id"]
    r = client.patch(f"/orders/{order}", json={"order_status": "shipped"})
    assert r.status_code == 200
    assert r.json()["order_status"] == "shipped"
    assert client.patch(f"/orders/{order}", json={"order_status": "lost"}).status_code == 422
    assert client.patch("/orders/99", json={"order_status": "shipped"}).status_code == 404
