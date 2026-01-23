from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .habits_jobs import check_habits_for_notification
from .events_jobs import check_events_for_notification


def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="UTC")

    # Привычки
    scheduler.add_job(
        check_habits_for_notification,
        trigger="interval",
        minutes=1,
        kwargs={"bot": bot},
    )

    # События
    scheduler.add_job(
        check_events_for_notification,
        trigger="interval",
        minutes=1,
        kwargs={"bot": bot},
    )

    return scheduler
