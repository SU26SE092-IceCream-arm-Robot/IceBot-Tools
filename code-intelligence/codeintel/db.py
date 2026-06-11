import sqlite3
from contextlib import contextmanager
from pathlib import Path
from codeintel.config import DB_PATH, ensure_directories

def get_connection() -> sqlite3.Connection:
    """Connects to SQLite database and returns the connection object."""
    ensure_directories()
    conn = sqlite3.connect(str(DB_PATH))
    # Enable foreign keys and row factory for dict-like access
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db_cursor():
    """Context manager that yields a cursor and commits/rolls back automatically."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

@contextmanager
def get_db_conn():
    """Context manager that yields a connection and commits/rolls back automatically."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
