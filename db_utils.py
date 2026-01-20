# db_utils.py
import sqlite3
from datetime import datetime, timezone, timedelta

DB_FILE = 'vector.db'


# --- Функции для Пользователей ---
def add_user_if_not_exists(telegram_id: int, first_name: str):
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
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timezone_offset FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else None


def set_user_timezone(telegram_id: int, offset: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET timezone_offset = ? WHERE telegram_id = ?", (offset, telegram_id))
        conn.commit()


def _get_user_internal_id(telegram_id: int):
    """Внутренний helper: user_id по telegram_id."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        return row[0] if row else None


def _get_user_timezone_offset_or_zero(telegram_id: int) -> int:
    """timezone_offset пользователя, если нет — 0."""
    tz = get_user_timezone(telegram_id)
    return int(tz) if tz is not None else 0


# --- Функции для Привычек ---
def save_habit(telegram_id: int, name: str, description: str, days: list, reminder_time: str = None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        if not result:
            return
        user_internal_id = result[0]
        days_str = ",".join(map(str, sorted(days)))
        cursor.execute(
            "INSERT INTO habits (user_id, name, description, days_of_week, reminder_time) VALUES (?, ?, ?, ?, ?)",
            (user_internal_id, name, description, days_str, reminder_time)
        )
        conn.commit()


def get_user_habits(telegram_id: int):
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
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, description, days_of_week, reminder_time FROM habits WHERE habit_id = ?",
            (habit_id,)
        )
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
    if field not in allowed_fields:
        return
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = f"UPDATE habits SET {field} = ? WHERE habit_id = ?"
        cursor.execute(query, (value, habit_id))
        conn.commit()


# --- ФУНКЦИИ ДЛЯ ЦЕЛЕЙ ---
def save_goal(telegram_id: int, name: str, description: str):
    """Сохраняет новую цель со статусом 'new'."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        if not result:
            return

        user_internal_id = result[0]
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO goals (user_id, name, description, status, creation_date) VALUES (?, ?, ?, ?, ?)",
            (user_internal_id, name, description, 'new', creation_date)
        )
        conn.commit()


def get_goals_by_status(telegram_id: int, status: str):
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
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = """
        SELECT status, COUNT(*) FROM goals g JOIN users u ON g.user_id = u.user_id
        WHERE u.telegram_id = ? GROUP BY status
        """
        cursor.execute(query, (telegram_id,))
        return {status: count for status, count in cursor.fetchall()}


def get_goal_details(goal_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, status FROM goals WHERE goal_id = ?", (goal_id,))
        return cursor.fetchone()


def update_goal_status(goal_id: int, new_status: str):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE goals SET status = ? WHERE goal_id = ?", (new_status, goal_id))
        conn.commit()


def delete_goal(goal_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))
        conn.commit()


# --- СТАТИСТИКА ---
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

        week_count = result[0] if result and result[0] is not None else 0
        month_count = result[1] if result and result[1] is not None else 0

        return week_count, month_count


# ==========================================================
# EVENTS (НОВОЕ) — календарные события и напоминания
# ==========================================================

def add_event(
    telegram_id: int,
    title: str,
    event_datetime_iso: str,
    remind_day: int,
    remind_hour: int,
    remind_15_min: int,
    custom_remind_minutes: int | None = None,
    timezone_offset: int | None = None,
) -> int | None:
    """
    Создать событие.

    event_datetime_iso: "YYYY-MM-DD HH:MM" или "YYYY-MM-DD HH:MM:SS"
    event_datetime хранится как локальное время пользователя (MVP).
    """
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return None

    dt = datetime.fromisoformat(event_datetime_iso)
    dt_norm = dt.replace(second=0, microsecond=0).isoformat(sep=" ")

    if timezone_offset is None:
        timezone_offset = _get_user_timezone_offset_or_zero(telegram_id)

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO events (
                user_id, title, event_datetime, timezone_offset,
                remind_day, remind_hour, remind_15_min,
                custom_remind_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_internal_id,
                title.strip(),
                dt_norm,
                int(timezone_offset),
                int(bool(remind_day)),
                int(bool(remind_hour)),
                int(bool(remind_15_min)),
                (int(custom_remind_minutes) if custom_remind_minutes is not None else None),
            )
        )
        conn.commit()
        return cursor.lastrowid


