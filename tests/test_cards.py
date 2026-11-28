from tests.helpers import make_user, run_sql

VISA = {"card_number": "4111111111111111", "card_cvv": "123", "card_exp_date": "2028-05-31"}

def test_add_and_list(client):
    alice = make_user(client, "alice")
    r = client.post(f"/users/{alice}/cards", json=VISA)
    assert r.status_code == 201
    assert r.json() == {"card_number": "4111111111111111", "card_exp_date": "2028-05-31"}
    assert client.get(f"/users/{alice}/cards").json() == [r.json()]

def test_add_errors(client):
    alice = make_user(client, "alice")
    client.post(f"/users/{alice}/cards", json=VISA)
    assert client.post(f"/users/{alice}/cards", json=VISA).status_code == 409
    assert client.post(f"/users/{alice}/cards", json={**VISA, "card_number": "12ab"}).status_code == 422
    assert client.post(f"/users/{alice}/cards", json={**VISA, "card_cvv": "1"}).status_code == 422
    assert client.post("/users/99/cards", json=VISA).status_code == 404

def test_shared_card(client):
    alice = make_user(client, "alice")
    bob = make_user(client, "bob")
    client.post(f"/users/{alice}/cards", json=VISA)
    assert client.post(f"/users/{bob}/cards", json=VISA).status_code == 201
    assert run_sql("SELECT count(*) FROM cards") == [(1,)]  # one card, two links

    # An edit is seen by both users.
    client.patch(f"/users/{bob}/cards/{VISA['card_number']}", json={"card_exp_date": "2030-01-31"})
    assert client.get(f"/users/{alice}/cards").json()[0]["card_exp_date"] == "2030-01-31"

    # Removing it from bob keeps the card for alice; removing it from alice deletes it.
    assert client.delete(f"/users/{bob}/cards/{VISA['card_number']}").status_code == 204
    assert run_sql("SELECT count(*) FROM cards") == [(1,)]
    client.delete(f"/users/{alice}/cards/{VISA['card_number']}")
    assert run_sql("SELECT count(*) FROM cards") == [(0,)]

def test_cannot_edit_or_remove_someone_elses_card(client):
    alice = make_user(client, "alice")
    bob = make_user(client, "bob")
    client.post(f"/users/{alice}/cards", json=VISA)
    path = f"/users/{bob}/cards/{VISA['card_number']}"
    assert client.patch(path, json={"card_exp_date": "2030-01-31"}).status_code == 404
    assert client.delete(path).status_code == 404

def test_update_cvv_keeps_exp_date(client):
    alice = make_user(client, "alice")
    client.post(f"/users/{alice}/cards", json=VISA)
    path = f"/users/{alice}/cards/{VISA['card_number']}"
    r = client.patch(path, json={"card_cvv": "987"})
    assert r.status_code == 200
    assert r.json()["card_exp_date"] == "2028-05-31"  # left out, so unchanged
    assert run_sql("SELECT card_cvv FROM cards") == [("987",)]
    assert client.patch(path, json={"card_cvv": "12"}).status_code == 422
