from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

import db_utils as db
import keyboards as kb

router = Router()


class SettingsStates(StatesGroup):
    timezone = State()


@router.message(F.text == "🕒 Таймзона")
async def settings_timezone_start(message: Message, state: FSMContext):
    cur = db.get_user_timezone(message.from_user.id)
    cur_txt = f"Сейчас: UTC{int(cur):+}" if cur is not None else "Сейчас: не задана"

    await state.set_state(SettingsStates.timezone)
    await message.answer(
        f"🕒 Настройка таймзоны.\n{cur_txt}\n\n"
        "Введите смещение от UTC числом, например:\n"
        "• -5\n"
        "• 0\n"
        "• +3\n\n"
        "Диапазон: от -12 до +14."
    )

@router.message(SettingsStates.timezone, F.text == "⬅️ Назад в главное меню")
async def settings_timezone_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ок, отменил.", reply_markup=kb.main_kb)

@router.message(SettingsStates.timezone)
async def settings_timezone_save(message: Message, state: FSMContext):
    text = (message.text or "").strip().replace("UTC", "").replace("utc", "")

    try:
        offset = int(text)
        if not (-12 <= offset <= 14):
            raise ValueError
    except ValueError:
        await message.answer("Неверный формат. Введите число от -12 до +14 (например, +3).")
        return

    db.set_user_timezone(message.from_user.id, offset)
    await state.clear()
    await message.answer(f"✅ Таймзона сохранена: UTC{offset:+}", reply_markup=kb.settings_kb)


