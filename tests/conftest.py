"""
Tests run against a separate database (TEST_DATABASE_URL). At the start of the
run its public schema is dropped and rebuilt from sql/schema.sql, and every
table is emptied before each test. The database name must end in "_test", this is 
safety to ensure the real database can't be wiped by mistake.
"""

import os
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

load_dotenv()
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://localhost/ecommerce_test")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL  # must be set before app.db is imported

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

SCHEMA_FILE = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


@pytest.fixture(scope="session", autouse=True)
def test_schema():
    if not conninfo_to_dict(TEST_DATABASE_URL).get("dbname", "").endswith("_test"):
        pytest.exit("TEST_DATABASE_URL must name a database ending in _test", returncode=2)
    with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")
        conn.execute(SCHEMA_FILE.read_text())


@pytest.fixture(autouse=True)
def empty_tables(test_schema):
    with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )]
        if tables:
            conn.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY CASCADE").format(
                sql.SQL(", ").join(map(sql.Identifier, tables))
            ))


@pytest.fixture(scope="session")
def client(test_schema):
    # Session scope: the app's connection pool opens once for the whole run.
    with TestClient(app) as c:
        yield c
