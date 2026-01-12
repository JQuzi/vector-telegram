import sqlite3

# --- ВВЕДИТЕ ID СВОЕЙ ПОСЛЕДНЕЙ ПРИВЫЧКИ ---
# (Если не знаете, просто оставьте 1, 2 или 3)
HABIT_ID_TO_CHECK = 7


def check_data():
    """Проверяет данные для напоминания в БД."""
    conn = sqlite3.connect('vector.db')
    cursor = conn.cursor()

    print("--- Проверяем привычку ---")
    cursor.execute("SELECT user_id, name, reminder_time, days_of_week FROM habits WHERE habit_id = ?",
                   (HABIT_ID_TO_CHECK,))
    habit_data = cursor.fetchone()

    if not habit_data:
        print(f"ОШИБКА: Привычка с ID {HABIT_ID_TO_CHECK} не найдена!")
        return

    user_internal_id, name, reminder_time, days_of_week = habit_data
    print(f"Привычка: '{name}' (ID: {HABIT_ID_TO_CHECK})")
    print(f"  - Время напоминания в БД: {reminder_time}")
    print(f"  - Дни недели в БД: {days_of_week}")

    print("\n--- Проверяем пользователя ---")
    cursor.execute("SELECT telegram_id, timezone_offset FROM users WHERE user_id = ?", (user_internal_id,))
    user_data = cursor.fetchone()

    if not user_data:
        print("ОШИБКА: Связанный пользователь не найден!")
        return

    telegram_id, timezone_offset = user_data
    print(f"Пользователь: {telegram_id}")
    print(f"  - Часовой пояс в БД: {timezone_offset}")

    conn.close()


if __name__ == '__main__':
    check_data()
