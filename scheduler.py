import sqlite3
from datetime import datetime, timezone, timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

DB_FILE = 'vector.db'

async def check_habits_for_notification(bot: Bot):
    query = """
    SELECT
        h.name, h.days_of_week, u.telegram_id, u.timezone_offset
    FROM habits h JOIN users u ON h.user_id = u.user_id
    WHERE h.reminder_time = strftime('%H:%M', 'now', u.timezone_offset || ' hours')
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        potential_notifications = cursor.execute(query).fetchall()

    if not potential_notifications:
        return

    for name, days_of_week, telegram_id, offset in potential_notifications:
        user_tz = timezone(timedelta(hours=offset))
        user_current_weekday = datetime.now(user_tz).weekday() + 1

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
