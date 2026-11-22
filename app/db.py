"""Database connection layer.

Every request borrows one connection from the pool. The connection runs one
transaction: it commits when the endpoint returns normally and rolls back if
the endpoint raises (including HTTPException).
"""

import os
from collections.abc import Iterator
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/ecommerce")

# open=False: the pool is opened by the app's lifespan in main.py, not at import.
# dict_row: rows come back as dicts, e.g. {"user_id": 1, "username": "..."}.
pool = ConnectionPool(DATABASE_URL, kwargs={"row_factory": dict_row}, open=False)


def get_conn() -> Iterator[Connection]:
    with pool.connection() as conn:
        yield conn


# Use as an endpoint parameter type: def endpoint(conn: Conn): ...
Conn = Annotated[Connection, Depends(get_conn)]
