import io
from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated
from database import (
    get_db, create_or_get_user, get_top_richest, get_group_settings, update_group_settings, dynamic_command
)
from utils.images import generate_welcome_card

# Set bot administrators list (mocked ID or loaded dynamically)
BOT_ADMIN_IDS = [7777777, 9999999]

async def is_eligible_admin(user_id: int) -> bool:
    """
    Returns True if user is a bot admin or ranks in the global Top 5 richest users.
    """
    if user_id in BOT_ADMIN_IDS:
        return True

    top_richest = await get_top_richest(5)
    richest_ids = [row["id"] for row in top_richest]
    if user_id in richest_ids:
        return True

    return False

# Toxic and NSFW lists
TOXIC_WORDS = ["toxic", "abuse", "badword", "idiot"]
NSFW_WORDS = ["nsfw", "porn", "xxx", "adult"]

@Client.on_message(filters.group & ~filters.service & ~filters.bot, group=-1)
async def group_moderation_handler(client: Client, message: Message):
    """
    Moderation handler to inspect and delete toxic/NSFW messages.
    """
    if not message.text:
        return

    chat_id = message.chat.id
    settings = await get_group_settings(chat_id)
    if not settings:
        return

    text = message.text.lower()

    # Toxicity filtering
    if settings["toxicity_filter"] == 1:
        if any(word in text for word in TOXIC_WORDS):
            try:
                await message.delete()
                await client.send_message(chat_id, f"⚠️ **Toxicity Filter:** Message from {message.from_user.first_name or 'User'} deleted.")
                return
            except Exception:
                pass

    # NSFW filtering
    if settings["nsfw_filter"] == 1:
        if any(word in text for word in NSFW_WORDS):
            try:
                await message.delete()
                await client.send_message(chat_id, f"⚠️ **NSFW Filter:** Message from {message.from_user.first_name or 'User'} deleted.")
                return
            except Exception:
                pass

@Client.on_message(dynamic_command("setgroup"))
async def setgroup_command(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check permissions
    if not await is_eligible_admin(user_id):
        await message.reply_text("❌ Permission Denied! This command can only be used by Bot Admins or the Top 5 Global Richest users.")
        return

    # Usage: /setgroup <setting> <value>
    # e.g., /setgroup prefix !
    # e.g., /setgroup toxicity 1
    # e.g., /setgroup nsfw 0
    # e.g., /setgroup welcome Welcome to our guild, {name}!
    if len(message.command) < 3:
        await message.reply_text(
            "⚙️ **Group Management Controls** ⚙️\n\n"
            "Usage: `/setgroup <setting> <value>`\n\n"
            "**Available Settings:**\n"
            "• `prefix <char>` - Change custom prefix (default: `/`)\n"
            "• `toxicity <0/1>` - Toggle toxic filter\n"
            "• `nsfw <0/1>` - Toggle NSFW/adult contents filter\n"
            "• `welcome <text>` - Set custom group welcome message (use `{name}` placeholder)"
        )
        return

    setting = message.command[1].lower()
    value = " ".join(message.command[2:]).strip()

    if setting == "prefix":
        await update_group_settings(chat_id, custom_prefix=value)
        await message.reply_text(f"✅ Custom prefix updated to: `{value}`")

    elif setting == "toxicity":
        if value not in ["0", "1"]:
            await message.reply_text("❌ Toxicity setting must be 0 (off) or 1 (on)!")
            return
        await update_group_settings(chat_id, toxicity_filter=int(value))
        status = "ENABLED" if value == "1" else "DISABLED"
        await message.reply_text(f"✅ Toxicity filter is now **{status}**.")

    elif setting == "nsfw":
        if value not in ["0", "1"]:
            await message.reply_text("❌ NSFW setting must be 0 (off) or 1 (on)!")
            return
        await update_group_settings(chat_id, nsfw_filter=int(value))
        status = "ENABLED" if value == "1" else "DISABLED"
        await message.reply_text(f"✅ NSFW filter is now **{status}**.")

    elif setting == "welcome":
        await update_group_settings(chat_id, welcome_msg=value)
        await message.reply_text(f"✅ Custom group welcome message set to:\n`{value}`")

    else:
        await message.reply_text("❌ Invalid setting! Use `/setgroup` to see options.")

# Handler for welcome trigger on member updates or bot addition
@Client.on_chat_member_updated()
async def welcome_member_handler(client: Client, chat_member_updated: ChatMemberUpdated):
    chat_id = chat_member_updated.chat.id
    group_name = chat_member_updated.chat.title or "Our Guild"

    # 1. Detect if the bot itself was added to the group
    if chat_member_updated.new_chat_member and chat_member_updated.new_chat_member.user.is_self:
        # Generate PIL welcome card on the fly and send it
        try:
            card_data = generate_welcome_card(group_name)
            bio = io.BytesIO(card_data)
            bio.name = f"welcome_{chat_id}.png"
            await client.send_photo(
                chat_id,
                bio,
                caption="💖 **Thank you for adding Welora Gacha RPG & Economy Bot!**\n\nUse `/game` to view instructions."
            )
        except Exception:
            pass
        return

    # 2. Trigger when a new member joins the chat
    if chat_member_updated.new_chat_member and not chat_member_updated.old_chat_member:
        user = chat_member_updated.new_chat_member.user

        # Avoid welcome loops for bots
        if user.is_bot:
            return

        settings = await get_group_settings(chat_id)
        welcome_template = settings["welcome_msg"] or "Welcome {name} to our group!"

        # Format welcome message
        formatted_msg = welcome_template.replace("{name}", user.first_name)

        try:
            # Generate group welcome banner on the fly and send it
            card_data = generate_welcome_card(group_name)
            bio = io.BytesIO(card_data)
            bio.name = f"welcome_{user.id}.png"
            await client.send_photo(
                chat_id,
                bio,
                caption=f"👋 **New Member Joined!**\n\n{formatted_msg}"
            )
        except Exception:
            # Fallback to plain text if photo fails
            await client.send_message(chat_id, f"👋 **New Member Joined!**\n\n{formatted_msg}")