def list_events(telegram_id: int, limit: int = 20):
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return []

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT event_id, title, event_datetime, remind_day, remind_hour, remind_15_min
            FROM events
            WHERE user_id = ?
            ORDER BY event_datetime ASC
            LIMIT ?
            """,
            (user_internal_id, limit)
        )
        return cursor.fetchall()


def delete_event(telegram_id: int, event_id: int) -> bool:
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return False

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM events WHERE event_id = ? AND user_id = ?",
            (int(event_id), int(user_internal_id))
        )
        conn.commit()
        return cursor.rowcount > 0


def get_due_event_reminders(now_utc: datetime | None = None):
    """
    Возвращает список напоминаний, которые нужно отправить сейчас (в минутное окно).

    kinds:
      - "day"   : за 1 день
      - "hour"  : за 1 час
      - "15min" : за 15 минут
      - "at"    : в момент события (если включено и ещё не отправлено)

    event_datetime хранится как локальное время пользователя (MVP).
    timezone_offset берём из events.timezone_offset (если NULL) -> users.timezone_offset (если NULL) -> 0.
    """
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    due: list[dict] = []

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.event_id,
                e.title,
                e.event_datetime,
                COALESCE(e.timezone_offset, u.timezone_offset, 0) AS tz_off,

                e.remind_day,
                e.remind_hour,
                e.remind_15_min,

                e.reminded_day,
                e.reminded_hour,
                e.reminded_15_min,

                -- NEW: напоминание в момент события
                COALESCE(e.remind_at_event, 1)  AS remind_at_event,
                COALESCE(e.reminded_at_event, 0) AS reminded_at_event,
                
                e.custom_remind_minutes,
                COALESCE(e.reminded_custom, 0) AS reminded_custom,

                u.telegram_id
            FROM events e
            JOIN users u ON u.user_id = e.user_id
            """
        )
        rows = cursor.fetchall()

    for row in rows:
        (
            event_id,
            title,
            event_datetime_str,
            tz_off,
            remind_day,
            remind_hour,
            remind_15,
            reminded_day,
            reminded_hour,
            reminded_15,
            remind_at_event,
            reminded_at_event,
            custom_remind_minutes,
            reminded_custom,
            telegram_id,
        ) = row

        tz = timezone(timedelta(hours=int(tz_off or 0)))

        # event_datetime хранится как "локальное время пользователя" (naive) -> назначаем tzinfo
        try:
            event_local = datetime.fromisoformat(event_datetime_str).replace(tzinfo=tz)
        except ValueError:
            # если в БД мусорный формат даты — пропускаем
            continue

        event_utc = event_local.astimezone(timezone.utc)

        remind_points: list[tuple[str, datetime]] = []

        # Галочки
        if int(remind_day) == 1 and int(reminded_day) == 0:
            remind_points.append(("day", event_utc - timedelta(days=1)))
        if int(remind_hour) == 1 and int(reminded_hour) == 0:
            remind_points.append(("hour", event_utc - timedelta(hours=1)))
        if int(remind_15) == 1 and int(reminded_15) == 0:
            remind_points.append(("15min", event_utc - timedelta(minutes=15)))

        if custom_remind_minutes is not None and int(reminded_custom) == 0:
            try:
                cm = int(custom_remind_minutes)
                if cm > 0:
                    remind_points.append(("custom", event_utc - timedelta(minutes=cm)))
            except Exception:
                pass

        # В момент события (по умолчанию включено)
        if int(remind_at_event) == 1 and int(reminded_at_event) == 0:
            remind_points.append(("at", event_utc))

        for kind, target_utc in remind_points:
            if abs((now_utc - target_utc).total_seconds()) <= 60:
                due.append(
                    {
                        "telegram_id": int(telegram_id),
                        "event_id": int(event_id),
                        "kind": kind,
                        "title": title,
                        "event_dt_local": event_local,
                        "custom_minutes": int(custom_remind_minutes) if custom_remind_minutes is not None else None,
                    }
                )

    return due


def mark_event_reminded(event_id: int, kind: str) -> None:
    """
    Отмечает конкретный тип напоминания как отправленный.
    kind: 'day' | 'hour' | '15min' | 'at'
    """
    field_map = {
        "day": "reminded_day",
        "hour": "reminded_hour",
        "15min": "reminded_15_min",
        "custom": "reminded_custom",
        "at": "reminded_at_event",
    }

    field = field_map.get(kind)
    if not field:
        return

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE events SET {field} = 1 WHERE event_id = ?", (int(event_id),))
        conn.commit()
