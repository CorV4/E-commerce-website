from tests.helpers import make_item, make_seller, make_user

REVIEW = {"stars": 5, "title": "Great", "description": "Keeps coffee hot"}

def setup(client):
    item = make_item(client, make_seller(client, make_user(client, "alice")))
    bob = make_user(client, "bob")
    return item, bob

def test_write_and_list(client):
    item, bob = setup(client)
    r = client.post(f"/items/{item}/reviews", json={**REVIEW, "user_id": bob})
    assert r.status_code == 201
    assert r.json() == {"review_id": 1, "item_id": item, "user_id": bob, "username": "bob", **REVIEW}
    assert client.get(f"/items/{item}/reviews").json() == [r.json()]

def test_write_errors(client):
    item, bob = setup(client)
    client.post(f"/items/{item}/reviews", json={**REVIEW, "user_id": bob})
    assert client.post(f"/items/{item}/reviews", json={**REVIEW, "user_id": bob}).status_code == 409
    assert client.post("/items/99/reviews", json={**REVIEW, "user_id": bob}).status_code == 404
    assert client.post(f"/items/{item}/reviews", json={**REVIEW, "user_id": 99}).status_code == 404
    assert client.post(f"/items/{item}/reviews",
                       json={**REVIEW, "user_id": bob, "stars": 6}).status_code == 422

def test_update_review(client):
    item, bob = setup(client)
    review = client.post(f"/items/{item}/reviews", json={**REVIEW, "user_id": bob}).json()["review_id"]
    r = client.patch(f"/reviews/{review}", json={"stars": 3})
    assert r.status_code == 200
    assert (r.json()["stars"], r.json()["title"]) == (3, "Great")
    assert client.patch("/reviews/99", json={"stars": 3}).status_code == 404

def test_delete_review(client):
    item, bob = setup(client)
    review = client.post(f"/items/{item}/reviews", json={**REVIEW, "user_id": bob}).json()["review_id"]
    assert client.delete(f"/reviews/{review}").status_code == 204
    assert client.get(f"/items/{item}/reviews").json() == []
    assert client.delete(f"/reviews/{review}").status_code == 404
