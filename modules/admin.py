import io
from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated
from database import (
    get_db, create_or_get_user, get_top_richest, get_group_settings, update_group_settings, dynamic_command
)
from utils.images import generate_welcome_card, to_small_caps

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
                label = to_small_caps("Toxicity Filter")
                await client.send_message(chat_id, f"⚠️ **{label}:** Message from {message.from_user.first_name or 'User'} deleted.")
                return
            except Exception:
                pass

    # NSFW filtering
    if settings["nsfw_filter"] == 1:
        if any(word in text for word in NSFW_WORDS):
            try:
                await message.delete()
                label = to_small_caps("NSFW Filter")
                await client.send_message(chat_id, f"⚠️ **{label}:** Message from {message.from_user.first_name or 'User'} deleted.")
                return
            except Exception:
                pass

@Client.on_message(dynamic_command("setgroup"))
async def setgroup_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check permissions
    if not await is_eligible_admin(user_id):
        err_msg = to_small_caps("Permission Denied! This command can only be used by Bot Admins or the Top 5 Global Richest users.")
        await message.reply_text(f"❌ {err_msg}")
        return

    # Usage: /setgroup <setting> <value>
    if len(message.command) < 3:
        title = to_small_caps("Group Management Controls")
        usage = to_small_caps("Usage:")
        available = to_small_caps("Available Settings:")
        prefix_desc = to_small_caps("Change custom prefix (default: /)")
        toxicity_desc = to_small_caps("Toggle toxic filter")
        nsfw_desc = to_small_caps("Toggle NSFW/adult contents filter")
        welcome_desc = to_small_caps("Set custom group welcome message (use {name} placeholder)")

        await message.reply_text(
            f"⚙️ **{title}** ⚙️\n\n"
            f"**{usage}** `/setgroup <setting> <value>`\n\n"
            f"**{available}**\n"
            f"• `prefix <char>` - {prefix_desc}\n"
            f"• `toxicity <0/1>` - {toxicity_desc}\n"
            f"• `nsfw <0/1>` - {nsfw_desc}\n"
            f"• `welcome <text>` - {welcome_desc}"
        )
        return

    setting = message.command[1].lower()
    value = " ".join(message.command[2:]).strip()

    if setting == "prefix":
        await update_group_settings(chat_id, custom_prefix=value)
        msg = to_small_caps("Custom prefix updated to:")
        await message.reply_text(f"✅ {msg} `{value}`")

    elif setting == "toxicity":
        if value not in ["0", "1"]:
            err = to_small_caps("Toxicity setting must be 0 (off) or 1 (on)!")
            await message.reply_text(f"❌ {err}")
            return
        await update_group_settings(chat_id, toxicity_filter=int(value))
        status = to_small_caps("ENABLED") if value == "1" else to_small_caps("DISABLED")
        msg = to_small_caps("Toxicity filter is now")
        await message.reply_text(f"✅ {msg} **{status}**.")

    elif setting == "nsfw":
        if value not in ["0", "1"]:
            err = to_small_caps("NSFW setting must be 0 (off) or 1 (on)!")
            await message.reply_text(f"❌ {err}")
            return
        await update_group_settings(chat_id, nsfw_filter=int(value))
        status = to_small_caps("ENABLED") if value == "1" else to_small_caps("DISABLED")
        msg = to_small_caps("NSFW filter is now")
        await message.reply_text(f"✅ {msg} **{status}**.")

    elif setting == "welcome":
        await update_group_settings(chat_id, welcome_msg=value)
        msg = to_small_caps("Custom group welcome message set to:")
        await message.reply_text(f"✅ {msg}\n`{value}`")

    else:
        err = to_small_caps("Invalid setting! Use /setgroup to see options.")
        await message.reply_text(f"❌ {err}")

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
            caption = to_small_caps("Thank you for adding Welora Gacha RPG & Economy Bot! Use /game to view instructions.")
            await client.send_photo(
                chat_id,
                bio,
                caption=f"💖 **{caption}**"
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

        title = to_small_caps("New Member Joined!")
        try:
            # Generate group welcome banner on the fly and send it
            card_data = generate_welcome_card(group_name)
            bio = io.BytesIO(card_data)
            bio.name = f"welcome_{user.id}.png"
            await client.send_photo(
                chat_id,
                bio,
                caption=f"👋 **{title}**\n\n{formatted_msg}"
            )
        except Exception:
            # Fallback to plain text if photo fails
            await client.send_message(chat_id, f"👋 **{title}**\n\n{formatted_msg}")
