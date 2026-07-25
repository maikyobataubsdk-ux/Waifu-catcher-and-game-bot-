import os
import aiosqlite
import logging
import contextlib

logger = logging.getLogger(__name__)

@contextlib.asynccontextmanager
async def get_db():
    db_file = os.environ.get("DATABASE_PATH", "bot_database.db")
    db = await aiosqlite.connect(db_file)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    async with get_db() as db:
        # Create tables
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            coins INTEGER DEFAULT 1000,
            gems INTEGER DEFAULT 10,
            xp INTEGER DEFAULT 0,
            daily_streak INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            kill_count INTEGER DEFAULT 0,
            is_protected_until INTEGER DEFAULT 0,
            is_dead_until INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS waifus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            rarity TEXT,
            price INTEGER,
            image_path TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_harems (
            user_id INTEGER,
            waifu_id INTEGER,
            married_at INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, waifu_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (waifu_id) REFERENCES waifus (id) ON DELETE CASCADE
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_marriages (
            user_one_id INTEGER,
            user_two_id INTEGER,
            married_at INTEGER,
            PRIMARY KEY (user_one_id, user_two_id),
            FOREIGN KEY (user_one_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (user_two_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS group_settings (
            chat_id INTEGER PRIMARY KEY,
            custom_prefix TEXT DEFAULT '/',
            toxicity_filter INTEGER DEFAULT 0,
            nsfw_filter INTEGER DEFAULT 0,
            welcome_msg TEXT DEFAULT 'Welcome {name} to our group!'
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS active_spawns (
            chat_id INTEGER PRIMARY KEY,
            waifu_id INTEGER,
            spawned_at INTEGER,
            FOREIGN KEY (waifu_id) REFERENCES waifus (id) ON DELETE CASCADE
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS message_counters (
            chat_id INTEGER PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
        """)

        await db.commit()

        # Pre-populate waifus if empty
        async with db.execute("SELECT COUNT(*) as cnt FROM waifus") as cursor:
            row = await cursor.fetchone()
            if row["cnt"] == 0:
                default_waifus = [
                    ("Zero Two", "Legendary", 5000, "zero_two.jpg"),
                    ("Rem", "Epic", 3000, "rem.jpg"),
                    ("Megumin", "Rare", 1500, "megumin.jpg"),
                    ("Asuka Langley", "Legendary", 5500, "asuka.jpg"),
                    ("Velora The Ancient", "Velora", 15000, "velora.jpg"),
                    ("Mikasa Ackerman", "Epic", 3500, "mikasa.jpg"),
                    ("Nezuko Kamado", "Rare", 2000, "nezuko.jpg"),
                    ("Saber", "Legendary", 6000, "saber.jpg"),
                    ("Hinata Hyuga", "Common", 800, "hinata.jpg"),
                    ("Sakura Haruno", "Common", 500, "sakura.jpg"),
                    ("Esdeath", "Velora", 12000, "esdeath.jpg"),
                    ("Chika Fujiwara", "Rare", 1800, "chika.jpg"),
                ]
                await db.executemany(
                    "INSERT INTO waifus (name, rarity, price, image_path) VALUES (?, ?, ?, ?)",
                    default_waifus
                )
                await db.commit()
                logger.info("Pre-populated waifus table.")

# Helper database operations
async def get_user(user_id: int):
    async with get_db() as db:
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def create_or_get_user(user_id: int, username: str = None, first_name: str = None):
    async with get_db() as db:
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if user:
                # Update username or first_name if changed
                if username or first_name:
                    await db.execute(
                        "UPDATE users SET username = COALESCE(?, username), first_name = COALESCE(?, first_name) WHERE id = ?",
                        (username, first_name, user_id)
                    )
                    await db.commit()
                async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur2:
                    return await cur2.fetchone()

            # Insert new user
            await db.execute(
                "INSERT INTO users (id, username, first_name, coins, gems, xp) VALUES (?, ?, ?, 1000, 10, 0)",
                (user_id, username, first_name)
            )
            await db.commit()
            async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur2:
                return await cur2.fetchone()

async def update_user_balance(user_id: int, coins_delta: int = 0, gems_delta: int = 0, xp_delta: int = 0):
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET coins = MAX(0, coins + ?), gems = MAX(0, gems + ?), xp = MAX(0, xp + ?) WHERE id = ?",
            (coins_delta, gems_delta, xp_delta, user_id)
        )
        await db.commit()

async def get_global_rank(user_id: int):
    async with get_db() as db:
        async with db.execute("""
            SELECT id, (SELECT COUNT(*) FROM users u2 WHERE u2.coins > u1.coins) + 1 AS rank
            FROM users u1 WHERE id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row["rank"] if row else 9999

async def get_top_richest(limit: int = 5):
    async with get_db() as db:
        async with db.execute("SELECT * FROM users ORDER BY coins DESC LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()

async def get_group_settings(chat_id: int):
    async with get_db() as db:
        async with db.execute("SELECT * FROM group_settings WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row
            await db.execute("INSERT OR IGNORE INTO group_settings (chat_id) VALUES (?)", (chat_id,))
            await db.commit()
            async with db.execute("SELECT * FROM group_settings WHERE chat_id = ?", (chat_id,)) as cur2:
                return await cur2.fetchone()

async def update_group_settings(chat_id: int, custom_prefix: str = None, toxicity_filter: int = None, nsfw_filter: int = None, welcome_msg: str = None):
    async with get_db() as db:
        await get_group_settings(chat_id)  # Ensure exists
        await db.execute("""
            UPDATE group_settings SET
                custom_prefix = COALESCE(?, custom_prefix),
                toxicity_filter = COALESCE(?, toxicity_filter),
                nsfw_filter = COALESCE(?, nsfw_filter),
                welcome_msg = COALESCE(?, welcome_msg)
            WHERE chat_id = ?
        """, (custom_prefix, toxicity_filter, nsfw_filter, welcome_msg, chat_id))
        await db.commit()

# Dynamic prefix command filter
from pyrogram import filters
from pyrogram.enums import ChatType

def dynamic_command(commands):
    if isinstance(commands, str):
        commands = [commands]
    commands = [cmd.lower() for cmd in commands]

    async def prefix_filter(flt, client, message):
        if not message.text:
            return False

        chat_id = message.chat.id
        # Fetch prefix dynamically from DB or default to '/'
        chat_type = getattr(message.chat.type, 'value', message.chat.type) if message.chat else None
        if chat_type and str(chat_type).lower() in ["group", "supergroup"]:
            settings = await get_group_settings(chat_id)
            prefix = settings["custom_prefix"] if settings else "/"
        else:
            prefix = "/"

        text = message.text.strip()
        if not text.startswith(prefix):
            return False

        parts = text[len(prefix):].split()
        if not parts:
            return False

        command_part = parts[0].split("@")[0].lower()
        if command_part in flt.commands:
            # Set the parsed command for ease of use in handler
            message.command = [command_part] + parts[1:]
            return True
        return False

    return filters.create(prefix_filter, commands=commands)
