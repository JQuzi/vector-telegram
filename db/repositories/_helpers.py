# db/repositories/_helpers.py
from db.connection import get_conn


def _get_user_internal_id(telegram_id: int):
    """Внутренний helper: user_id по telegram_id."""
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        return row[0] if row else None


def _get_user_timezone_offset_or_zero(telegram_id: int) -> int:
    """timezone_offset пользователя, если нет — 0."""
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timezone_offset FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        tz = result[0] if result and result[0] is not None else None
        return int(tz) if tz is not None else 0
