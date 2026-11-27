from tests.helpers import make_item, make_seller, make_user

def setup(client):
    """alice sells a mug (12.50) and a plate (3.00); bob is a shopper."""
    alice = make_user(client, "alice")
    seller = make_seller(client, alice)
    mug = make_item(client, seller, name="Mug", price=12.5)
    plate = make_item(client, seller, name="Plate", price=3)
    bob = make_user(client, "bob")
    return alice, bob, mug, plate

def test_empty_cart(client):
    bob = make_user(client, "bob")
    assert client.get(f"/users/{bob}/cart").json() == {"user_id": bob, "items": [], "total": 0}

def test_add_and_view(client):
    _, bob, mug, plate = setup(client)
    client.post(f"/users/{bob}/cart", json={"item_id": mug, "quantity": 2})
    r = client.post(f"/users/{bob}/cart", json={"item_id": plate})  # quantity defaults to 1
    assert r.status_code == 200

    cart = client.get(f"/users/{bob}/cart").json()
    assert cart["items"] == [
        {"item_id": mug, "name": "Mug", "store_name": "Alice's Shop",
         "price": 12.5, "quantity": 2, "line_total": 25.0},
        {"item_id": plate, "name": "Plate", "store_name": "Alice's Shop",
         "price": 3.0, "quantity": 1, "line_total": 3.0},
    ]
    assert cart["total"] == 28.0

def test_adding_again_adds_to_quantity(client):
    _, bob, mug, _ = setup(client)
    client.post(f"/users/{bob}/cart", json={"item_id": mug, "quantity": 2})
    cart = client.post(f"/users/{bob}/cart", json={"item_id": mug, "quantity": 3}).json()
    assert cart["items"][0]["quantity"] == 5

def test_add_errors(client):
    alice, bob, mug, plate = setup(client)
    client.delete(f"/items/{plate}")

    assert client.post(f"/users/{bob}/cart", json={"item_id": 99}).status_code == 404
    assert client.post(f"/users/{bob}/cart", json={"item_id": plate}).status_code == 409   # unlisted
    assert client.post(f"/users/{alice}/cart", json={"item_id": mug}).status_code == 409  # own item
    assert client.post("/users/99/cart", json={"item_id": mug}).status_code == 404
    assert client.post(f"/users/{bob}/cart", json={"item_id": mug, "quantity": 0}).status_code == 422

def test_change_quantity(client):
    _, bob, mug, _ = setup(client)
    client.post(f"/users/{bob}/cart", json={"item_id": mug})
    r = client.patch(f"/users/{bob}/cart/{mug}", json={"quantity": 4})
    assert r.status_code == 200
    assert r.json()["items"][0]["quantity"] == 4
    assert r.json()["total"] == 50.0
    assert client.patch(f"/users/{bob}/cart/{mug}", json={"quantity": 0}).status_code == 422
    assert client.patch(f"/users/{bob}/cart/99", json={"quantity": 1}).status_code == 404

def test_remove_item(client):
    _, bob, mug, plate = setup(client)
    client.post(f"/users/{bob}/cart", json={"item_id": mug})
    client.post(f"/users/{bob}/cart", json={"item_id": plate})

    assert client.delete(f"/users/{bob}/cart/{mug}").status_code == 204
    assert [i["item_id"] for i in client.get(f"/users/{bob}/cart").json()["items"]] == [plate]
    assert client.delete(f"/users/{bob}/cart/{mug}").status_code == 404

def test_clear_cart(client):
    _, bob, mug, plate = setup(client)
    client.post(f"/users/{bob}/cart", json={"item_id": mug})
    client.post(f"/users/{bob}/cart", json={"item_id": plate})
    assert client.delete(f"/users/{bob}/cart").status_code == 204
    assert client.get(f"/users/{bob}/cart").json()["items"] == []

def test_closed_account_has_no_cart(client):
    _, bob, mug, _ = setup(client)
    client.delete(f"/users/{bob}")
    assert client.get(f"/users/{bob}/cart").status_code == 404

def test_seller_closing_account_removes_items_from_carts(client):
    alice, bob, mug, _ = setup(client)
    client.post(f"/users/{bob}/cart", json={"item_id": mug})
    client.delete(f"/users/{alice}")
    assert client.get(f"/users/{bob}/cart").json()["items"] == []
