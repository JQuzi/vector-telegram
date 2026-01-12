from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

import keyboards as kb
import db_utils as db

router = Router()


class GoalCreation(StatesGroup):
    name, description = State(), State()


async def show_goal_filters(callback_or_message: types.Union[CallbackQuery, Message]):
    counts = db.get_goals_counts(callback_or_message.from_user.id)
    keyboard = kb.get_goals_filter_kb(counts)
    text = "Выберите, какие цели вы хотите посмотреть:"
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback_or_message.answer(text, reply_markup=keyboard)


async def show_goal_card(callback: CallbackQuery, goal_id: int):
    details = db.get_goal_details(goal_id)
    if not details:
        await callback.answer("Цель не найдена.", show_alert=True)
        await show_goal_filters(callback)
        return

    name, description, status = details
    status_map = {'new': '🆕 Новая', 'active': '⏳ В процессе', 'completed': '✅ Выполнена', 'cancelled': '❌ Отменена'}
    text = f"**Цель: {name}**\n\n📝 **Описание:** {description}\n\n*Статус: {status_map.get(status, status)}*"
    keyboard = kb.get_goal_detail_kb(goal_id, status)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.message(F.text == "Цели")
async def goals_menu(message: Message):
    await message.answer("Раздел 'Цели'.", reply_markup=kb.goals_kb)


@router.message(F.text == "🎯 Просмотр целей")
async def view_goals_entry(message: Message):
    await show_goal_filters(message)


@router.callback_query(F.data == "back_to_goals_filters")
async def back_to_goals_filters_handler(callback: CallbackQuery):
    await show_goal_filters(callback)


@router.callback_query(F.data.startswith('goals_filter_'))
async def process_goals_filter(callback: CallbackQuery):
    status = callback.data.split('_')[2]
    goals = db.get_goals_by_status(callback.from_user.id, status)

    if not goals:
        await callback.message.edit_text(f"У вас нет целей в этом статусе.")
        await callback.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="↩️ К фильтрам", callback_data="back_to_goals_filters")]]))
        return

    keyboard = kb.get_goals_pagination_kb(goals, status, page=0)
    await callback.message.edit_text(f"**Цели в статусе '{status.capitalize()}':**", reply_markup=keyboard,
                                     parse_mode="Markdown")


@router.callback_query(F.data.startswith('goals_page_'))
async def process_goals_pagination(callback: CallbackQuery):
    _, _, status, page = callback.data.split('_')
    page = int(page)
    goals = db.get_goals_by_status(callback.from_user.id, status)
    keyboard = kb.get_goals_pagination_kb(goals, status, page=page)
    await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(F.data.startswith('view_goal_'))
async def view_goal_handler(callback: CallbackQuery):
    goal_id = int(callback.data.split('_')[2])
    await show_goal_card(callback, goal_id)


@router.callback_query(F.data.startswith('change_status_'))
async def change_goal_status_handler(callback: CallbackQuery):
    _, _, new_status, goal_id = callback.data.split('_')
    goal_id = int(goal_id)
    db.update_goal_status(goal_id, new_status)
    await show_goal_card(callback, goal_id)


@router.callback_query(F.data.startswith('delete_goal_start_'))
async def delete_goal_start_handler(callback: CallbackQuery):
    # ИСПРАВЛЕНО
    goal_id = int(callback.data.split('_')[3])
    keyboard = kb.get_goal_delete_confirm_kb(goal_id)
    await callback.message.edit_text("Вы уверены, что хотите удалить эту цель? Действие необратимо.",
                                     reply_markup=keyboard)


@router.callback_query(F.data.startswith('delete_goal_confirm_'))
async def delete_goal_confirm_handler(callback: CallbackQuery):
    # ИСПРАВЛЕНО
    goal_id = int(callback.data.split('_')[3])
    db.delete_goal(goal_id)
    await callback.answer("Цель удалена.", show_alert=True)
    await show_goal_filters(callback)


# ... (FSM для создания цели без изменений)
@router.message(F.text == "➕ Создать цель")
async def create_goal_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(GoalCreation.name)
    await message.answer("Введите название цели:", reply_markup=types.ReplyKeyboardRemove())


@router.message(StateFilter(GoalCreation.name))
async def process_goal_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(GoalCreation.description)
    await message.answer("Отлично! Теперь введите описание.")


@router.message(StateFilter(GoalCreation.description))
async def process_goal_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    data = await state.get_data()
    db.save_goal(telegram_id=message.from_user.id, name=data.get('name'), description=data.get('description'))
    await state.clear()
    await message.answer("✅ Новая цель успешно создана!", reply_markup=kb.goals_kb)

