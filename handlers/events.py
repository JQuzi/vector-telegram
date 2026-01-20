from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import db_utils as db
import keyboards as kb

router = Router()


class EventStates(StatesGroup):
    title = State()
    datetime = State()
    timezone = State()
    reminders = State()
    custom_minutes = State()


# ----------------------------
# Date parsing (human-friendly)
# ----------------------------

@dataclass(frozen=True)
class ParsedDateTime:
    dt: datetime  # naive local datetime (user local)
    pretty: str


_TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*$")
_DMY_RE = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?\s+(\d{1,2}):(\d{2})\s*$")
_ISO_RE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s*$")


def _parse_time_piece(s: str) -> tuple[int, int] | None:
    m = _TIME_RE.match(s)
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None
    return hh, mm


def parse_human_datetime(text: str, now_local: datetime) -> ParsedDateTime | None:
    """
    Возвращает naive datetime в локальном времени пользователя (без tzinfo).
    now_local тоже naive (локальное время пользователя).

    Поддержка:
      - "сегодня 19:00"
      - "завтра 09:15"
      - "31.01 18:00" / "31.01.2026 18:00"
      - "2026-01-31 18:00"
      - "конец месяца 18:00" / "конец месяца"
    """
    t = text.strip().lower()

    # ISO: YYYY-MM-DD HH:MM
    m = _ISO_RE.match(t)
    if m:
        y, mo, d, hh, mm = map(int, m.groups())
        try:
            dt = datetime(y, mo, d, hh, mm)
            return ParsedDateTime(dt=dt, pretty=dt.strftime("%d.%m.%Y %H:%M"))
        except ValueError:
            return None

    # D.M[.YYYY] HH:MM
    m = _DMY_RE.match(t)
    if m:
        d = int(m.group(1))
        mo = int(m.group(2))
        y = int(m.group(3)) if m.group(3) else now_local.year
        hh = int(m.group(4))
        mm = int(m.group(5))
        try:
            dt = datetime(y, mo, d, hh, mm)
        except ValueError:
            return None

        # Если год не указан и дата уже прошла — переносим на следующий год
        if not m.group(3) and dt < now_local:
            try:
                dt = datetime(now_local.year + 1, mo, d, hh, mm)
            except ValueError:
                return None

        return ParsedDateTime(dt=dt, pretty=dt.strftime("%d.%m.%Y %H:%M"))

    # "сегодня HH:MM"
    if t.startswith("сегодня"):
        rest = t.replace("сегодня", "", 1).strip()
        tm = _parse_time_piece(rest)
        if not tm:
            return None
        hh, mm = tm
        dt = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0)
        return ParsedDateTime(dt=dt, pretty=dt.strftime("%d.%m.%Y %H:%M"))

    # "завтра HH:MM"
    if t.startswith("завтра"):
        rest = t.replace("завтра", "", 1).strip()
        tm = _parse_time_piece(rest)
        if not tm:
            return None
        hh, mm = tm
        base = (now_local + timedelta(days=1)).replace(second=0, microsecond=0)
        dt = base.replace(hour=hh, minute=mm)
        return ParsedDateTime(dt=dt, pretty=dt.strftime("%d.%m.%Y %H:%M"))

    # "конец месяца [HH:MM]"
    if t.startswith("конец месяца"):
        rest = t.replace("конец месяца", "", 1).strip()
        tm = _parse_time_piece(rest) if rest else (9, 0)  # дефолт 09:00
        if not tm:
            return None
        hh, mm = tm
        last_day = calendar.monthrange(now_local.year, now_local.month)[1]
        dt = datetime(now_local.year, now_local.month, last_day, hh, mm)

        # Если конец месяца уже прошёл (например, сегодня последний день и время прошло) — берём конец следующего месяца
        if dt < now_local:
            y = now_local.year
            mo = now_local.month + 1
            if mo == 13:
                mo = 1
                y += 1
            last_day2 = calendar.monthrange(y, mo)[1]
            dt = datetime(y, mo, last_day2, hh, mm)

        return ParsedDateTime(dt=dt, pretty=dt.strftime("%d.%m.%Y %H:%M"))

    return None


