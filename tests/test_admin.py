import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from database import init_db, create_or_get_user, get_db, get_group_settings
from modules.admin import setgroup_command, is_eligible_admin

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
        self.chat.id = 55555
        self.reply_text = AsyncMock()

@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "test_bot_admin.db")
    await init_db()
    yield
    if os.path.exists("test_bot_admin.db"):
        os.remove("test_bot_admin.db")

@pytest.mark.asyncio
async def test_setgroup_command_denied():
    # User 501 is not a bot admin and not richest top 5 (since db empty)
    message = MockMessage("/setgroup prefix !", 501, "peasant", "Peasant")
    client = MagicMock()
    await setgroup_command(client, message)

    assert "Permission Denied!" in message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_setgroup_command_success_as_bot_admin():
    # User 7777777 is configured as a static bot admin in admin.py
    message = MockMessage("/setgroup prefix !", 7777777, "admin_user", "Admin")
    client = MagicMock()
    await setgroup_command(client, message)

    assert "Custom prefix updated to:" in message.reply_text.call_args[0][0]

    # Verify group settings are updated in DB
    settings = await get_group_settings(55555)
    assert settings["custom_prefix"] == "!"

@pytest.mark.asyncio
async def test_dynamic_prefix_routing():
    from database import dynamic_command
    from pyrogram.types import Message as PyMessage

    # Setup custom prefix as '!'
    from database import update_group_settings
    await update_group_settings(55555, custom_prefix="!")

    # Test dynamic command filter matches correctly
    client = MagicMock()

    # Message starting with original prefix '/' should fail
    message_slash = MagicMock()
    message_slash.text = "/setgroup option"
    message_slash.chat.id = 55555
    message_slash.chat.type = "group"

    flt = dynamic_command("setgroup")
    match_slash = await flt(client, message_slash)
    assert match_slash is False

    # Message starting with '!' should match
    message_excl = MagicMock()
    message_excl.text = "!setgroup option"
    message_excl.chat.id = 55555
    message_excl.chat.type = "group"

    match_excl = await flt(client, message_excl)
    assert match_excl is True
    assert message_excl.command == ["setgroup", "option"]

@pytest.mark.asyncio
async def test_group_moderation_filters():
    from modules.admin import group_moderation_handler
    from database import update_group_settings

    # Enable toxicity and nsfw filters
    await update_group_settings(55555, toxicity_filter=1, nsfw_filter=1)

    client = MagicMock()
    client.send_message = AsyncMock()

    # 1. Toxic word test
    msg_toxic = MagicMock()
    msg_toxic.text = "You are an idiot"
    msg_toxic.chat.id = 55555
    msg_toxic.chat.type = "group"
    msg_toxic.from_user.first_name = "Sender"
    msg_toxic.delete = AsyncMock()

    await group_moderation_handler(client, msg_toxic)
    msg_toxic.delete.assert_called_once()
    assert client.send_message.called

    # 2. NSFW word test
    client.send_message.reset_mock()
    msg_nsfw = MagicMock()
    msg_nsfw.text = "Adult xxx content"
    msg_nsfw.chat.id = 55555
    msg_nsfw.chat.type = "group"
    msg_nsfw.from_user.first_name = "Sender"
    msg_nsfw.delete = AsyncMock()

    await group_moderation_handler(client, msg_nsfw)
    msg_nsfw.delete.assert_called_once()
    assert client.send_message.called
