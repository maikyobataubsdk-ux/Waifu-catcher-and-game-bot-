import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from database import init_db, create_or_get_user, get_db
from modules.waifu import grasp_command, explore_command, marry_command, propose_command, propose_callback

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
        self.chat.id = 88888
        self.reply_to_message = reply_to
        self.reply_text = AsyncMock()

@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "test_bot_waifu.db")
    await init_db()
    yield
    if os.path.exists("test_bot_waifu.db"):
        os.remove("test_bot_waifu.db")

@pytest.mark.asyncio
async def test_grasp_command_with_no_spawn():
    message = MockMessage("/grasp", 301, "charlie", "Charlie")
    client = MagicMock()
    await grasp_command(client, message)
    message.reply_text.assert_called_once_with("❌ There is no active character to claim in this group!")

@pytest.mark.asyncio
async def test_grasp_command_with_active_spawn():
    # Setup active spawn manually
    async with get_db() as db:
        await db.execute("INSERT INTO active_spawns (chat_id, waifu_id, spawned_at) VALUES (88888, 1, 123456)")
        await db.commit()

    message = MockMessage("/grasp", 301, "charlie", "Charlie")
    client = MagicMock()
    await grasp_command(client, message)

    # Assert successful claim
    assert "You have successfully claimed" in message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_explore_command():
    message = MockMessage("/explore", 302, "explorer", "Explorer")
    client = MagicMock()
    # Execute multiple times to ensure we cover either hit or miss path
    for _ in range(5):
        await explore_command(client, message)

    assert message.reply_text.called
