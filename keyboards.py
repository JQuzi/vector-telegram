from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- Главное меню ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Привычки"), KeyboardButton(text="Цели")],
        [KeyboardButton(text="Статистика")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие из меню"
)

# --- Меню раздела "Привычки" ---
habits_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Создать привычку")],
        [KeyboardButton(text="📋 Мои привычки")],
        [KeyboardButton(text="⬅️ Назад в главное меню")]
    ],
    resize_keyboard=True
)


# --- Клавиатура для выбора дней недели ---
# --- Клавиатура для выбора дней недели (ОБНОВЛЕННАЯ) ---
def get_days_of_week_kb(selected_days: set = None):
    """
    Создает клавиатуру для выбора дней недели.
    Добавляет '✅' к уже выбранным дням.
    """
    if selected_days is None:
        selected_days = set()

    days = {
        "1": "Пн", "2": "Вт", "3": "Ср", "4": "Чт",
        "5": "Пт", "6": "Сб", "7": "Вс"
    }

    buttons = []
    # Динамически создаем ряды кнопок
    row = []
    for day_id, day_name in days.items():
        # Проверяем, выбран ли этот день
        text = f"✅ {day_name}" if day_id in selected_days else day_name
        row.append(InlineKeyboardButton(text=text, callback_data=f"day_{day_id}"))

        # Делаем по 4 кнопки в ряду
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:  # Добавляем оставшиеся кнопки
        buttons.append(row)

    # Добавляем кнопку "Готово"
    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="days_done")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# --- Клавиатура для подтверждения напоминания ---
confirm_reminder_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Да", callback_data="reminder_yes"),
        InlineKeyboardButton(text="Нет", callback_data="reminder_no")
    ]
])


# --- ОБНОВЛЕНО: Клавиатура для пагинации ---
def get_habits_pagination_kb(habits: list, page: int = 0, page_size: int = 5):
    """Добавляет '✅' к выполненным привычкам."""
    start = page * page_size
    end = start + page_size

    buttons = []
    # Теперь habits содержит (habit_id, name, is_completed)
    for habit_id, name, is_completed in habits[start:end]:
        # Добавляем галочку, если привычка выполнена
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


# --- НОВАЯ КЛАВИАТУРА: Меню для конкретной привычки ---
def get_habit_detail_kb(habit_id: int):
    """Создает клавиатуру для 'карточки привычки'."""
    buttons = [
        [InlineKeyboardButton(text="✅ Отметить выполненной", callback_data=f"track_{habit_id}")],
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_habit_{habit_id}"),
            InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_habit_{habit_id}")
        ],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="habits_page_0")]  # Возврат на 1-ю страницу
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_delete_confirm_kb(habit_id: int):
    """Клавиатура для подтверждения удаления."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{habit_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_habit_{habit_id}") # Возврат к карточке
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_edit_habit_kb(habit_id: int):
    """Клавиатура для выбора поля для редактирования."""
    buttons = [
        [InlineKeyboardButton(text="Название", callback_data=f"edit_field_name_{habit_id}")],
        [InlineKeyboardButton(text="Описание", callback_data=f"edit_field_description_{habit_id}")],
        # [InlineKeyboardButton(text="Дни недели", callback_data=f"edit_field_days_{habit_id}")], # Пока в разработке
        # [InlineKeyboardButton(text="Время напоминания", callback_data=f"edit_field_time_{habit_id}")], # Пока в разработке
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"view_habit_{habit_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