def _events_list_kb(rows) -> InlineKeyboardMarkup:
    """
    rows: список кортежей/строк sqlite:
      (event_id, title, event_datetime, remind_day, remind_hour, remind_15_min)
    """
    buttons: list[list[InlineKeyboardButton]] = []
    for r in rows:
        event_id = r[0]
        title = r[1]
        dt_str = r[2]
        # Кнопка удаления. Заголовок в кнопке — сокращаем.
        short = title if len(title) <= 28 else title[:28] + "…"
        buttons.append([InlineKeyboardButton(text=f"🗑 {short} ({dt_str})", callback_data=f"ev_del_{event_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else InlineKeyboardMarkup(inline_keyboard=[])


# ----------------------------
# Handlers
# ----------------------------

@router.message(F.text == "➕ Добавить событие")
async def add_event_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ок! Напиши название события 📝")
    await state.set_state(EventStates.title)


@router.message(EventStates.title)
async def add_event_set_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не должно быть пустым. Напиши ещё раз 🙂")
        return

    await state.update_data(title=title)
    await message.answer(
        "Теперь дата и время.\n\n"
        "Примеры:\n"
        "• завтра 19:00\n"
        "• сегодня 09:15\n"
        "• 31.01 18:00\n"
        "• конец месяца 18:00\n"
        "• 2026-01-31 18:00"
    )
    await state.set_state(EventStates.datetime)


@router.message(EventStates.datetime)
async def add_event_set_datetime(message: Message, state: FSMContext):
    tz_off = db.get_user_timezone(message.from_user.id)

    # Если таймзона не задана — просим и запоминаем введённую дату
    if tz_off is None:
        await state.update_data(pending_datetime_text=message.text)
        await state.set_state(EventStates.timezone)
        await message.answer("Укажите ваш часовой пояс (например, +3):")
        return

    tz_off = int(tz_off)

    # Локальное "сейчас" пользователя (naive datetime)
    now_local = datetime.utcnow() + timedelta(hours=tz_off)

    # Парсим ввод пользователя
    parsed = parse_human_datetime(message.text or "", now_local)
    if not parsed:
        await message.answer(
            "Не понял дату 😅\n"
            "Напиши в одном из форматов, например: `завтра 19:00` или `31.01 18:00`",
            parse_mode="Markdown",
        )
        return

    if parsed.dt < now_local:
        await message.answer("Это время уже в прошлом. Дай дату/время в будущем 🙂")
        return

    dt_norm = parsed.dt.replace(second=0, microsecond=0).isoformat(sep=" ")

    await state.update_data(
        event_datetime_iso=dt_norm,
        tz_off=tz_off,
        remind_selected=set(),
    )

    data = await state.get_data()
    await message.answer(
        f"Событие: *{data['title']}*\n"
        f"Когда: *{parsed.pretty}*\n\n"
        f"Выбери напоминания галочками:",
        reply_markup=kb.get_event_reminders_kb(set()),
        parse_mode="Markdown",
    )
    await state.set_state(EventStates.reminders)

@router.message(EventStates.timezone)
async def process_event_timezone(message: Message, state: FSMContext):
    text = (message.text or "").strip().replace("UTC", "").replace("utc", "")

    try:
        offset = int(text)
        if not (-12 <= offset <= 14):
            raise ValueError
    except ValueError:
        await message.answer("Неверный формат. Введите число (например, +3).")
        return

    db.set_user_timezone(message.from_user.id, offset)

    data = await state.get_data()
    pending_text = data.get("pending_datetime_text")

    await state.set_state(EventStates.datetime)
    await message.answer(f"✅ Часовой пояс установлен: UTC{offset:+}.\n\nТеперь ещё раз введи дату и время события:")


@router.callback_query(
    EventStates.reminders,
    F.data.in_({"ev_rem_day", "ev_rem_hour", "ev_rem_15min", "ev_rem_custom", "ev_rem_done"})
)
async def event_reminders_click(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected: set = data.get("remind_selected", set())
    if not isinstance(selected, set):
        selected = set(selected or [])

    # ─── toggle стандартных напоминаний ──────────────────────────────
    if cb.data == "ev_rem_day":
        selected.symmetric_difference_update({"day"})

    elif cb.data == "ev_rem_hour":
        selected.symmetric_difference_update({"hour"})

    elif cb.data == "ev_rem_15min":
        selected.symmetric_difference_update({"15min"})

    # ─── кастомные минуты ─────────────────────────────────────────────
    elif cb.data == "ev_rem_custom":
        await state.set_state(EventStates.custom_minutes)
        await cb.message.answer(
            "⏱ Введи число минут, за сколько напомнить до события.\n"
            "Например: 30\n\n"
            "Чтобы отключить кастомное напоминание — введи 0."
        )
        await cb.answer()
        return

    # ─── сохранение события ──────────────────────────────────────────
    elif cb.data == "ev_rem_done":
        title = data["title"]
        event_datetime_iso = data["event_datetime_iso"]
        tz_off = int(data.get("tz_off", 0))

        remind_day = 1 if "day" in selected else 0
        remind_hour = 1 if "hour" in selected else 0
        remind_15 = 1 if "15min" in selected else 0

        custom_minutes = data.get("custom_remind_minutes")
        if custom_minutes is not None:
            try:
                custom_minutes = int(custom_minutes)
            except (TypeError, ValueError):
                custom_minutes = None

        db.add_event(
            telegram_id=cb.from_user.id,
            title=title,
            event_datetime_iso=event_datetime_iso,
            remind_day=remind_day,
            remind_hour=remind_hour,
            remind_15_min=remind_15,
            timezone_offset=tz_off,
            custom_remind_minutes=custom_minutes,
        )

        await state.clear()
        await cb.message.answer("✅ Событие сохранено!", reply_markup=kb.events_kb)
        await cb.answer()
        return

    # ─── обновляем FSM и клавиатуру ───────────────────────────────────
    await state.update_data(remind_selected=selected)

    try:
        await cb.message.edit_reply_markup(
            reply_markup=kb.get_event_reminders_kb(selected)
        )
    except Exception:
        pass

    await cb.answer()

@router.message(EventStates.custom_minutes)
async def event_set_custom_minutes(message: Message, state: FSMContext):
    text = (message.text or "").strip()

    try:
        minutes = int(text)
    except ValueError:
        await message.answer("Нужно ввести целое число минут (например: 30).")
        return

    data = await state.get_data()
    selected: set = data.get("remind_selected", set())
    if not isinstance(selected, set):
        selected = set(selected or [])

    if minutes <= 0:
        # выключаем кастомное напоминание
        selected.discard("custom")
        await state.update_data(
            custom_remind_minutes=None,
            remind_selected=selected,
        )
    else:
        # включаем / обновляем кастом
        selected.add("custom")
        await state.update_data(
            custom_remind_minutes=minutes,
            remind_selected=selected,
        )

    # возвращаемся к выбору напоминаний
    await state.set_state(EventStates.reminders)

    await message.answer(
        "✅ Готово. Выбери напоминания:",
        reply_markup=kb.get_event_reminders_kb(selected),
    )


@router.message(F.text == "📋 Мои события")
async def list_events_handler(message: Message):
    rows = db.list_events(message.from_user.id, limit=30)
    if not rows:
        await message.answer("У тебя пока нет событий. Нажми «➕ Добавить событие».", reply_markup=kb.events_kb)
        return

    await message.answer(
        "📋 Твои события (нажми, чтобы удалить):",
        reply_markup=_events_list_kb(rows)
    )


@router.callback_query(F.data.startswith("ev_del_"))
async def delete_event_cb(cb: CallbackQuery):
    try:
        event_id = int(cb.data.split("_")[-1])
    except Exception:
        await cb.answer("Не понял id события", show_alert=True)
        return

    ok = db.delete_event(cb.from_user.id, event_id)
    if not ok:
        await cb.answer("Не удалось удалить (возможно уже удалено).", show_alert=True)
        return

    await cb.answer("Удалено ✅")
    # Обновим список
    rows = db.list_events(cb.from_user.id, limit=30)
    if not rows:
        await cb.message.edit_text("Событий больше нет.")
        return
    await cb.message.edit_reply_markup(reply_markup=_events_list_kb(rows))
