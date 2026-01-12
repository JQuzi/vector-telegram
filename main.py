import asyncio
from aiogram import Bot, Dispatcher

# Импортируем наши роутеры и планировщик
from handlers import common, habits
from scheduler import setup_scheduler  # <-- НОВЫЙ ИМПОРТ

API_TOKEN = '7347989523:AAFhnQ-udpOIys3siLaWmKeEZ_5I_eG6_PY'


async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(common.router)
    dp.include_router(habits.router)

    # Настраиваем и запускаем планировщик
    scheduler = setup_scheduler(bot)  # <-- НОВАЯ СТРОКА
    scheduler.start()  # <-- НОВАЯ СТРОКА

    print("Бот 'Вектор' и планировщик напоминаний запущены...")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
