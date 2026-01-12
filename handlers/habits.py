import re
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

import db_utils as db
import keyboards as kb

router = Router()


class HabitCreation(StatesGroup):
    name, description, days, reminder, timezone, reminder_time = (State(), State(), State(), State(), State(), State())


class HabitEditing(StatesGroup):
    waiting_for_new_value = State()


async def show_habit_card(callback_or_message: types.Union[CallbackQuery, Message], habit_id: int, state: FSMContext):
    await state.clear()
    details = db.get_habit_details(habit_id)
    if not details:
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text("Эта привычка была удалена.")
            await callback_or_message.answer()
        return

    name, description, days_of_week, reminder_time = details
    days_map = {"1": "Пн", "2": "Вт", "3": "Ср", "4": "Чт", "5": "Пт", "6": "Сб", "7": "Вс"}
    days_str = ", ".join([days_map[d] for d in days_of_week.split(',')]) if days_of_week else "Не задано"
    text = (
        f"**Привычка: {name}**\n\n📝 **Описание:** {description}\n🗓️ **Дни:** {days_str}\n⏰ **Напоминание:** {reminder_time or 'Нет'}")
    keyboard = kb.get_habit_detail_kb(habit_id)

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback_or_message.answer()
    else:
        await callback_or_message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(F.text == "Привычки")
async def habits_menu(message: Message):
    await message.answer("Раздел 'Привычки'. Что вы хотите сделать?", reply_markup=kb.habits_kb)


@router.message(F.text == "📋 Мои привычки")
async def my_habits_handler(message: Message):
    habits = db.get_user_habits(message.from_user.id)
    if not habits:
        await message.answer("У вас пока нет созданных привычек.")
        return
    keyboard = kb.get_habits_pagination_kb(habits, page=0)
    await message.answer("📋 **Ваши привычки:**", reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data.startswith('habits_page_'))
async def habits_pagination_handler(callback: CallbackQuery):
    page = int(callback.data.split('_')[2])
    habits = db.get_user_habits(callback.from_user.id)
    keyboard = kb.get_habits_pagination_kb(habits, page=page)
    await callback.message.edit_text("📋 **Ваши привычки:**", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith('view_habit_'))
async def view_habit_handler(callback: CallbackQuery, state: FSMContext):
    habit_id = int(callback.data.split('_')[2])
    await show_habit_card(callback, habit_id, state)


@router.callback_query(F.data.startswith('track_'))
async def track_habit_callback(callback: CallbackQuery, state: FSMContext):
    habit_id = int(callback.data.split('_')[1])
    db.track_habit(habit_id)
    await callback.answer("✅ Отмечено!", show_alert=False)
    await show_habit_card(callback, habit_id, state)


@router.callback_query(F.data.startswith('edit_habit_'))
async def edit_habit_handler(callback: CallbackQuery):
    habit_id = int(callback.data.split('_')[2])
    keyboard = kb.get_edit_habit_kb(habit_id)
    await callback.message.edit_text("Что вы хотите изменить?", reply_markup=keyboard)


@router.callback_query(F.data.startswith('delete_habit_'))
async def delete_habit_start_handler(callback: CallbackQuery):
    habit_id = int(callback.data.split('_')[2])
    keyboard = kb.get_delete_confirm_kb(habit_id)
    await callback.message.edit_text("Вы уверены, что хотите удалить эту привычку?", reply_markup=keyboard)


@router.callback_query(F.data.startswith('confirm_delete_'))
async def delete_habit_confirm_handler(callback: CallbackQuery):
    habit_id = int(callback.data.split('_')[2])
    db.delete_habit(habit_id)

    habits = db.get_user_habits(callback.from_user.id)
    if not habits:
        await callback.message.edit_text("Привычка удалена. У вас больше нет привычек.", reply_markup=None)
        return

    keyboard = kb.get_habits_pagination_kb(habits, page=0)
    await callback.message.edit_text("Привычка удалена. Вот ваш обновленный список:", reply_markup=keyboard,
                                     parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith('edit_field_'))
