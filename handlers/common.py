from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import db_utils as db
import keyboards as kb

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    db.add_user_if_not_exists(user.id, user.first_name)
    await message.answer(f"Привет, {user.full_name}!", reply_markup=kb.main_kb)


@router.message(F.text == "⬅️ Назад в главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Вы вернулись в главное меню.", reply_markup=kb.main_kb)


@router.message(F.text == "📅 События")
async def open_events_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📅 Раздел «События».", reply_markup=kb.events_kb)

@router.message(F.text == "⚙️ Настройки")
async def open_settings_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⚙️ Настройки:", reply_markup=kb.settings_kb)