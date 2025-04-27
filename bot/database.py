import aiosqlite

DB_PATH = "data.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")

        await db.commit()

async def add_user(telegram_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        await db.commit()

async def get_user_id(telegram_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else None

async def add_note(telegram_id: int, text: str):
    user_id = await get_user_id(telegram_id)
    if user_id:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO notes (user_id, text) VALUES (?, ?)",
                (user_id, text)
            )
            await db.commit()

async def add_reminder(telegram_id: int, text: str):
    user_id = await get_user_id(telegram_id)
    if user_id:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO reminders (user_id, text) VALUES (?, ?)",
                (user_id, text)
            )
            await db.commit()

async def get_notes(telegram_id: int):
    user_id = await get_user_id(telegram_id)
    if user_id:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, text FROM notes WHERE user_id = ?", (user_id,)
            )
            return await cursor.fetchall()
    return []

async def get_reminders(telegram_id: int):
    user_id = await get_user_id(telegram_id)
    if user_id:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, text FROM reminders WHERE user_id = ?", (user_id,)
            )
            return await cursor.fetchall()
    return []

async def delete_note(note_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await db.commit()

async def delete_reminder(reminder_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        await db.commit()
