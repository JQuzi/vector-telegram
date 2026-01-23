# db/repositories/users_repo.py
from datetime import datetime

from db.connection import get_conn


def add_user_if_not_exists(telegram_id: int, first_name: str):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        if cursor.fetchone() is None:
            reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO users (telegram_id, first_name, registration_date) VALUES (?, ?, ?)",
                (telegram_id, first_name, reg_date),
            )
            conn.commit()


def get_user_timezone(telegram_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timezone_offset FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None


def set_user_timezone(telegram_id: int, offset: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET timezone_offset = ? WHERE telegram_id = ?", (offset, telegram_id))
        conn.commit()
