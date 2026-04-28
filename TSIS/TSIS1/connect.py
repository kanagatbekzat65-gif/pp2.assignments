# connect.py
"""
Provides a single get_connection() helper used across the project.
"""

import psycopg2
import psycopg2.extras
from config import DB_CONFIG


def get_connection():
    """Return a new psycopg2 connection using DB_CONFIG."""
    return psycopg2.connect(**DB_CONFIG)


def init_schema():
    """
    Read and execute schema.sql then procedures.sql.
    Safe to call on every startup (uses IF NOT EXISTS / CREATE OR REPLACE).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for fname in ("schema.sql", "procedures.sql"):
                with open(fname, "r", encoding="utf-8") as fh:
                    cur.execute(fh.read())
        conn.commit()
        print("[DB] Schema and procedures applied successfully.")
    except Exception as exc:
        conn.rollback()
        print(f"[DB] Error during schema init: {exc}")
        raise
    finally:
        conn.close()
