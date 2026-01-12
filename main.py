# main.py

import asyncio
from aiogram import Bot, Dispatcher

# Импортируем наши роутеры
from handlers import common, habits, goals  # <-- ДОБАВИЛИ goals
from handlers import common, habits, goals, stats

API_TOKEN = '7347989523:AAFhnQ-udpOIys3siLaWmKeEZ_5I_eG6_PY'


async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры к главному диспетчеру
    dp.include_router(common.router)
    dp.include_router(habits.router)
    dp.include_router(goals.router)  # <-- ПОДКЛЮЧИЛИ НОВЫЙ РОУТЕР
    dp.include_router(stats.router)

    print("Бот 'Вектор' и планировщик напоминаний запущены...")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
