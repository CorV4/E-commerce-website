NEW_USER = {
    "username": "alice",
    "email": "alice@example.com",
    "password": "correct-horse",
    "shipping_addr": "1 Main St, San Jose, CA",
    "billing_addr": "1 Main St, San Jose, CA",
}


def register(client, **overrides):
    return client.post("/users", json={**NEW_USER, **overrides})


def test_health(client):
    assert client.get("/health/db").json() == {"database": "ok"}


def test_register_returns_user_without_password(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["user_id"] == 1
    assert body["username"] == "alice"
    assert "password" not in body and "password_hash" not in body


def test_password_is_stored_hashed(client):
    register(client)
    import psycopg
    from tests.conftest import TEST_DATABASE_URL

    with psycopg.connect(TEST_DATABASE_URL) as conn:
        (stored,) = conn.execute("SELECT password_hash FROM users").fetchone()
    assert stored.startswith("scrypt$")
    assert "correct-horse" not in stored


def test_duplicate_username_or_email_is_409(client):
    register(client)
    assert register(client, email="other@example.com").status_code == 409
    assert register(client, username="bob").status_code == 409


def test_register_validates_input(client):
    assert register(client, email="not-an-email").status_code == 422
    assert register(client, password="short").status_code == 422
    assert register(client, shipping_addr="").status_code == 422


def test_login(client):
    register(client)
    ok = client.post("/users/login", json={"username": "alice", "password": "correct-horse"})
    assert ok.status_code == 200
    assert ok.json()["username"] == "alice"

    bad = client.post("/users/login", json={"username": "alice", "password": "wrong-pass"})
    assert bad.status_code == 401
    nobody = client.post("/users/login", json={"username": "nobody", "password": "x"})
    assert nobody.status_code == 401


def test_get_and_list(client):
    register(client)
    register(client, username="bob", email="bob@example.com")

    assert client.get("/users/2").json()["username"] == "bob"
    assert client.get("/users/99").status_code == 404
    assert [u["username"] for u in client.get("/users").json()] == ["alice", "bob"]
    assert len(client.get("/users", params={"limit": 1}).json()) == 1


def test_update_changes_only_sent_fields(client):
    register(client)
    r = client.patch("/users/1", json={"shipping_addr": "2 Market St"})
    assert r.status_code == 200
    assert r.json()["shipping_addr"] == "2 Market St"
    assert r.json()["email"] == "alice@example.com"


def test_update_password_then_login(client):
    register(client)
    client.patch("/users/1", json={"password": "new-password"})
    r = client.post("/users/login", json={"username": "alice", "password": "new-password"})
    assert r.status_code == 200


def test_update_errors(client):
    register(client)
    register(client, username="bob", email="bob@example.com")
    assert client.patch("/users/2", json={"username": "alice"}).status_code == 409
    assert client.patch("/users/99", json={"username": "zed"}).status_code == 404


def test_close_account(client):
    register(client)
    assert client.delete("/users/1").status_code == 204
    assert client.get("/users/1").status_code == 404
    assert client.delete("/users/1").status_code == 404
