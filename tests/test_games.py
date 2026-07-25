import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from database import init_db, create_or_get_user, get_db
from modules.games import rocket_command, scrabble_command

class MockUser:
    def __init__(self, id, username, first_name):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.is_bot = False

class MockMessage:
    def __init__(self, text, user_id, username, first_name):
        self.text = text
        self.command = text.split()
        self.from_user = MockUser(user_id, username, first_name)
        self.chat = MagicMock()
        self.chat.id = 66666
        self.reply_text = AsyncMock()

@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "test_bot_games.db")
    await init_db()
    yield
    if os.path.exists("test_bot_games.db"):
        os.remove("test_bot_games.db")

@pytest.mark.asyncio
async def test_rocket_command_success_or_loss():
    message = MockMessage("/rocket 100 2.0", 501, "rocket_man", "Rocketman")
    client = MagicMock()
    await rocket_command(client, message)

    # Message should be replied to indicating outcome
    assert message.reply_text.called
    response = message.reply_text.call_args[0][0]
    assert "ROCKET TO THE MOON!" in response or "BOOM! CRASHED!" in response

@pytest.mark.asyncio
async def test_scrabble_command():
    message = MockMessage("/scrabble", 502, "word_man", "Wordman")
    client = MagicMock()
    await scrabble_command(client, message)

    assert "SCRABBLE MINI-GAME TRIGGERED!" in message.reply_text.call_args[0][0]
