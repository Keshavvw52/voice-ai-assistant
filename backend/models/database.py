"""
Database models and initialization using aiosqlite.
"""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite
from models.user import create_user_table

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BACKEND_DIR / "voice_assistant.db"


async def ensure_column(db, table_name: str, column_name: str, definition: str):
    cursor = await db.execute(f"PRAGMA table_info({table_name})")
    columns = await cursor.fetchall()
    existing_names = {column[1] for column in columns}
    if column_name not in existing_names:
        await db.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


async def init_db():
    """Create application tables if they do not exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await create_user_table(db)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                title TEXT NOT NULL,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                user_text TEXT,
                intent TEXT,
                ai_response TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await ensure_column(db, "tasks", "user_id", "INTEGER REFERENCES users(id)")
        await ensure_column(
            db,
            "conversation_log",
            "user_id",
            "INTEGER REFERENCES users(id)",
        )
        await db.commit()
        logger.info("Database tables ready at %s", DB_PATH)


async def get_db():
    """Yield an async database connection for FastAPI dependencies."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
