# main.py

import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os

load_dotenv()
# Импортируем наши роутеры
from handlers import common, habits, goals, stats


API_TOKEN = os.getenv("API_TOKEN")


async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры к главному диспетчеру
    dp.include_router(common.router)
    dp.include_router(habits.router)
    dp.include_router(goals.router)
    dp.include_router(stats.router)

    print("Бот 'Вектор' и планировщик напоминаний запущены...")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
