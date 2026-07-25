import os
import time
import logging
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Redis client configuration
_redis_client = None
_redis_checked = False

def is_redis_configured() -> bool:
    """
    Checks if Redis URL or host is set.
    """
    return bool(os.environ.get("REDIS_URL") or os.environ.get("REDIS_HOST") or os.environ.get("REDIS_PORT"))

async def get_redis_client():
    """
    Initializes and returns the async Redis client.
    Returns None if Redis is not configured or fails to connect.
    """
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client

    _redis_checked = True
    if not is_redis_configured():
        logger.info("Redis is not configured. Falling back to in-memory caching.")
        return None

    try:
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            _redis_client = aioredis.from_url(redis_url, decode_responses=True)
        else:
            host = os.environ.get("REDIS_HOST", "localhost")
            port = int(os.environ.get("REDIS_PORT", "6379"))
            _redis_client = aioredis.Redis(host=host, port=port, decode_responses=True)

        # Test connection
        await _redis_client.ping()
        logger.info("Successfully connected to Redis server.")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory caching.")
        _redis_client = None

    return _redis_client

# In-memory storage structures for fallback mode
IN_MEMORY_COUNTERS = {}
IN_MEMORY_SPAWNS = {}
IN_MEMORY_COOLDOWNS = {}
IN_MEMORY_SCRABBLES = {}

# Message Counters Caching API
async def incr_message_counter(chat_id: int) -> int:
    """
    Increments the message counter for a chat. Returns the new count.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"msg_count:{chat_id}"
            count = await client.incr(key)
            return int(count)
        except Exception as e:
            logger.error(f"Redis incr_message_counter error: {e}")

    # Fallback to in-memory
    current = IN_MEMORY_COUNTERS.get(chat_id, 0)
    new_count = current + 1
    IN_MEMORY_COUNTERS[chat_id] = new_count
    return new_count

async def get_message_counter(chat_id: int) -> int:
    """
    Retrieves the current message counter for a chat.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"msg_count:{chat_id}"
            val = await client.get(key)
            return int(val) if val else 0
        except Exception as e:
            logger.error(f"Redis get_message_counter error: {e}")

    return IN_MEMORY_COUNTERS.get(chat_id, 0)

async def reset_message_counter(chat_id: int):
    """
    Resets the message counter for a chat.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"msg_count:{chat_id}"
            await client.set(key, 0)
            return
        except Exception as e:
            logger.error(f"Redis reset_message_counter error: {e}")

    IN_MEMORY_COUNTERS[chat_id] = 0

# Active Spawns Caching API
async def set_active_spawn(chat_id: int, waifu_id: int, name: str, rarity: str, price: int):
    """
    Stores an active character spawn. TTL of 1 hour to prevent stale spawns.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"active_spawn:{chat_id}"
            data = {
                "waifu_id": str(waifu_id),
                "name": name,
                "rarity": rarity,
                "price": str(price),
                "spawned_at": str(int(time.time()))
            }
            await client.hset(key, mapping=data)
            await client.expire(key, 3600)  # Expires in 1 hour
            return
        except Exception as e:
            logger.error(f"Redis set_active_spawn error: {e}")

    # Fallback to in-memory
    IN_MEMORY_SPAWNS[chat_id] = {
        "waifu_id": waifu_id,
        "name": name,
        "rarity": rarity,
        "price": price,
        "spawned_at": int(time.time())
    }

async def get_active_spawn(chat_id: int) -> dict | None:
    """
    Retrieves the active character spawn for a chat.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"active_spawn:{chat_id}"
            data = await client.hgetall(key)
            if data:
                return {
                    "waifu_id": int(data["waifu_id"]),
                    "name": data["name"],
                    "rarity": data["rarity"],
                    "price": int(data["price"]),
                    "spawned_at": int(data["spawned_at"])
                }
            return None
        except Exception as e:
            logger.error(f"Redis get_active_spawn error: {e}")

    # Fallback to in-memory
    spawn = IN_MEMORY_SPAWNS.get(chat_id)
    if spawn:
        # Check TTL of 1 hour manually
        if int(time.time()) - spawn["spawned_at"] > 3600:
            del IN_MEMORY_SPAWNS[chat_id]
            return None
        return spawn
    return None

async def delete_active_spawn(chat_id: int):
    """
    Deletes the active character spawn for a chat.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"active_spawn:{chat_id}"
            await client.delete(key)
            return
        except Exception as e:
            logger.error(f"Redis delete_active_spawn error: {e}")

    if chat_id in IN_MEMORY_SPAWNS:
        del IN_MEMORY_SPAWNS[chat_id]

# RPG Cooldowns Caching API
async def set_cooldown(user_id: int, action: str, duration_seconds: int):
    """
    Sets a cooldown for a specific user action (e.g. 'rob', 'kill').
    """
    expires_at = int(time.time()) + duration_seconds
    client = await get_redis_client()
    if client:
        try:
            key = f"cooldown:{action}:{user_id}"
            await client.set(key, expires_at, ex=duration_seconds)
            return
        except Exception as e:
            logger.error(f"Redis set_cooldown error: {e}")

    # Fallback to in-memory
    if user_id not in IN_MEMORY_COOLDOWNS:
        IN_MEMORY_COOLDOWNS[user_id] = {}
    IN_MEMORY_COOLDOWNS[user_id][action] = expires_at

async def get_cooldown_expiry(user_id: int, action: str) -> int:
    """
    Returns the absolute expiration timestamp (int) of a cooldown, or 0 if expired/not set.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"cooldown:{action}:{user_id}"
            val = await client.get(key)
            return int(val) if val else 0
        except Exception as e:
            logger.error(f"Redis get_cooldown_expiry error: {e}")

    # Fallback to in-memory
    user_data = IN_MEMORY_COOLDOWNS.get(user_id, {})
    expires_at = user_data.get(action, 0)
    if expires_at < int(time.time()):
        return 0
    return expires_at

# Scrabble Words Caching API
async def set_scrabble_word(chat_id: int, word: str):
    """
    Sets the active scrabble word for a chat. Expires in 15 minutes.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"scrabble:{chat_id}"
            await client.set(key, word, ex=900)  # 15 minutes TTL
            return
        except Exception as e:
            logger.error(f"Redis set_scrabble_word error: {e}")

    IN_MEMORY_SCRABBLES[chat_id] = word

async def get_scrabble_word(chat_id: int) -> str | None:
    """
    Gets the active scrabble word for a chat.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"scrabble:{chat_id}"
            return await client.get(key)
        except Exception as e:
            logger.error(f"Redis get_scrabble_word error: {e}")

    return IN_MEMORY_SCRABBLES.get(chat_id)

async def delete_scrabble_word(chat_id: int):
    """
    Deletes the active scrabble word for a chat.
    """
    client = await get_redis_client()
    if client:
        try:
            key = f"scrabble:{chat_id}"
            await client.delete(key)
            return
        except Exception as e:
            logger.error(f"Redis delete_scrabble_word error: {e}")

    if chat_id in IN_MEMORY_SCRABBLES:
        del IN_MEMORY_SCRABBLES[chat_id]
