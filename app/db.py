"""DB connection layer.

Every goes through here and borrows one connection from the pool. Then the connection runs one
transaction, committing only when the endpoint returns normally and rolls back if
the endpoint raises an exception.
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

pool = ConnectionPool(DATABASE_URL, kwargs={"row_factory": dict_row}, open=False)

def get_conn() -> Iterator[Connection]:
    with pool.connection() as conn:
        yield conn

Conn = Annotated[Connection, Depends(get_conn)]
