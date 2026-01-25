# app/db/read_connection.py
from contextlib import contextmanager
import psycopg
from app.db.connection import get_connection

@contextmanager
def read_connection() -> psycopg.Connection:
    conn = get_connection()
    try:
        yield conn
        # 纯读不需要 commit
    finally:
        conn.close()
