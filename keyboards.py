# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- Главное меню ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Привычки"),
            KeyboardButton(text="📅 События"),
            KeyboardButton(text="Цели"),
        ],
        [
            KeyboardButton(text="Статистика"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие из меню"
)

# --- Меню Привычек ---
habits_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Создать привычку")],
        [KeyboardButton(text="📋 Мои привычки")],
        [KeyboardButton(text="⬅️ Назад в главное меню")],
    ],
    resize_keyboard=True
)


def get_days_of_week_kb(selected_days: set = None):
    if selected_days is None:
        selected_days = set()
    days = {"1": "Пн", "2": "Вт", "3": "Ср", "4": "Чт", "5": "Пт", "6": "Сб", "7": "Вс"}
    buttons = []
    row = []
    for day_id, day_name in days.items():
        text = f"✅ {day_name}" if day_id in selected_days else day_name
        row.append(InlineKeyboardButton(text=text, callback_data=f"day_{day_id}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="days_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


confirm_reminder_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да", callback_data="reminder_yes"),
     InlineKeyboardButton(text="Нет", callback_data="reminder_no")]
])


def get_habits_pagination_kb(habits: list, page: int = 0, page_size: int = 5):
    start, end = page * page_size, page * page_size + page_size
    buttons = []
    for habit_id, name, is_completed in habits[start:end]:
        display_name = f"✅ {name}" if is_completed else name
        buttons.append([InlineKeyboardButton(text=display_name, callback_data=f"view_habit_{habit_id}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"habits_page_{page - 1}"))
    if end < len(habits):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"habits_page_{page + 1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_habit_detail_kb(habit_id: int):
    buttons = [
        [InlineKeyboardButton(text="✅ Отметить выполненной", callback_data=f"track_{habit_id}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_habit_{habit_id}"),
         InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_habit_{habit_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_habits_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_delete_confirm_kb(habit_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{habit_id}"),
         InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_habit_{habit_id}")]
    ])


def get_edit_habit_kb(habit_id: int):
    buttons = [
        [InlineKeyboardButton(text="Название", callback_data=f"edit_field_name_{habit_id}")],
        [InlineKeyboardButton(text="Описание", callback_data=f"edit_field_description_{habit_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"view_habit_{habit_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- Клавиатуры для ЦЕЛЕЙ ---
goals_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Создать цель")],
        [KeyboardButton(text="🎯 Просмотр целей")],
        [KeyboardButton(text="⬅️ Назад в главное меню")],
    ],
    resize_keyboard=True
)


def get_goals_filter_kb(counts: dict):
    new_count = counts.get('new', 0)
    active_count = counts.get('active', 0)
    completed_count = counts.get('completed', 0)
    cancelled_count = counts.get('cancelled', 0)

    buttons = [
        [InlineKeyboardButton(text=f"🆕 Новые ({new_count})", callback_data="goals_filter_new")],
        [InlineKeyboardButton(text=f"⏳ В процессе ({active_count})", callback_data="goals_filter_active")],
        [InlineKeyboardButton(text=f"✅ Выполненные ({completed_count})", callback_data="goals_filter_completed")],
        [InlineKeyboardButton(text=f"❌ Отмененные ({cancelled_count})", callback_data="goals_filter_cancelled")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_goals_pagination_kb(goals: list, status: str, page: int = 0, page_size: int = 5):
    start, end = page * page_size, page * page_size + page_size
    buttons = []
    for goal_id, name in goals[start:end]:
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"view_goal_{goal_id}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"goals_page_{status}_{page - 1}"))
    if end < len(goals):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"goals_page_{status}_{page + 1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="↩️ К фильтрам", callback_data="back_to_goals_filters")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_goal_detail_kb(goal_id: int, current_status: str):
    buttons = []

    if current_status == 'new':
        buttons.append([
            InlineKeyboardButton(text="▶️ Взять в работу", callback_data=f"change_status_active_{goal_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"change_status_cancelled_{goal_id}")
        ])
    elif current_status == 'active':
        buttons.append([
            InlineKeyboardButton(text="✅ Выполнить", callback_data=f"change_status_completed_{goal_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"change_status_cancelled_{goal_id}")
        ])

    buttons.append([InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_goal_start_{goal_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data=f"goals_filter_{current_status}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_goal_delete_confirm_kb(goal_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_goal_confirm_{goal_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_goal_{goal_id}")
    ]])


# --- Меню раздела "Статистика" ---
stats_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📊 По привычкам", callback_data="stats_habits")],
        [InlineKeyboardButton(text="🎯 По целям", callback_data="stats_goals")]
    ]
)

# ==========================================================
# EVENTS (НОВОЕ)
# ==========================================================

events_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить событие")],
        [KeyboardButton(text="📋 Мои события")],
        [KeyboardButton(text="⬅️ Назад в главное меню")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Управление событиями"
)


def get_event_reminders_kb(selected: set | None = None) -> InlineKeyboardMarkup:
    """
    Галочки для напоминаний:
    - day
    - hour
    - 15min
    """
    if selected is None:
        selected = set()

    def label(key: str, text: str) -> str:
        return f"✅ {text}" if key in selected else text

    buttons = [
        [InlineKeyboardButton(text=label("day", "За день"), callback_data="ev_rem_day")],
        [InlineKeyboardButton(text=label("hour", "За час"), callback_data="ev_rem_hour")],
        [InlineKeyboardButton(text=label("15min", "За 15 минут"), callback_data="ev_rem_15min")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="ev_rem_done")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
