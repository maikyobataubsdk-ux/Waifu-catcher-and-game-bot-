import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from database import init_db, create_or_get_user, get_db
from modules.economy import bal_command, daily_command, pay_or_gift_command

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
        self.chat.id = 99999
        self.reply_to_message = reply_to
        self.reply_text = AsyncMock()

@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "test_bot_economy.db")
    await init_db()
    yield
    if os.path.exists("test_bot_economy.db"):
        os.remove("test_bot_economy.db")

@pytest.mark.asyncio
async def test_daily_command():
    message = MockMessage("/daily", 101, "bob", "Bob")
    client = MagicMock()

    # First daily claim
    await daily_command(client, message)
    message.reply_text.assert_called_once()
    assert "DAILY REWARD CLAIMED!" in message.reply_text.call_args[0][0]

    # Second daily claim (should trigger cooldown)
    message.reply_text.reset_mock()
    await daily_command(client, message)
    assert "Daily Reward Cooldown!" in message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_pay_command():
    # Setup users
    await create_or_get_user(201, "sender", "Sender")
    await create_or_get_user(202, "recipient", "Recipient")

    reply_msg = MockMessage("/dummy", 202, "recipient", "Recipient")
    pay_msg = MockMessage("/pay 500", 201, "sender", "Sender", reply_to=reply_msg)

    client = MagicMock()
    await pay_or_gift_command(client, pay_msg)

    # Check balance transition
    async with get_db() as db:
        async with db.execute("SELECT coins FROM users WHERE id = ?", (201,)) as cursor:
            sender_coins = (await cursor.fetchone())["coins"]
        async with db.execute("SELECT coins FROM users WHERE id = ?", (202,)) as cursor:
            recipient_coins = (await cursor.fetchone())["coins"]

    assert sender_coins == 500  # 1000 - 500
    assert recipient_coins == 1500  # 1000 + 500
    assert "Transaction Complete!" in pay_msg.reply_text.call_args[0][0]
