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

# Заглушки для будущих разделов
@router.message(F.text.in_({"Цели", "Статистика"}))
async def not_implemented_handler(message: Message):
    await message.answer("Этот раздел находится в разработке.")

