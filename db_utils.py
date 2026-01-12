import sqlite3
from datetime import datetime

DB_FILE = 'vector.db'

def add_user_if_not_exists(user_id: int, first_name: str):
    """Добавляет нового пользователя в БД, если его там нет."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
        if cursor.fetchone() is None:
            reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO users (telegram_id, first_name, registration_date) VALUES (?, ?, ?)",
                (user_id, first_name, reg_date)
            )
            conn.commit()


def save_habit(telegram_user_id: int, name: str, description: str, days: list, reminder_time: str = None):
    """
    Сохраняет новую привычку в БД.
    СНАЧАЛА находит внутренний user_id по telegram_id.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
        # Находим внутренний ID пользователя по его Telegram ID
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_user_id,))
        result = cursor.fetchone()
        if not result:
            print(
                f"Критическая ошибка: не удалось найти пользователя с telegram_id {telegram_user_id} при сохранении привычки.")
            return

        user_internal_id = result[0]
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

        days_str = ",".join(map(str, sorted(days)))
        cursor.execute(
            "INSERT INTO habits (user_id, name, description, days_of_week, reminder_time) VALUES (?, ?, ?, ?, ?)",
            # Используем правильный ID
            (user_internal_id, name, description, days_str, reminder_time)
        )
        conn.commit()


def get_user_habits(user_id: int):
    """
    Возвращает список привычек пользователя.
    Формат: [(habit_id, name, is_completed_today), ...]
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        # Сложный SQL-запрос, который сразу проверяет, выполнена ли привычка
        query = """
        SELECT
            h.habit_id,
            h.name,
            CASE
                WHEN t.track_id IS NOT NULL THEN 1
                ELSE 0
            END AS is_completed_today
        FROM habits h
        LEFT JOIN habit_tracking t ON h.habit_id = t.habit_id AND t.completion_date = ?
        WHERE h.user_id = ?
        """
        cursor.execute(query, (today, user_id))
        return cursor.fetchall()

def track_habit(habit_id: int):
    """Отмечает выполнение привычки на сегодня."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        # Проверим, не отмечали ли уже сегодня
        cursor.execute(
            "SELECT * FROM habit_tracking WHERE habit_id = ? AND completion_date = ?",
            (habit_id, today)
        )
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO habit_tracking (habit_id, completion_date) VALUES (?, ?)",
                (habit_id, today)
            )
            conn.commit()
            return True # Успешно отмечено
        return False # Уже было отмечено

def get_user_timezone(user_id: int):
    """Возвращает часовой пояс пользователя."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timezone_offset FROM users WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None

def set_user_timezone(user_id: int, offset: int):
    """Устанавливает часовой пояс пользователя."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET timezone_offset = ? WHERE telegram_id = ?",
            (offset, user_id)
        )
        conn.commit()

# НОВАЯ ФУНКЦИЯ
def get_habit_details(habit_id: int):
    """Возвращает все детали одной привычки по ее ID."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, days_of_week, reminder_time FROM habits WHERE habit_id = ?", (habit_id,))
        return cursor.fetchone()

def delete_habit(habit_id: int):
    """Удаляет привычку и все связанные с ней записи отслеживания."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Сначала удаляем записи отслеживания, чтобы не нарушать целостность
        cursor.execute("DELETE FROM habit_tracking WHERE habit_id = ?", (habit_id,))
        # Затем удаляем саму привычку
        cursor.execute("DELETE FROM habits WHERE habit_id = ?", (habit_id,))
        conn.commit()

def update_habit_field(habit_id: int, field: str, value):
    """Обновляет одно поле (field) для конкретной привычки."""
    # Валидация, чтобы избежать SQL-инъекций
    allowed_fields = ['name', 'description', 'days_of_week', 'reminder_time']
    if field not in allowed_fields:
        print(f"Попытка обновить неразрешенное поле: {field}")
        return

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = f"UPDATE habits SET {field} = ? WHERE habit_id = ?"
        cursor.execute(query, (value, habit_id))
        conn.commit()
