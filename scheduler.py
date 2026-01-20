import sqlite3
from datetime import datetime, timezone, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db_utils import get_due_event_reminders, mark_event_reminded

DB_FILE = "vector.db"


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

        if str(user_current_weekday) in days_of_week.split(","):
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=f"⏰ *Напоминание!*\n\nНе забудьте про вашу привычку: *{name}*",
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Не удалось отправить напоминание пользователю {telegram_id}: {e}")


async def check_events_for_notification(bot: Bot):
    """
    Проверяем события (таблица events) и отправляем напоминания:
    - за день
    - за час
    - за 15 минут

    Важно: функция get_due_event_reminders() сама вычисляет, что нужно отправить
    в текущее минутное окно.
    """
    now_utc = datetime.now(timezone.utc)
    due = get_due_event_reminders(now_utc)

    if not due:
        return

    for item in due:
        telegram_id = item["telegram_id"]
        event_id = item["event_id"]
        kind = item["kind"]
        title = item["title"]
        event_dt_local = item["event_dt_local"]  # datetime с tzinfo

        when_str = event_dt_local.strftime("%d.%m %H:%M")

        if kind == "day":
            prefix = "📅 Завтра"
        elif kind == "hour":
            prefix = "⏳ Через час"
        elif kind == "15min":
            prefix = "⚠️ Через 15 минут"
        elif kind == "custom":
            cm = item.get("custom_minutes")
            prefix = f"⏱ Через {cm} мин" if cm else "⏱ Скоро"
        else:  # "at"
            prefix = "🔔 Сейчас"
        text = (
            f"{prefix}: *{title}*\n"
            f"🕒 {when_str}"
        )

        try:
            await bot.send_message(chat_id=telegram_id, text=text, parse_mode="Markdown")
            mark_event_reminded(event_id, kind)
        except Exception as e:
            print(f"Не удалось отправить напоминание о событии пользователю {telegram_id}: {e}")


def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="UTC")

    # Привычки (как было)
    scheduler.add_job(
        check_habits_for_notification,
        trigger="interval",
        minutes=1,
        kwargs={"bot": bot},
    )

    # События (НОВОЕ)
    scheduler.add_job(
        check_events_for_notification,
        trigger="interval",
        minutes=1,
        kwargs={"bot": bot},
    )

    return scheduler
