"""
Task Engine — CRUD operations for tasks stored in SQLite.
"""

import logging
from typing import Optional, List
import aiosqlite
from models.database import DB_PATH

logger = logging.getLogger(__name__)


async def create_task(user_id: int, title: str, due_date: Optional[str] = None) -> dict:
    """Insert a new task into the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "INSERT INTO tasks (user_id, title, due_date) VALUES (?, ?, ?)",
            (user_id, title.strip(), due_date),
        )
        await db.commit()
        task_id = cursor.lastrowid
        row = await (await db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        )).fetchone()
        logger.info(f"Task created: id={task_id}, title='{title}'")
        return dict(row)


async def list_tasks(user_id: int, status: Optional[str] = None) -> List[dict]:
    """Fetch one user's tasks, optionally filtered by status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            rows = await (await db.execute(
                """
                SELECT * FROM tasks
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
                """,
                (user_id, status),
            )).fetchall()
        else:
            rows = await (await db.execute(
                "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )).fetchall()
        return [dict(r) for r in rows]


async def delete_task_by_title(user_id: int, title: str) -> bool:
    """Delete the first task matching the given title (case-insensitive)."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Find task with fuzzy title match
        row = await (await db.execute(
            """
            SELECT id FROM tasks
            WHERE user_id = ? AND LOWER(title) LIKE LOWER(?)
            LIMIT 1
            """,
            (user_id, f"%{title}%"),
        )).fetchone()
        
        if not row:
            logger.warning(f"No task found matching: '{title}'")
            return False
        
        await db.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (row[0], user_id))
        await db.commit()
        logger.info(f"Task deleted: id={row[0]}, title match='{title}'")
        return True


async def delete_task_by_id(user_id: int, task_id: int) -> bool:
    """Delete a task by its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        result = await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        await db.commit()
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Task deleted: id={task_id}")
        return deleted


async def update_task_status(user_id: int, task_id: int, status: str) -> Optional[dict]:
    """Update a task's status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """
            UPDATE tasks
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (status, task_id, user_id),
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )).fetchone()
        return dict(row) if row else None


async def log_conversation(user_id: int, user_text: str, intent: str, ai_response: str):
    """Log a conversation turn for debugging/history."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO conversation_log (user_id, user_text, intent, ai_response)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, user_text, intent, ai_response),
        )
        await db.commit()
