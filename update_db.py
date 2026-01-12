import sqlite3

def migrate_db():
    """Проверяет и обновляет схему БД, добавляя недостающие столбцы."""
    conn = sqlite3.connect('vector.db')
    cursor = conn.cursor()

    try:
        # Попытка прочитать новый столбец. Если его нет, возникнет ошибка.
        cursor.execute("SELECT timezone_offset FROM users LIMIT 1")
        print("Столбец 'timezone_offset' уже существует. Обновление не требуется.")
    except sqlite3.OperationalError:
        # Если столбца нет, добавляем его
        print("Обнаружена старая версия БД. Добавляю столбец 'timezone_offset'...")
        cursor.execute("ALTER TABLE users ADD COLUMN timezone_offset INTEGER")
        conn.commit()
        print("База данных успешно обновлена!")

    conn.close()

if __name__ == '__main__':
    migrate_db()
