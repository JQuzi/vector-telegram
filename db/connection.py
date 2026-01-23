import sqlite3
from database import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # ВАЖНО: foreign keys работают ТОЛЬКО так
    conn.execute("PRAGMA foreign_keys = ON")

    return conn
