"""
Task Engine — CRUD operations for tasks stored in SQLite.
"""

import logging
from typing import Optional, List
import aiosqlite
from models.database import DB_PATH

logger = logging.getLogger(__name__)


async def create_task(title: str, due_date: Optional[str] = None) -> dict:
    """Insert a new task into the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            (title.strip(), due_date),
        )
        await db.commit()
        task_id = cursor.lastrowid
        row = await (await db.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        )).fetchone()
        logger.info(f"Task created: id={task_id}, title='{title}'")
        return dict(row)


async def list_tasks(status: Optional[str] = None) -> List[dict]:
    """Fetch all tasks, optionally filtered by status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            rows = await (await db.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC", (status,)
            )).fetchall()
        else:
            rows = await (await db.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC"
            )).fetchall()
        return [dict(r) for r in rows]


async def delete_task_by_title(title: str) -> bool:
    """Delete the first task matching the given title (case-insensitive)."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Find task with fuzzy title match
        row = await (await db.execute(
            "SELECT id FROM tasks WHERE LOWER(title) LIKE LOWER(?) LIMIT 1",
            (f"%{title}%",),
        )).fetchone()
        
        if not row:
            logger.warning(f"No task found matching: '{title}'")
            return False
        
        await db.execute("DELETE FROM tasks WHERE id = ?", (row[0],))
        await db.commit()
        logger.info(f"Task deleted: id={row[0]}, title match='{title}'")
        return True


async def delete_task_by_id(task_id: int) -> bool:
    """Delete a task by its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        result = await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Task deleted: id={task_id}")
        return deleted


async def update_task_status(task_id: int, status: str) -> Optional[dict]:
    """Update a task's status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, task_id),
        )
        await db.commit()
        row = await (await db.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        )).fetchone()
        return dict(row) if row else None


async def log_conversation(user_text: str, intent: str, ai_response: str):
    """Log a conversation turn for debugging/history."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO conversation_log (user_text, intent, ai_response) VALUES (?, ?, ?)",
            (user_text, intent, ai_response),
        )
        await db.commit()