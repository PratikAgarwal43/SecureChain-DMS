"""
database.py — PostgreSQL connection pool for the API Gateway.
Uses psycopg2 with a simple connection factory.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import settings


def get_connection():
    """Return a new psycopg2 connection."""
    return psycopg2.connect(settings.database_url)


@contextmanager
def db_cursor():
    """Context manager yielding a dict-style cursor, auto-commits or rolls back."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
