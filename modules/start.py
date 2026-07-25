from pyrogram import Client
from pyrogram.types import Message
from database import create_or_get_user, dynamic_command
from utils.images import to_small_caps

@Client.on_message(dynamic_command(["start", "help"]))
async def start_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    username = message.from_user.username or "unnamed"
    first_name = message.from_user.first_name or "User"

    # Ensure user is registered
    await create_or_get_user(user_id, username, first_name)

    title = to_small_caps("Welora Gacha, RPG & Economy")
    welcome_msg = (
        f"💖 **{title}** 💖\n\n"
        f"👋 **{to_small_caps('Hello')} {first_name}!**\n\n"
        f"✨ **{to_small_caps('Welcome to Welora Bot!')}** {to_small_caps('The ultimate Telegram Gacha, RPG, and multi-tenant Economy experience!')}\n\n"
        f"🎯 **{to_small_caps('How to Play:')}**\n"
        f"• {to_small_caps('Economy & Balance:')} `/bal` - {to_small_caps('Check stats card')}\n"
        f"• {to_small_caps('Daily Reward:')} `/daily` - {to_small_caps('Claim coins & build streak')}\n"
        f"• {to_small_caps('Auto Spawns:')} {to_small_caps('Chat in groups to trigger random character spawns!')}\n"
        f"• {to_small_caps('Grasp/Claim:')} `/grasp` {to_small_caps('or')} `/claim` - {to_small_caps('Catch spawned characters')}\n"
        f"• {to_small_caps('Check Harem:')} `/harem` - {to_small_caps('View caught characters')}\n"
        f"• {to_small_caps('Propose Marriage:')} `/propose` - {to_small_caps('Reply to propose to a user')}\n"
        f"• {to_small_caps('Marry Character:')} `/marry <waifu name>` - {to_small_caps('Marry a character in harem')}\n"
        f"• {to_small_caps('Rocket Game:')} `/rocket <bet> <multiplier>` - {to_small_caps('Crash game')}\n"
        f"• {to_small_caps('Word Scrabble:')} `/scrabble` - {to_small_caps('Unscramble words for rewards')}\n"
        f"• {to_small_caps('Robbery & Attacks:')} `/rob` {to_small_caps('and')} `/kill` - {to_small_caps('Steal or kill a target')}\n"
        f"• {to_small_caps('Protection Shield:')} `/protect <days>` - {to_small_caps('Block steals & kills')}\n"
        f"• {to_small_caps('Group Settings:')} `/setgroup` - {to_small_caps('Change custom prefix, filters')}\n\n"
        f"🕹️ **{to_small_caps('Type')} `/game` {to_small_caps('to view the interactive menu and games index!')}**"
    )

    await message.reply_text(welcome_msg)
