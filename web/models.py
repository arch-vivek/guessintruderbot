import sqlite3, threading
from contextlib import contextmanager
from config import DATABASE_PATH

_db_lock = threading.Lock()

@contextmanager
def get_db():
    """Get a synchronous database connection (for Flask)."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def query_one(query, params=()):
    with get_db() as conn:
        return conn.execute(query, params).fetchone()

def query_all(query, params=()):
    with get_db() as conn:
        return conn.execute(query, params).fetchall()

def execute(query, params=()):
    with get_db() as conn:
        conn.execute(query, params)