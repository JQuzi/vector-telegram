# db/repositories/goals_repo.py
from datetime import datetime

from db.connection import get_conn


def save_goal(telegram_id: int, name: str, description: str):
    """Сохраняет новую цель со статусом 'new'."""
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        if not result:
            return

        user_internal_id = result[0]
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO goals (user_id, name, description, status, creation_date) VALUES (?, ?, ?, ?, ?)",
            (user_internal_id, name, description, "new", creation_date),
        )
        conn.commit()


def get_goals_by_status(telegram_id: int, status: str):
    with get_conn() as conn:
        cursor = conn.cursor()
        query = """
        SELECT g.goal_id, g.name
        FROM goals g JOIN users u ON g.user_id = u.user_id
        WHERE u.telegram_id = ? AND g.status = ?
        """
        cursor.execute(query, (telegram_id, status))
        return cursor.fetchall()


def get_goals_counts(telegram_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        query = """
        SELECT status, COUNT(*) FROM goals g JOIN users u ON g.user_id = u.user_id
        WHERE u.telegram_id = ? GROUP BY status
        """
        cursor.execute(query, (telegram_id,))
        return {status: count for status, count in cursor.fetchall()}


def get_goal_details(goal_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, status FROM goals WHERE goal_id = ?", (goal_id,))
        return cursor.fetchone()


def update_goal_status(goal_id: int, new_status: str):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE goals SET status = ? WHERE goal_id = ?", (new_status, goal_id))
        conn.commit()


def delete_goal(goal_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))
        conn.commit()
