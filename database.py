import sqlite3


def init_db():
    """Инициализирует базу данных и создает таблицы, если их нет."""
    try:
        conn = sqlite3.connect('vector.db')
        cursor = conn.cursor()

        # Создаем таблицу users С ПОЛЕМ TIMEZONE_OFFSET
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                telegram_id INTEGER NOT NULL UNIQUE,
                first_name TEXT,
                registration_date TEXT,
                timezone_offset INTEGER  -- <--- ЭТО САМАЯ ВАЖНАЯ СТРОКА
            )
        ''')

        # Создаем таблицу habits
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                habit_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                days_of_week TEXT,
                reminder_time TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Остальные таблицы (без изменений)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_tracking (
                track_id INTEGER PRIMARY KEY,
                habit_id INTEGER,
                completion_date TEXT,
                FOREIGN KEY (habit_id) REFERENCES habits (habit_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_categories (
                category_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                name TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        cursor.execute('''
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
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_actions (
                action_id INTEGER PRIMARY KEY,
                goal_id INTEGER,
                action_text TEXT NOT NULL,
                is_completed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (goal_id) REFERENCES goals (goal_id)
            )
        ''')

        conn.commit()
        conn.close()
        print("База данных успешно инициализирована по ПРАВИЛЬНОЙ схеме.")
    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")


if __name__ == '__main__':
    init_db()
