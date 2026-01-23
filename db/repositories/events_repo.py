# db/repositories/events_repo.py
from datetime import datetime, timezone, timedelta

from db.connection import get_conn
from ._helpers import _get_user_internal_id, _get_user_timezone_offset_or_zero


def add_event(
        telegram_id: int,
        title: str,
        event_datetime_iso: str,
        remind_day: int,
        remind_hour: int,
        remind_15_min: int,
        custom_remind_minutes: int | None = None,
        timezone_offset: int | None = None,
) -> int | None:
    """
    Создать событие.

    event_datetime_iso: "YYYY-MM-DD HH:MM" или "YYYY-MM-DD HH:MM:SS"
    event_datetime хранится как локальное время пользователя (MVP).
    """
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return None

    dt = datetime.fromisoformat(event_datetime_iso)
    dt_norm = dt.replace(second=0, microsecond=0).isoformat(sep=" ")

    if timezone_offset is None:
        timezone_offset = _get_user_timezone_offset_or_zero(telegram_id)

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO events (
                user_id, title, event_datetime, timezone_offset,
                remind_day, remind_hour, remind_15_min,
                custom_remind_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_internal_id,
                title.strip(),
                dt_norm,
                int(timezone_offset),
                int(bool(remind_day)),
                int(bool(remind_hour)),
                int(bool(remind_15_min)),
                (int(custom_remind_minutes) if custom_remind_minutes is not None else None),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def list_events(telegram_id: int, limit: int = 20):
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return []

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT event_id, title, event_datetime, remind_day, remind_hour, remind_15_min
            FROM events
            WHERE user_id = ?
            ORDER BY event_datetime ASC
            LIMIT ?
            """,
            (user_internal_id, limit),
        )
        return cursor.fetchall()


def update_event_title(telegram_id: int, event_id: int, new_title: str) -> bool:
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return False

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE events
            SET title = ?
            WHERE event_id = ?
              AND user_id = ?
            """,
            (new_title.strip(), int(event_id), int(user_internal_id)),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_event_datetime(telegram_id: int, event_id: int, new_event_datetime: str) -> bool:
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return False

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE events
            SET
                event_datetime = ?,
                reminded_day = 0,
                reminded_hour = 0,
                reminded_15_min = 0,
                reminded_custom = 0,
                reminded_at_event = 0
            WHERE event_id = ?
              AND user_id = ?
            """,
            (new_event_datetime, int(event_id), int(user_internal_id)),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_event_reminders(
        telegram_id: int,
        event_id: int,
        remind_day: int,
        remind_hour: int,
        remind_15_min: int,
        custom_remind_minutes,
        remind_at_event: int = 1,
) -> bool:
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return False

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE events
            SET
                remind_day = ?,
                remind_hour = ?,
                remind_15_min = ?,
                custom_remind_minutes = ?,
                remind_at_event = ?,
                reminded_day = 0,
                reminded_hour = 0,
                reminded_15_min = 0,
                reminded_custom = 0,
                reminded_at_event = 0
            WHERE event_id = ?
              AND user_id = ?
            """,
            (
                int(remind_day),
                int(remind_hour),
                int(remind_15_min),
                custom_remind_minutes,
                int(remind_at_event),
                int(event_id),
                int(user_internal_id),
            ),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_event(telegram_id: int, event_id: int) -> bool:
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return False

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE event_id = ? AND user_id = ?", (int(event_id), int(user_internal_id)))
        conn.commit()
        return cursor.rowcount > 0


def get_event_by_id(telegram_id: int, event_id: int):
    user_internal_id = _get_user_internal_id(telegram_id)
    if not user_internal_id:
        return None

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                event_id, title, event_datetime,
                COALESCE(timezone_offset, 0) AS tz_off,
                remind_day, remind_hour, remind_15_min,
                custom_remind_minutes,
                COALESCE(remind_at_event, 1) AS remind_at_event
            FROM events
            WHERE event_id = ? AND user_id = ?
            """,
            (int(event_id), int(user_internal_id)),
        )
        return cursor.fetchone()


def get_due_event_reminders(now_utc: datetime | None = None):
    """
    Возвращает список напоминаний, которые нужно отправить сейчас (в минутное окно).

    kinds:
      - "day"   : за 1 день
      - "hour"  : за 1 час
      - "15min" : за 15 минут
      - "at"    : в момент события (если включено и ещё не отправлено)

    event_datetime хранится как локальное время пользователя (MVP).
    timezone_offset берём из events.timezone_offset (если NULL) -> users.timezone_offset (если NULL) -> 0.
    """
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    due: list[dict] = []

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.event_id,
                e.title,
                e.event_datetime,
                COALESCE(e.timezone_offset, u.timezone_offset, 0) AS tz_off,

                e.remind_day,
                e.remind_hour,
                e.remind_15_min,

                e.reminded_day,
                e.reminded_hour,
                e.reminded_15_min,

                -- NEW: напоминание в момент события
                COALESCE(e.remind_at_event, 1)  AS remind_at_event,
                COALESCE(e.reminded_at_event, 0) AS reminded_at_event,

                e.custom_remind_minutes,
                COALESCE(e.reminded_custom, 0) AS reminded_custom,

                u.telegram_id
            FROM events e
            JOIN users u ON u.user_id = e.user_id
            """
        )
        rows = cursor.fetchall()

    for row in rows:
        (
            event_id,
            title,
            event_datetime_str,
            tz_off,
            remind_day,
            remind_hour,
            remind_15,
            reminded_day,
            reminded_hour,
            reminded_15,
            remind_at_event,
            reminded_at_event,
            custom_remind_minutes,
            reminded_custom,
            telegram_id,
        ) = row

        tz = timezone(timedelta(hours=int(tz_off or 0)))

        # event_datetime хранится как "локальное время пользователя" (naive) -> назначаем tzinfo
        try:
            event_local = datetime.fromisoformat(event_datetime_str).replace(tzinfo=tz)
        except ValueError:
            # если в БД мусорный формат даты — пропускаем
            continue

        event_utc = event_local.astimezone(timezone.utc)

        remind_points: list[tuple[str, datetime]] = []

        # Галочки
        if int(remind_day) == 1 and int(reminded_day) == 0:
            remind_points.append(("day", event_utc - timedelta(days=1)))
        if int(remind_hour) == 1 and int(reminded_hour) == 0:
            remind_points.append(("hour", event_utc - timedelta(hours=1)))
        if int(remind_15) == 1 and int(reminded_15) == 0:
            remind_points.append(("15min", event_utc - timedelta(minutes=15)))

        if custom_remind_minutes is not None and int(reminded_custom) == 0:
            try:
                cm = int(custom_remind_minutes)
                if cm > 0:
                    remind_points.append(("custom", event_utc - timedelta(minutes=cm)))
            except Exception:
                pass

        # В момент события (по умолчанию включено)
        if int(remind_at_event) == 1 and int(reminded_at_event) == 0:
            remind_points.append(("at", event_utc))

        for kind, target_utc in remind_points:
            if abs((now_utc - target_utc).total_seconds()) <= 60:
                due.append(
                    {
                        "telegram_id": int(telegram_id),
                        "event_id": int(event_id),
                        "kind": kind,
                        "title": title,
                        "event_dt_local": event_local,
                        "custom_minutes": int(custom_remind_minutes) if custom_remind_minutes is not None else None,
                    }
                )

    return due


def mark_event_reminded(event_id: int, kind: str) -> None:
    """
    Отмечает конкретный тип напоминания как отправленный.
    kind: 'day' | 'hour' | '15min' | 'custom' | 'at'
    """
    field_map = {
        "day": "reminded_day",
        "hour": "reminded_hour",
        "15min": "reminded_15_min",
        "custom": "reminded_custom",
        "at": "reminded_at_event",
    }

    field = field_map.get(kind)
    if not field:
        return

    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE events SET {field} = 1 WHERE event_id = ?", (int(event_id),))
        conn.commit()
