from tests.helpers import make_item, make_seller, make_user, run_sql

def setup_seller(client, name="alice", store="Alice's Shop"):
    return make_seller(client, make_user(client, name), store)

def test_list_item(client):
    seller = setup_seller(client)
    r = client.post("/items", json={
        "seller_id": seller, "name": "Blue mug", "description": "Holds coffee", "price": 12.5,
    })
    assert r.status_code == 201
    assert r.json() == {
        "item_id": 1, "seller_id": seller, "store_name": "Alice's Shop",
        "name": "Blue mug", "description": "Holds coffee", "price": 12.5, "is_listed": True,
    }

def test_list_item_validation(client):
    seller = setup_seller(client)
    base = {"seller_id": seller, "name": "Mug", "description": "d", "price": 5}
    assert client.post("/items", json={**base, "price": 0}).status_code == 422
    assert client.post("/items", json={**base, "price": 1.999}).status_code == 422
    assert client.post("/items", json={**base, "description": ""}).status_code == 422
    assert client.post("/items", json={**base, "seller_id": 99}).status_code == 404

def test_browse_shows_only_listed_items(client):
    seller = setup_seller(client)
    make_item(client, seller, name="Mug")
    plate = make_item(client, seller, name="Plate")
    client.delete(f"/items/{plate}")
    assert [i["name"] for i in client.get("/items").json()] == ["Mug"]

def test_search(client):
    seller = setup_seller(client)
    make_item(client, seller, name="Blue mug", description="Ceramic")
    make_item(client, seller, name="Red plate", description="Holds a blue pattern")
    make_item(client, seller, name="Spoon", description="Steel")

    def names(**params):
        return [i["name"] for i in client.get("/items", params=params).json()]

    assert names(search="BLUE") == ["Blue mug", "Red plate"]  # name or description, any case
    assert names(search="spoon") == ["Spoon"]
    assert names(search="fork") == []
    assert names() == ["Blue mug", "Red plate", "Spoon"]  # no search returns every item
    assert names(search="Joe's") == []  # an apostrophe doesn't break the query

def test_get_item_works_when_unlisted(client):
    item = make_item(client, setup_seller(client))
    client.delete(f"/items/{item}")
    r = client.get(f"/items/{item}")
    assert r.status_code == 200
    assert r.json()["is_listed"] is False
    assert client.get("/items/99").status_code == 404

def test_update_item(client):
    item = make_item(client, setup_seller(client))
    r = client.patch(f"/items/{item}", json={"price": 15, "name": "Big mug"})
    assert r.status_code == 200
    assert (r.json()["name"], r.json()["price"], r.json()["description"]) == \
        ("Big mug", 15.0, "Holds coffee")
    assert client.patch(f"/items/{item}", json={"price": -1}).status_code == 422
    assert client.patch("/items/99", json={"name": "x"}).status_code == 404

def test_unlist_and_relist(client):
    item = make_item(client, setup_seller(client))
    assert client.patch(f"/items/{item}", json={"is_listed": False}).json()["is_listed"] is False
    assert client.get("/items").json() == []
    assert client.patch(f"/items/{item}", json={"is_listed": True}).json()["is_listed"] is True
    assert len(client.get("/items").json()) == 1

def test_delete_unlists_and_removes_from_carts(client):
    item = make_item(client, setup_seller(client))
    bob = make_user(client, "bob")
    client.post(f"/users/{bob}/cart", json={"item_id": item})

    assert client.delete(f"/items/{item}").status_code == 204
    assert run_sql("SELECT is_listed FROM items") == [(False,)]  # row kept
    assert client.get(f"/users/{bob}/cart").json()["items"] == []
    assert client.delete("/items/99").status_code == 404

def test_unlisted_item_with_orders_is_kept(client):
    item = make_item(client, setup_seller(client))
    bob = make_user(client, "bob")
    run_sql("INSERT INTO orders (user_id, item_id, quantity, total) VALUES (%s, %s, 1, 12.5)",
            (bob, item))
    assert client.delete(f"/items/{item}").status_code == 204
    assert run_sql("SELECT user_id, item_id FROM orders") == [(bob, item)]

def test_closed_sellers_items_cannot_be_edited_or_relisted(client):
    alice = make_user(client)
    item = make_item(client, make_seller(client, alice))
    client.delete(f"/users/{alice}")
    assert client.get(f"/items/{item}").json()["is_listed"] is False
    assert client.patch(f"/items/{item}", json={"is_listed": True}).status_code == 404
