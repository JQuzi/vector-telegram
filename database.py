import sqlite3

DB_PATH = "vector.db"


def _column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]  # row[1] = column name
    return column in cols


def _ensure_column(cursor: sqlite3.Cursor, table: str, column: str, col_def: str) -> None:
    """
    Добавляет колонку в существующую таблицу, если её нет.
    col_def — строка вида: "timezone_offset INTEGER DEFAULT 0"
    """
    if not _column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")


def init_db() -> None:
    """Инициализирует базу данных, создаёт таблицы и выполняет мягкие миграции."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Включим foreign keys (в SQLite по умолчанию выключено)
    cursor.execute("PRAGMA foreign_keys = ON")

    # ----------------------------
    # 1) БАЗОВЫЕ ТАБЛИЦЫ (как было)
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            telegram_id INTEGER NOT NULL UNIQUE,
            first_name TEXT,
            registration_date TEXT,
            timezone_offset INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            habit_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            days_of_week TEXT,
            reminder_time TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_tracking (
            track_id INTEGER PRIMARY KEY,
            habit_id INTEGER,
            completion_date TEXT,
            FOREIGN KEY (habit_id) REFERENCES habits (habit_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goal_categories (
            category_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            goal_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            category_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL,
            creation_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (category_id) REFERENCES goal_categories (category_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goal_actions (
            action_id INTEGER PRIMARY KEY,
            goal_id INTEGER,
            action_text TEXT NOT NULL,
            is_completed INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (goal_id) REFERENCES goals (goal_id)
        )
    """)

    # ----------------------------
    # 2) МИГРАЦИИ СУЩЕСТВУЮЩИХ ТАБЛИЦ (мягко, без падений)
    # ----------------------------
    # Если у кого-то users была создана раньше без timezone_offset — добавим.
    _ensure_column(cursor, "users", "timezone_offset", "timezone_offset INTEGER DEFAULT 0")

    # ----------------------------
    # 3) НОВАЯ ТАБЛИЦА: EVENTS (календарные события)
    # ----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,

            title TEXT NOT NULL,
            event_datetime TEXT NOT NULL,    -- ISO-строка в локальном времени пользователя (или в UTC, решим позже)
            timezone_offset INTEGER,         -- если NULL -> использовать users.timezone_offset

            -- выбранные пользователем напоминания (галочки)
            remind_day INTEGER NOT NULL DEFAULT 0,
            remind_hour INTEGER NOT NULL DEFAULT 0,
            remind_15_min INTEGER NOT NULL DEFAULT 0,

            -- отправлено ли конкретное напоминание
            reminded_day INTEGER NOT NULL DEFAULT 0,
            reminded_hour INTEGER NOT NULL DEFAULT 0,
            reminded_15_min INTEGER NOT NULL DEFAULT 0,

            created_at TEXT DEFAULT (datetime('now')),

            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    # Индексы (не обязательно, но очень поможет scheduler-у)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_datetime ON events(event_datetime)")

    _ensure_column(cursor, "events", "remind_at_event", "remind_at_event INTEGER NOT NULL DEFAULT 1")
    _ensure_column(cursor, "events", "reminded_at_event", "reminded_at_event INTEGER NOT NULL DEFAULT 0")

    conn.commit()
    conn.close()
    print("База данных успешно инициализирована (включая таблицу events).")


if __name__ == "__main__":
    init_db()
