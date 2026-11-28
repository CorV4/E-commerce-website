from tests.helpers import make_item, make_seller, make_user, run_sql

def test_register_seller(client):
    alice = make_user(client)
    r = client.post("/sellers", json={
        "user_id": alice, "store_name": "Alice's Shop", "bank_acc_number": "123456789",
    })
    assert r.status_code == 201
    assert r.json() == {"seller_id": 1, "user_id": alice, "store_name": "Alice's Shop"}
    # The bank account number is stored but never returned.
    assert run_sql("SELECT bank_acc_number FROM sellers") == [("123456789",)]

def test_one_store_per_user(client):
    alice = make_user(client)
    make_seller(client, alice)
    r = client.post("/sellers", json={
        "user_id": alice, "store_name": "Second", "bank_acc_number": "1111",
    })
    assert r.status_code == 409

def test_register_seller_errors(client):
    assert client.post("/sellers", json={
        "user_id": 99, "store_name": "x", "bank_acc_number": "1234",
    }).status_code == 404
    alice = make_user(client)
    assert client.post("/sellers", json={
        "user_id": alice, "store_name": "x", "bank_acc_number": "not-digits",
    }).status_code == 422
    assert client.post("/sellers", json={
        "user_id": alice, "store_name": "", "bank_acc_number": "1234",
    }).status_code == 422

def test_closed_user_cannot_become_seller(client):
    alice = make_user(client)
    client.delete(f"/users/{alice}")
    assert client.post("/sellers", json={
        "user_id": alice, "store_name": "x", "bank_acc_number": "1234",
    }).status_code == 404

def test_list_and_get_sellers(client):
    make_seller(client, make_user(client, "alice"), "A")
    make_seller(client, make_user(client, "bob"), "B")
    assert [s["store_name"] for s in client.get("/sellers").json()] == ["A", "B"]
    assert client.get("/sellers/2").json()["store_name"] == "B"
    assert client.get("/sellers/99").status_code == 404

def test_update_seller(client):
    seller = make_seller(client, make_user(client))
    r = client.patch(f"/sellers/{seller}", json={"store_name": "New name"})
    assert r.status_code == 200
    assert r.json()["store_name"] == "New name"
    client.patch(f"/sellers/{seller}", json={"bank_acc_number": "99998888"})
    assert run_sql("SELECT bank_acc_number FROM sellers") == [("99998888",)]
    assert client.patch("/sellers/99", json={"store_name": "x"}).status_code == 404

def test_closed_sellers_are_hidden(client):
    alice = make_user(client)
    seller = make_seller(client, alice)
    client.delete(f"/users/{alice}")
    assert client.get("/sellers").json() == []
    assert client.get(f"/sellers/{seller}").status_code == 404
    assert client.patch(f"/sellers/{seller}", json={"store_name": "x"}).status_code == 404

def test_seller_items_include_unlisted(client):
    seller = make_seller(client, make_user(client))
    make_item(client, seller, name="Mug")
    hidden = make_item(client, seller, name="Plate")
    client.delete(f"/items/{hidden}")

    items = client.get(f"/sellers/{seller}/items").json()
    assert [(i["name"], i["is_listed"]) for i in items] == [("Mug", True), ("Plate", False)]
    assert client.get("/sellers/99/items").status_code == 404
