# main.py

import asyncio
from aiogram import Bot, Dispatcher
from config import API_TOKEN

from database import init_db

from scheduler import setup_scheduler


from handlers import common, habits, goals, stats, events, settings


async def main():
    init_db()
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    dp.include_router(common.router)
    dp.include_router(habits.router)
    dp.include_router(goals.router)
    dp.include_router(stats.router)
    dp.include_router(events.router)
    dp.include_router(settings.router)

    # создаём и запускаем планировщик
    scheduler = setup_scheduler(bot)
    scheduler.start()

    print("Бот 'Вектор' и планировщик напоминаний запущены...")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
