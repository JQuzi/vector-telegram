import sqlite3
from datetime import datetime, timezone, timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

DB_FILE = 'vector.db'


async def check_habits_for_notification(bot: Bot):
    """
    Проверяет БД на наличие привычек, по которым пора отправить напоминание,
    и отправляет их с учетом часового пояса пользователя.
    """
    query = """
    SELECT
        h.name,
        h.days_of_week,
        u.telegram_id
    FROM habits h
    JOIN users u ON h.user_id = u.user_id
    WHERE h.reminder_time = strftime('%H:%M', 'now', u.timezone_offset || ' hours')
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        potential_notifications = cursor.execute(query).fetchall()

    if not potential_notifications:
        return

    for name, days_of_week, telegram_id in potential_notifications:
        # Поскольку SQL-запрос уже учитывает смещение, нам нужна только проверка дня недели по UTC
        # Это более простой и надежный подход
        utc_current_weekday = datetime.now(timezone.utc).weekday() + 1

        # Нам нужно найти, какой день недели у пользователя.
        # Для этого нужно снова получить его смещение.
        cursor.execute("SELECT timezone_offset FROM users WHERE telegram_id = ?", (telegram_id,))
        offset_res = cursor.fetchone()
        if offset_res:
            offset = offset_res[0]
            user_tz = timezone(timedelta(hours=offset))
            user_current_weekday = datetime.now(user_tz).weekday() + 1
        else:  # Если вдруг смещение не найдено, используем UTC
            user_current_weekday = utc_current_weekday

        if str(user_current_weekday) in days_of_week.split(','):
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=f"⏰ **Напоминание!**\n\nНе забудьте про вашу привычку: **{name}**",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Не удалось отправить напоминание пользователю {telegram_id}: {e}")


def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        check_habits_for_notification,
        trigger='interval',
        minutes=1,
        kwargs={'bot': bot}
    )
    return scheduler
