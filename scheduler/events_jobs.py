from datetime import datetime, timezone

from aiogram import Bot

from db_utils import get_due_event_reminders, mark_event_reminded


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
