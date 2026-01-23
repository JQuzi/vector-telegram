# db/repositories/habits_repo.py
from datetime import datetime

from db.connection import get_conn


def save_habit(telegram_id: int, name: str, description: str, days: list, reminder_time: str = None):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        if not result:
            return
        user_internal_id = result[0]
        days_str = ",".join(map(str, sorted(days)))
        cursor.execute(
            "INSERT INTO habits (user_id, name, description, days_of_week, reminder_time) VALUES (?, ?, ?, ?, ?)",
            (user_internal_id, name, description, days_str, reminder_time),
        )
        conn.commit()


def get_user_habits(telegram_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        query = """
        SELECT
            h.habit_id, h.name,
            CASE WHEN t.track_id IS NOT NULL THEN 1 ELSE 0 END AS is_completed_today
        FROM habits h JOIN users u ON h.user_id = u.user_id
        LEFT JOIN habit_tracking t ON h.habit_id = t.habit_id AND t.completion_date = ?
        WHERE u.telegram_id = ?
        """
        cursor.execute(query, (today, telegram_id))
        return cursor.fetchall()


def get_habit_details(habit_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, description, days_of_week, reminder_time FROM habits WHERE habit_id = ?",
            (habit_id,),
        )
        return cursor.fetchone()


def track_habit(habit_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT * FROM habit_tracking WHERE habit_id = ? AND completion_date = ?", (habit_id, today))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO habit_tracking (habit_id, completion_date) VALUES (?, ?)", (habit_id, today))
            conn.commit()
            return True
        return False


def delete_habit(habit_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM habit_tracking WHERE habit_id = ?", (habit_id,))
        cursor.execute("DELETE FROM habits WHERE habit_id = ?", (habit_id,))
        conn.commit()


def update_habit_field(habit_id: int, field: str, value):
    allowed_fields = ["name", "description", "days_of_week", "reminder_time"]
    if field not in allowed_fields:
        return
    with get_conn() as conn:
        cursor = conn.cursor()
        query = f"UPDATE habits SET {field} = ? WHERE habit_id = ?"
        cursor.execute(query, (value, habit_id))
        conn.commit()
