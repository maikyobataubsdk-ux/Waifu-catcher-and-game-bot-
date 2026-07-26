import os
import re
import aiosqlite
import asyncpg
import logging
import contextlib

logger = logging.getLogger(__name__)

# Global postgres pool reference
POSTGRES_POOL = None

def is_postgres_configured() -> bool:
    """
    Checks if PostgreSQL is configured via DATABASE_URL or dedicated env variables.
    """
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
        return True
    if os.environ.get("POSTGRES_USER") or os.environ.get("POSTGRES_DB"):
        return True
    return False

async def get_postgres_pool():
    """
    Retrieves or initializes the asyncpg connection pool.
    """
    global POSTGRES_POOL
    if POSTGRES_POOL is None:
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            POSTGRES_POOL = await asyncpg.create_pool(dsn=db_url)
        else:
            user = os.environ.get("POSTGRES_USER", "postgres")
            password = os.environ.get("POSTGRES_PASSWORD", "")
            database = os.environ.get("POSTGRES_DB", "welora_bot_db")
            host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
            port = os.environ.get("POSTGRES_PORT", "5432")
            POSTGRES_POOL = await asyncpg.create_pool(
                user=user,
                password=password,
                database=database,
                host=host,
                port=port
            )
    return POSTGRES_POOL

def translate_query(query: str, dialect: str) -> str:
    """
    Translates SQLite compatible SQL queries into PostgreSQL dialect where necessary.
    Also maps positional '?' placeholders to '$1, $2, ...' placeholders for PostgreSQL.
    """
    if dialect == "sqlite":
        return query

    # Translate specific INSERT queries
    q_lower = query.strip().lower().replace("\n", " ")
    if "insert or ignore into group_settings" in q_lower:
        return "INSERT INTO group_settings (chat_id) VALUES ($1) ON CONFLICT (chat_id) DO NOTHING"
    if "insert or replace into active_spawns" in q_lower:
        return "INSERT INTO active_spawns (chat_id, waifu_id, spawned_at) VALUES ($1, $2, $3) ON CONFLICT (chat_id) DO UPDATE SET waifu_id = EXCLUDED.waifu_id, spawned_at = EXCLUDED.spawned_at"

    # Translate placeholders
    parts = query.split('?')
    new_query = []
    for i, part in enumerate(parts[:-1]):
        new_query.append(part)
        new_query.append(f"${i+1}")
    new_query.append(parts[-1])
    translated = "".join(new_query)

    # Translate SQLite to PostgreSQL schema types
    translated = re.sub(r'(?i)\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b', 'SERIAL PRIMARY KEY', translated)
    translated = re.sub(r'(?i)\bINTEGER\s+PRIMARY\s+KEY\b', 'BIGINT PRIMARY KEY', translated)

    # Columns representing 64-bit Telegram IDs
    translated = re.sub(r'(?i)\buser_id\s+INTEGER\b', 'user_id BIGINT', translated)
    translated = re.sub(r'(?i)\buser_one_id\s+INTEGER\b', 'user_one_id BIGINT', translated)
    translated = re.sub(r'(?i)\buser_two_id\s+INTEGER\b', 'user_two_id BIGINT', translated)
    translated = re.sub(r'(?i)\bchat_id\s+INTEGER\b', 'chat_id BIGINT', translated)

    return translated

class DBRow(dict):
    """
    A dictionary subclass that also allows accessing columns by index position.
    """
    def __init__(self, keys, values):
        super().__init__(zip(keys, values))
        self._keys = list(keys)
        self._values = list(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

class DBCursorWrapper:
    def __init__(self, cursor_or_rows, dialect):
        self.cursor_or_rows = cursor_or_rows
        self.dialect = dialect
        self._index = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.dialect == "sqlite":
            sqlite_row = await self.cursor_or_rows.__anext__()
            return DBRow(sqlite_row.keys(), tuple(sqlite_row))
        else:
            if self._index < len(self.cursor_or_rows):
                row = self.cursor_or_rows[self._index]
                self._index += 1
                return row
            else:
                raise StopAsyncIteration

    async def fetchone(self):
        if self.dialect == "sqlite":
            sqlite_row = await self.cursor_or_rows.fetchone()
            if sqlite_row is None:
                return None
            return DBRow(sqlite_row.keys(), tuple(sqlite_row))
        else:
            if self._index < len(self.cursor_or_rows):
                row = self.cursor_or_rows[self._index]
                self._index += 1
                return row
            return None

    async def fetchall(self):
        if self.dialect == "sqlite":
            sqlite_rows = await self.cursor_or_rows.fetchall()
            return [DBRow(r.keys(), tuple(r)) for r in sqlite_rows]
        else:
            rows = self.cursor_or_rows[self._index:]
            self._index = len(self.cursor_or_rows)
            return rows

class DBExecuteContextManager:
    def __init__(self, conn_wrapper, query, params):
        self.conn_wrapper = conn_wrapper
        self.query = query
        self.params = params
        self._cursor = None

    def __await__(self):
        return self._execute().__await__()

    async def _execute(self):
        if self._cursor is None:
            self._cursor = await self.conn_wrapper._real_execute(self.query, self.params)
        return self._cursor

    async def __aenter__(self):
        return await self._execute()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class DBConnectionWrapper:
    def __init__(self, conn, dialect):
        self.conn = conn
        self.dialect = dialect

    def execute(self, query: str, params=None):
        return DBExecuteContextManager(self, query, params)

    async def _real_execute(self, query: str, params=None):
        translated = translate_query(query, self.dialect)
        if self.dialect == "sqlite":
            cursor = await self.conn.execute(translated, params or ())
            return DBCursorWrapper(cursor, self.dialect)
        else:
            q_strip = translated.strip().lower()
            if q_strip.startswith("select") or "returning" in q_strip:
                records = await self.conn.fetch(translated, *(params or ()))
                rows = [DBRow(r.keys(), r.values()) for r in records]
                return DBCursorWrapper(rows, self.dialect)
            else:
                await self.conn.execute(translated, *(params or ()))
                return DBCursorWrapper([], self.dialect)

    async def executemany(self, query: str, params_list):
        translated = translate_query(query, self.dialect)
        if self.dialect == "sqlite":
            await self.conn.executemany(translated, params_list)
        else:
            await self.conn.executemany(translated, params_list)

    async def commit(self):
        if self.dialect == "sqlite":
            await self.conn.commit()

    async def rollback(self):
        if self.dialect == "sqlite":
            await self.conn.rollback()

@contextlib.asynccontextmanager
async def get_db():
    if is_postgres_configured():
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            wrapper = DBConnectionWrapper(conn, "postgres")
            async with conn.transaction():
                try:
                    yield wrapper
                except Exception:
                    raise
    else:
        db_file = os.environ.get("DATABASE_PATH", "bot_database.db")
        db = await aiosqlite.connect(db_file)
        db.row_factory = aiosqlite.Row
        wrapper = DBConnectionWrapper(db, "sqlite")
        try:
            yield wrapper
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
        await db.execute("""
            UPDATE users SET
                coins = CASE WHEN coins + ? < 0 THEN 0 ELSE coins + ? END,
                gems = CASE WHEN gems + ? < 0 THEN 0 ELSE gems + ? END,
                xp = CASE WHEN xp + ? < 0 THEN 0 ELSE xp + ? END
            WHERE id = ?
        """, (coins_delta, coins_delta, gems_delta, gems_delta, xp_delta, xp_delta, user_id))
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
            message.command = [command_part] + parts[1:]
            return True
        return False

    return filters.create(prefix_filter, commands=commands)
