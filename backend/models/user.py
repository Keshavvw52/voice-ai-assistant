import aiosqlite

DB_PATH = "voice_ai.db"

async def create_user_table():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
        """)
        await db.commit()