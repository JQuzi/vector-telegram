# db/repositories/stats_repo.py
from db.connection import get_conn


def get_habit_completion_stats(telegram_id: int):
    """Считает, сколько раз привычки были выполнены за 7 и 30 дней."""
    with get_conn() as conn:
        cursor = conn.cursor()

        query = """
        SELECT
            SUM(CASE WHEN ht.completion_date >= date('now', '-7 days') THEN 1 ELSE 0 END) as week_count,
            SUM(CASE WHEN ht.completion_date >= date('now', '-30 days') THEN 1 ELSE 0 END) as month_count
        FROM habit_tracking ht
        JOIN habits h ON ht.habit_id = h.habit_id
        JOIN users u ON h.user_id = u.user_id
        WHERE u.telegram_id = ?
        """
        cursor.execute(query, (telegram_id,))
        result = cursor.fetchone()

        week_count = result[0] if result and result[0] is not None else 0
        month_count = result[1] if result and result[1] is not None else 0

        return week_count, month_count
