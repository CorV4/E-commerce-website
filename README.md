# E-commerce Platform (CS157A)

Three-tier web app: frontend → FastAPI (Python) → PostgreSQL.

## Current Layout

```
app/
  main.py          FastAPI app, connection pool lifecycle, router registration
  db.py            Connection pool + `Conn` dependency (one transaction per request)
  security.py      Password hashing (stdlib scrypt)
  schemas/         Pydantic request/response models, one file per resource
  routers/         Endpoints with SQL, one file per resource
sql/
  schema.sql       CREATE TABLE statements
  sampleData.sql   INSERT statements (15+ rows per table)
tests/             pytest suite; runs against a separate _test database
```

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      pip install -r requirements.txt
   ```
2. Create the two databases and load the schema into the dev one:
   ```bash
      createdb ecommerce
      createdb ecommerce_test
      psql -d ecommerce -f sql/schema.sql
      psql -d ecommerce -f sql/sampleData.sql
   ```
3. Copy `.env.example` to `.env` and fill in your Postgres username and password.

## Run

```bash
uvicorn app.main:app --reload
```

Interactive API docs: http://localhost:8000/docs

## Test

```bash
pytest
```

The tests drop and rebuild the schema in `TEST_DATABASE_URL` and empty every
table before each test. The test database name must end in `_test`.

## How to add a resource (like items, cart, orders, ...)

Copy the pattern in `app/routers/users.py`:

1. Add Pydantic models in `app/schemas/<resource>.py`.
2. Add `app/routers/<resource>.py` with an `APIRouter`. Take `conn: Conn` as a

   parameter and pass every value as a `%s` parameter. Never use f-strings or `+` to put values into SQL.
3. Catch `psycopg.errors.UniqueViolation` / `ForeignKeyViolation` and raise an

   `HTTPException` with a clear message.
4. Register it in `app/main.py` with `app.include_router(...)`.
5. Add `tests/test_<resource>.py`.

## Endpoints so far

| Method | Path           | SQL             | Purpose                     |
| ------ | -------------- | --------------- | --------------------------- |
| POST   | `/users`       | INSERT          | Register a user             |
| POST   | `/users/login` | SELECT          | Check username and password |
| GET    | `/users`       | SELECT          | List users                  |
| GET    | `/users/{id}`  | SELECT          | View one user               |
| PATCH  | `/users/{id}`  | UPDATE          | Edit only the fields sent   |
| DELETE | `/users/{id}`  | DELETE + UPDATE | Close account (soft delete) |

### Sellers

| Method | Path                  | SQL    | Purpose                                         |
| ------ | --------------------- | ------ | ----------------------------------------------- |
| POST   | `/sellers`            | INSERT | Register a store for a user (one per user)      |
| GET    | `/sellers`            | SELECT | List stores                                     |
| GET    | `/sellers/{id}`       | SELECT | View one store                                  |
| PATCH  | `/sellers/{id}`       | UPDATE | Edit store name or bank account number          |
| GET    | `/sellers/{id}/items` | SELECT | The store's listings, including unlisted items  |

`bank_acc_number` is never returned. Stores of closed accounts are hidden.

### Items

| Method | Path          | SQL             | Purpose                                                  |
| ------ | ------------- | --------------- | -------------------------------------------------------- |
| POST   | `/items`      | INSERT          | List an item for sale                                    |
| GET    | `/items`      | SELECT          | Browse items for sale (`?search=`)                       |
| GET    | `/items/{id}` | SELECT          | View one item (works for unlisted items too)             |
| PATCH  | `/items/{id}` | UPDATE          | Edit only the fields sent; `is_listed` relists/unlists   |
| DELETE | `/items/{id}` | UPDATE + DELETE | Unlist the item and remove it from every cart            |

Items are never deleted, because orders point to them. Unlisting sets `is_listed = false`.

### Cart

| Method | Path                            | SQL    | Purpose                                          |
| ------ | ------------------------------- | ------ | ------------------------------------------------ |
| GET    | `/users/{id}/cart`              | SELECT | View the cart with line totals and a cart total  |
| POST   | `/users/{id}/cart`              | INSERT | Add an item (adds to the quantity if present)    |
| PATCH  | `/users/{id}/cart/{item_id}`    | UPDATE | Change an item's quantity                        |
| DELETE | `/users/{id}/cart/{item_id}`    | DELETE | Remove one item                                  |
| DELETE | `/users/{id}/cart`              | DELETE | Clear the cart                                   |

Only listed items can be added, and sellers can't add their own items.

Prices are returned as JSON numbers (e.g. `12.5`).
