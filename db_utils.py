import sqlite3
from datetime import datetime

DB_FILE = 'vector.db'


def add_user_if_not_exists(telegram_id: int, first_name: str):
    """Добавляет нового пользователя в БД, если его там нет."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        if cursor.fetchone() is None:
            reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO users (telegram_id, first_name, registration_date) VALUES (?, ?, ?)",
                (telegram_id, first_name, reg_date)
            )
            conn.commit()


def save_habit(telegram_id: int, name: str, description: str, days: list, reminder_time: str = None):
    """Сохраняет новую привычку, находя внутренний ID пользователя по telegram_id."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        if not result:
            print(f"Критическая ошибка: не удалось найти пользователя с telegram_id {telegram_id}.")
            return

        user_internal_id = result[0]

        days_str = ",".join(map(str, sorted(days)))
        cursor.execute(
            "INSERT INTO habits (user_id, name, description, days_of_week, reminder_time) VALUES (?, ?, ?, ?, ?)",
            (user_internal_id, name, description, days_str, reminder_time)
        )
        conn.commit()


def get_user_habits(telegram_id: int):
    """
    ИСПРАВЛЕНО: Получает список привычек пользователя, используя telegram_id.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        query = """
        SELECT
            h.habit_id,
            h.name,
            CASE WHEN t.track_id IS NOT NULL THEN 1 ELSE 0 END AS is_completed_today
        FROM habits h
        JOIN users u ON h.user_id = u.user_id
        LEFT JOIN habit_tracking t ON h.habit_id = t.habit_id AND t.completion_date = ?
        WHERE u.telegram_id = ?
        """
        cursor.execute(query, (today, telegram_id))
        return cursor.fetchall()


def get_user_timezone(telegram_id: int):
    """ИСПРАВЛЕНО: Принимает telegram_id."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timezone_offset FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None


def set_user_timezone(telegram_id: int, offset: int):
    """ИСПРАВЛЕНО: Принимает telegram_id."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET timezone_offset = ? WHERE telegram_id = ?", (offset, telegram_id))
        conn.commit()


# --- Функции, которые были правильными и не требуют изменений ---

def get_habit_details(habit_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, days_of_week, reminder_time FROM habits WHERE habit_id = ?",
                       (habit_id,))
        return cursor.fetchone()


def track_habit(habit_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT * FROM habit_tracking WHERE habit_id = ? AND completion_date = ?", (habit_id, today))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO habit_tracking (habit_id, completion_date) VALUES (?, ?)", (habit_id, today))
            conn.commit()
            return True
        return False


def delete_habit(habit_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM habit_tracking WHERE habit_id = ?", (habit_id,))
        cursor.execute("DELETE FROM habits WHERE habit_id = ?", (habit_id,))
        conn.commit()


def update_habit_field(habit_id: int, field: str, value):
    allowed_fields = ['name', 'description', 'days_of_week', 'reminder_time']
    if field not in allowed_fields: return
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = f"UPDATE habits SET {field} = ? WHERE habit_id = ?"
        cursor.execute(query, (value, habit_id))
        conn.commit()

