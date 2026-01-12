# db_utils.py
import sqlite3
from datetime import datetime

DB_FILE = 'vector.db'


# --- Функции для Пользователей ---
def add_user_if_not_exists(telegram_id: int, first_name: str):
    # ... (код без изменений)
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


def get_user_timezone(telegram_id: int):
    # ... (код без изменений)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timezone_offset FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None


def set_user_timezone(telegram_id: int, offset: int):
    # ... (код без изменений)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET timezone_offset = ? WHERE telegram_id = ?", (offset, telegram_id))
        conn.commit()


# --- Функции для Привычек ---
def save_habit(telegram_id: int, name: str, description: str, days: list, reminder_time: str = None):
    # ... (код без изменений)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        if not result: return
        user_internal_id = result[0]
        days_str = ",".join(map(str, sorted(days)))
        cursor.execute(
            "INSERT INTO habits (user_id, name, description, days_of_week, reminder_time) VALUES (?, ?, ?, ?, ?)",
            (user_internal_id, name, description, days_str, reminder_time)
        )
        conn.commit()


def get_user_habits(telegram_id: int):
    # ... (код без изменений)
    with sqlite3.connect(DB_FILE) as conn:
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
    # ... (код без изменений)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, days_of_week, reminder_time FROM habits WHERE habit_id = ?",
                       (habit_id,))
        return cursor.fetchone()


def track_habit(habit_id: int):
    # ... (код без изменений)
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
    # ... (код без изменений)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM habit_tracking WHERE habit_id = ?", (habit_id,))
        cursor.execute("DELETE FROM habits WHERE habit_id = ?", (habit_id,))
        conn.commit()


def update_habit_field(habit_id: int, field: str, value):
    # ... (код без изменений)
    allowed_fields = ['name', 'description', 'days_of_week', 'reminder_time']
    if field not in allowed_fields: return
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = f"UPDATE habits SET {field} = ? WHERE habit_id = ?"
        cursor.execute(query, (value, habit_id))
        conn.commit()


# --- НОВЫЕ ФУНКЦИИ ДЛЯ ЦЕЛЕЙ ---

def save_goal(telegram_id: int, name: str, description: str):
    """ИЗМЕНЕНО: Сохраняет новую цель со статусом 'new'."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        if not result: return

        user_internal_id = result[0]
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Статус по умолчанию 'new'
        cursor.execute(
            "INSERT INTO goals (user_id, name, description, status, creation_date) VALUES (?, ?, ?, ?, ?)",
            (user_internal_id, name, description, 'new', creation_date)
        )
        conn.commit()


def get_goals_by_status(telegram_id: int, status: str):
    """Получает список целей пользователя по заданному статусу."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = """
        SELECT g.goal_id, g.name
        FROM goals g JOIN users u ON g.user_id = u.user_id
        WHERE u.telegram_id = ? AND g.status = ?
        """
        cursor.execute(query, (telegram_id, status))
        return cursor.fetchall()


def get_goals_counts(telegram_id: int):
    """Считает количество целей в каждом статусе."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = """
        SELECT status, COUNT(*) FROM goals g JOIN users u ON g.user_id = u.user_id
        WHERE u.telegram_id = ? GROUP BY status
        """
        cursor.execute(query, (telegram_id,))
        return {status: count for status, count in cursor.fetchall()}


def get_goal_details(goal_id: int):
    """Возвращает все детали одной цели по ее ID."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, status FROM goals WHERE goal_id = ?", (goal_id,))
        return cursor.fetchone()


def update_goal_status(goal_id: int, new_status: str):
    """Обновляет статус цели."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE goals SET status = ? WHERE goal_id = ?", (new_status, goal_id))
        conn.commit()


def delete_goal(goal_id: int):
    """Удаляет цель."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))
        conn.commit()


def get_habit_completion_stats(telegram_id: int):
    """Считает, сколько раз привычки были выполнены за 7 и 30 дней."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        query = """
        SELECT
            SUM(CASE WHEN ht.completion_date >= date('now', '-7 days') THEN 1 ELSE 0 END) as week_count,
            SUM(CASE WHEN ht.completion_date >= date('now', '-30 days') THEN 1 ELSE 0 END) as month_count
        FROM habit_tracking ht
        JOIN habits h ON ht.habit_id = h.habit_id
        JOIN users u ON h.user_id = u.user_id
        WHERE u.telegram_id = ?
        """
        cursor.execute(query, (telegram_id,))
        result = cursor.fetchone()

        # fetchone вернет (None, None), если записей нет. Обработаем это.
        week_count = result[0] if result and result[0] is not None else 0
        month_count = result[1] if result and result[1] is not None else 0

        return week_count, month_count