async def edit_habit_field_handler(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split('_')
    field, habit_id = parts[2], int(parts[3])
    await state.set_state(HabitEditing.waiting_for_new_value)
    await state.update_data(habit_id=habit_id, field_to_edit=field)
    prompts = {"name": "Введите новое название:", "description": "Введите новое описание:"}
    await callback.message.edit_text(prompts.get(field, "Введите новое значение:"))
    await callback.answer()


@router.message(StateFilter(HabitEditing.waiting_for_new_value))
async def process_new_value_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    habit_id = data['habit_id']
    field = data['field_to_edit']
    new_value = message.text
    db.update_habit_field(habit_id, field, new_value)
    await message.answer("✅ Изменения сохранены!")
    await show_habit_card(message, habit_id, state)


@router.message(F.text == "➕ Создать привычку")
async def create_habit_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(HabitCreation.name)
    await message.answer("Введите название новой привычки:")


@router.message(StateFilter(HabitCreation.name))
async def process_habit_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(HabitCreation.description)
    await message.answer("Отлично! Теперь введите краткое описание:")


@router.message(StateFilter(HabitCreation.description))
async def process_habit_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.update_data(selected_days=set())
    await state.set_state(HabitCreation.days)
    await message.answer("Выберите дни недели:", reply_markup=kb.get_days_of_week_kb())


@router.callback_query(F.data.startswith('day_'), StateFilter(HabitCreation.days))
async def process_habit_days_callback(callback: CallbackQuery, state: FSMContext):
    day_id = callback.data.split('_')[1]
    data = await state.get_data()
    selected_days = data.get('selected_days', set()).copy()

    if day_id in selected_days:
        selected_days.remove(day_id)
    else:
        selected_days.add(day_id)

    await state.update_data(selected_days=selected_days)

    new_keyboard = kb.get_days_of_week_kb(selected_days)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)
    await callback.answer()


@router.callback_query(F.data == 'days_done', StateFilter(HabitCreation.days))
async def process_days_done_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(HabitCreation.reminder)
    await callback.message.answer("Нужно ли напоминание?", reply_markup=kb.confirm_reminder_kb)


@router.callback_query(F.data.startswith('reminder_'), StateFilter(HabitCreation.reminder))
async def process_reminder_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()

    if 'name' not in data:
        await callback.message.answer("Произошла ошибка, данные были утеряны. Начните заново.",
                                      reply_markup=kb.habits_kb)
        await state.clear()
        return

    if callback.data == "reminder_yes":
        user_timezone = db.get_user_timezone(callback.from_user.id)
        if user_timezone is None:
            await state.set_state(HabitCreation.timezone)
            await callback.message.answer("Укажите ваш часовой пояс (например, +3):")
        else:
            await state.set_state(HabitCreation.reminder_time)
            await callback.message.answer("Введите время для напоминания (ЧЧ:ММ):")
    else:
        db.save_habit(
            telegram_id=callback.from_user.id,
            name=data.get('name'),
            description=data.get('description'),
            days=list(data.get('selected_days', []))
        )
        await state.clear()
        await callback.message.answer("✅ Привычка успешно создана!", reply_markup=kb.habits_kb)


@router.message(StateFilter(HabitCreation.timezone))
async def process_timezone(message: Message, state: FSMContext):
    try:
        offset = int(message.text)
        if not (-12 <= offset <= 14): raise ValueError
        db.set_user_timezone(message.from_user.id, offset)
        await state.set_state(HabitCreation.reminder_time)
        await message.answer(f"Часовой пояс установлен: UTC{offset:+}.\n\nВведите время напоминания (ЧЧ:ММ):")
    except (ValueError, TypeError):
        await message.answer("Неверный формат. Введите число (например, +3).")


@router.message(StateFilter(HabitCreation.reminder_time))
async def process_reminder_time(message: Message, state: FSMContext):
    if not re.match(r'^\d{2}:\d{2}$', message.text):
        await message.answer("Неверный формат времени. Введите в формате ЧЧ:ММ:")
        return
    data = await state.get_data()

    if 'name' not in data:
        await message.answer("Произошла ошибка, данные были утеряны. Начните заново.", reply_markup=kb.habits_kb)
        await state.clear()
        return

    db.save_habit(
        telegram_id=message.from_user.id,
        name=data.get('name'),
        description=data.get('description'),
        days=list(data.get('selected_days', [])),
        reminder_time=message.text
    )
    await state.clear()
    await message.answer("✅ Привычка с напоминанием создана!", reply_markup=kb.habits_kb)
