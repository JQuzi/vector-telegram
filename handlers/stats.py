# handlers/stats.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

import keyboards as kb
import db_utils as db

router = Router()


@router.message(F.text == "Статистика")
async def stats_menu(message: Message):
    await message.answer("По какому разделу вы хотите посмотреть статистику?", reply_markup=kb.stats_menu_kb)


@router.callback_query(F.data == "stats_habits")
async def stats_habits_handler(callback: CallbackQuery):
    week_count, month_count = db.get_habit_completion_stats(callback.from_user.id)

    text = (
        "**📊 Статистика по привычкам:**\n\n"
        f"✅ Выполнено за последние 7 дней: **{week_count}**\n"
        f"🗓️ Выполнено за последние 30 дней: **{month_count}**\n\n"
        "*В будущем здесь появятся красивые графики!*"
    )

    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "stats_goals")
async def stats_goals_handler(callback: CallbackQuery):
    counts = db.get_goals_counts(callback.from_user.id)

    new_count = counts.get('new', 0)
    active_count = counts.get('active', 0)
    completed_count = counts.get('completed', 0)
    cancelled_count = counts.get('cancelled', 0)

    total = new_count + active_count + completed_count + cancelled_count

    text = (
        "**🎯 Статистика по целям:**\n\n"
        f"🆕 Новые: **{new_count}**\n"
        f"⏳ В процессе: **{active_count}**\n"
        f"✅ Выполненные: **{completed_count}**\n"
        f"❌ Отмененные: **{cancelled_count}**\n\n"
        f"**Всего целей: {total}**"
    )

    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

