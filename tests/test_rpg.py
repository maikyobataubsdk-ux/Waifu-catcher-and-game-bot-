import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from database import init_db, create_or_get_user, get_db
from modules.rpg import rob_command, kill_command, protect_command

class MockUser:
    def __init__(self, id, username, first_name):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.is_bot = False

class MockMessage:
    def __init__(self, text, user_id, username, first_name, reply_to=None):
        self.text = text
        self.command = text.split()
        self.from_user = MockUser(user_id, username, first_name)
        self.chat = MagicMock()
        self.chat.id = 77777
        self.reply_to_message = reply_to
        self.reply_text = AsyncMock()

@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "test_bot_rpg.db")
    await init_db()
    yield
    if os.path.exists("test_bot_rpg.db"):
        os.remove("test_bot_rpg.db")

@pytest.mark.asyncio
async def test_protect_command():
    # Setup user and give them sufficient coins (need at least 1500 for a 1-day shield)
    from database import update_user_balance
    await create_or_get_user(401, "shield_user", "Shieldy")
    await update_user_balance(401, coins_delta=1000) # 1000 + 1000 = 2000

    message = MockMessage("/protect 1", 401, "shield_user", "Shieldy")
    client = MagicMock()
    await protect_command(client, message)

    assert "SHIELD ACTIVATED!" in message.reply_text.call_args[0][0]

    # Verify user has shield in DB
    user = await create_or_get_user(401)
    assert user["is_protected_until"] > 0
    assert user["coins"] == 500  # 2000 - 1500 = 500

@pytest.mark.asyncio
async def test_rob_fails_on_shield():
    # Setup protected user
    await create_or_get_user(402, "protected_target", "Protected Target")
    async with get_db() as db:
        await db.execute("UPDATE users SET is_protected_until = 9999999999 WHERE id = 402")
        await db.commit()

    reply_msg = MockMessage("/dummy", 402, "protected_target", "Protected Target")
    rob_msg = MockMessage("/rob", 403, "robber", "Robber", reply_to=reply_msg)

    client = MagicMock()
    await rob_command(client, rob_msg)
    assert "has an active protection shield!" in rob_msg.reply_text.call_args[0][0]
