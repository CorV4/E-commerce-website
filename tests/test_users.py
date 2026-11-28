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


def test_close_account_hides_the_user(client):
    register(client)
    assert client.delete("/users/1").status_code == 204

    assert client.get("/users/1").status_code == 404
    assert client.get("/users").json() == []
    assert client.patch("/users/1", json={"shipping_addr": "x"}).status_code == 404
    assert client.delete("/users/1").status_code == 404
    login = client.post("/users/login", json={"username": "alice", "password": "correct-horse"})
    assert login.status_code == 401


def test_close_account_anonymizes_but_keeps_the_row(client):
    register(client)
    client.delete("/users/1")

    row = run_sql("""SELECT is_active, username, email, password_hash, shipping_addr, billing_addr
                     FROM users WHERE user_id = 1""")
    assert row == [(False, "deleted_user_1", "deleted_1@deleted.invalid", "!",
                    "deleted", "deleted")]
    # The original username and email are free again.
    assert register(client).status_code == 201


# There are no card endpoints yet, so these tests set up cards with SQL.

def run_sql(query, params=()):
    import psycopg
    from tests.conftest import TEST_DATABASE_URL

    with psycopg.connect(TEST_DATABASE_URL) as conn:
        cur = conn.execute(query, params)
        return cur.fetchall() if cur.description else None


def add_card(user_id, card_number):
    run_sql("INSERT INTO cards VALUES (%s, '123', '2028-05-01') ON CONFLICT DO NOTHING",
            (card_number,))
    run_sql("INSERT INTO user_cards VALUES (%s, %s)", (user_id, card_number))


def card_numbers():
    return [r[0] for r in run_sql("SELECT card_number FROM cards ORDER BY 1")]


def test_close_account_deletes_own_cards_but_keeps_shared_ones(client):
    register(client)                                         # alice = 1
    register(client, username="bob", email="bob@example.com")  # bob = 2
    add_card(1, "4111111111111111")   # shared by alice and bob
    add_card(2, "4111111111111111")
    add_card(1, "5555555555554444")   # alice only

    assert client.delete("/users/1").status_code == 204

    assert card_numbers() == ["4111111111111111"]
    assert run_sql("SELECT user_id, card_number FROM user_cards") == [(2, "4111111111111111")]


def make_seller_with_an_order():
    """alice (1) sells an item, and bob (2) has ordered it."""
    run_sql("INSERT INTO sellers (user_id, store_name, bank_acc_number) VALUES (1, 'shop', '12345')")
    run_sql("INSERT INTO items (seller_id, name, description, price) VALUES (1, 'mug', 'blue', 5)")
    run_sql("INSERT INTO orders (user_id, item_id, quantity, total) VALUES (2, 1, 1, 5)")


def test_seller_with_orders_can_close_account(client):
    register(client)
    register(client, username="bob", email="bob@example.com")
    make_seller_with_an_order()
    run_sql("INSERT INTO cart VALUES (1, 1, 2)")  # alice's own cart

    assert client.delete("/users/1").status_code == 204

    # Bob's order still points to alice's item; the item is hidden, not deleted.
    assert run_sql("SELECT user_id, item_id FROM orders") == [(2, 1)]
    assert run_sql("SELECT is_listed FROM items") == [(False,)]
    assert run_sql("SELECT bank_acc_number FROM sellers") == [("deleted",)]
    assert run_sql("SELECT * FROM cart") == []


def test_buyer_closing_account_keeps_orders(client):
    register(client)
    register(client, username="bob", email="bob@example.com")
    make_seller_with_an_order()

    assert client.delete("/users/2").status_code == 204  # bob, the buyer

    # The seller still sees the sale.
    assert run_sql("SELECT user_id, item_id FROM orders") == [(2, 1)]


def test_users_with_orders_cannot_be_hard_deleted():
    """The foreign key is a safety net if code ever tries a real DELETE."""
    import psycopg
    import pytest
    from tests.conftest import TEST_DATABASE_URL

    run_sql("INSERT INTO users (username, email, password_hash, shipping_addr, billing_addr) "
            "VALUES ('a','a@x.com','h','s','b'), ('b','b@x.com','h','s','b')")
    make_seller_with_an_order()
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        run_sql("DELETE FROM users WHERE user_id = 2")  # bob, the buyer
