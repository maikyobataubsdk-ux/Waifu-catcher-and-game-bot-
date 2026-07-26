import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import (
    create_or_get_user, update_user_balance, dynamic_command
)
from utils.images import to_small_caps
import utils.redis_cache as redis_cache

# Selection of words for scrabble mini-game
SCRABBLE_WORDS = [
    "pyrogram", "telethon", "waifu", "gacha", "rpg", "combat", "economy",
    "multiplier", "rocket", "protection", "legendary", "velora", "harem"
]

@Client.on_message(dynamic_command("rocket"))
async def rocket_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Usage: /rocket <bet_amount> <multiplier_target>
    if len(message.command) < 3:
        usage = to_small_caps("Usage:")
        example = to_small_caps("Example: /rocket 1000 2.0 (target 2.0x multiplier)")
        await message.reply_text(f"❌ **{usage}** `/rocket <bet_amount> <multiplier_target>`\n{example}")
        return

    try:
        bet_amount = int(message.command[1])
        multiplier_target = float(message.command[2])
    except ValueError:
        err = to_small_caps("Bet amount must be an integer, and target multiplier must be a float!")
        await message.reply_text(f"❌ {err}")
        return

    if bet_amount <= 0:
        err = to_small_caps("Bet amount must be positive!")
        await message.reply_text(f"❌ {err}")
        return

    if multiplier_target < 1.01:
        err = to_small_caps("Target multiplier must be at least 1.01x!")
        await message.reply_text(f"❌ {err}")
        return

    if user["coins"] < bet_amount:
        err = to_small_caps(f"Insufficient balance! You only have {user['coins']} coins.")
        await message.reply_text(f"❌ {err}")
        return

    # Deduct bet amount
    await update_user_balance(user_id, coins_delta=-bet_amount)

    # Determine actual crash multiplier
    if random.random() < 0.10:
        crash_point = 1.00
    else:
        # Generate multiplier distribution favoring lower multipliers
        crash_point = round(1.0 + (random.gammavariate(1, 1.5)), 2)
        if crash_point < 1.01:
            crash_point = 1.01

    if crash_point >= multiplier_target:
        # Success!
        winnings = int(bet_amount * multiplier_target)
        await update_user_balance(user_id, coins_delta=winnings, xp_delta=20)
        title = to_small_caps("ROCKET TO THE MOON!")
        desc = to_small_caps(f"Rocket safely reached {crash_point:.2f}x (Target: {multiplier_target:.2f}x)!")
        won = to_small_caps(f"You won! Received {winnings} coins!")
        await message.reply_text(
            f"🚀 **{title}** 🚀\n\n"
            f"📈 {desc}\n"
            f"🎉 **{won}** (+20 XP)"
        )
    else:
        # Crash!
        title = to_small_caps("BOOM! CRASHED!")
        desc = to_small_caps(f"The rocket crashed at {crash_point:.2f}x before reaching your target of {multiplier_target:.2f}x!")
        lost = to_small_caps(f"You lost your bet of {bet_amount} coins.")
        await message.reply_text(
            f"💥 **{title}** 💥\n\n"
            f"📈 {desc}\n"
            f"💸 {lost}"
        )

@Client.on_message(dynamic_command("scrabble"))
async def scrabble_command(client: Client, message: Message):
    chat_id = message.chat.id

    # Choose a word and scramble it
    word = random.choice(SCRABBLE_WORDS)
    scrambled = "".join(random.sample(word, len(word)))

    # Ensure scrambled isn't exactly the original word
    while scrambled == word and len(word) > 1:
        scrambled = "".join(random.sample(word, len(word)))

    # Save active scrabble in Redis cache
    await redis_cache.set_scrabble_word(chat_id, word)

    title = to_small_caps("SCRABBLE MINI-GAME TRIGGERED!")
    desc = to_small_caps("Unscramble the word below to win 500 coins:")
    type_ans = to_small_caps("Type your answer directly in the group!")
    await message.reply_text(
        f"🧩 **{title}** 🧩\n\n"
        f"{desc}\n"
        f"👉 **`{scrambled}`** 👈\n\n"
        f"{type_ans}"
    )

# Listener for Scrabble answers
@Client.on_message(filters.group & ~filters.service & ~filters.bot)
async def scrabble_listener(client: Client, message: Message):
    chat_id = message.chat.id

    correct_word = await redis_cache.get_scrabble_word(chat_id)
    if not correct_word:
        return

    user_answer = (message.text or "").strip().lower()

    if user_answer == correct_word:
        # Clear active scrabble game from cache
        await redis_cache.delete_scrabble_word(chat_id)

        if not message.from_user:
            return

        user_id = message.from_user.id
        first_name = message.from_user.first_name or "User"
        await create_or_get_user(user_id, message.from_user.username, first_name)

        reward = 500
        await update_user_balance(user_id, coins_delta=reward, xp_delta=30)

        title = to_small_caps("Correct Answer!")
        desc = to_small_caps(f"unscrambled the word {correct_word} first!")
        reward_msg = to_small_caps(f"Reward of {reward} coins and 30 XP has been awarded!")
        await message.reply_text(
            f"🎉 **{title}** 🎉\n\n"
            f"**{first_name}** {desc}\n"
            f"💰 {reward_msg}"
        )

@Client.on_message(dynamic_command("game"))
async def game_menu_command(client: Client, message: Message):
    title = to_small_caps("Welora Games & Economy Index")
    desc = to_small_caps("Welcome to the Welora bot dashboard! Here you can check out all our games and rules.")

    btn_rocket = to_small_caps("Rocket / Crash")
    btn_scrabble = to_small_caps("Word Scrabble")
    btn_rpg = to_small_caps("Economy & RPG Rules")
    btn_shield = to_small_caps("Shield & Protection")

    buttons = [
        [
            InlineKeyboardButton(f"🚀 {btn_rocket}", callback_data="rules_rocket"),
            InlineKeyboardButton(f"🧩 {btn_scrabble}", callback_data="rules_scrabble")
        ],
        [
            InlineKeyboardButton(f"💰 {btn_rpg}", callback_data="rules_economy"),
            InlineKeyboardButton(f"🛡️ {btn_shield}", callback_data="rules_shield")
        ]
    ]

    await message.reply_text(f"🎮 **{title}** 🎮\n\n{desc}", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^rules_(\w+)$"))
async def rules_callback(client: Client, callback_query: CallbackQuery):
    rule_type = callback_query.matches[0].group(1)

    rules = {
        "rocket": (
            f"🚀 **{to_small_caps('Rocket / Crash Game Rules')}** 🚀\n\n"
            f"{to_small_caps('Multiplier-based roulette. Place a bet and choose a multiplier target!')}\n"
            f"{to_small_caps('Format:')} `/rocket <bet> <target>`\n"
            f"• {to_small_caps('Example:')} `/rocket 1000 2.5`\n"
            f"{to_small_caps('If the rocket reaches or exceeds your target, you win bet * target coins!')}\n"
            f"{to_small_caps('Otherwise, your bet is lost.')}"
        ),
        "scrabble": (
            f"🧩 **{to_small_caps('Word Scrabble Rules')}** 🧩\n\n"
            f"{to_small_caps('Command:')} `/scrabble`\n"
            f"{to_small_caps('The bot will scramble a random game/anime word and drop it in the group chat.')}\n"
            f"{to_small_caps('The first user to type the unscrambled word correctly in chat wins 500 coins!')}"
        ),
        "economy": (
            f"💰 **{to_small_caps('Economy & RPG Rules')}** 💰\n\n"
            f"• `/bal`: {to_small_caps('Check balance & stats card.')}\n"
            f"• `/daily`: {to_small_caps('Claim 2000+ coins daily and build a streak.')}\n"
            f"• `/pay`: {to_small_caps('Pay or gift coins/waifus to active friends.')}\n"
            f"• `/rob`: {to_small_caps('Reply to rob a user. 40% chance of failing and paying a penalty!')}\n"
            f"• `/kill`: {to_small_caps('Attempt to assassinate a user. Sets target to dead status for 2 hours.')}"
        ),
        "shield": (
            f"🛡️ **{to_small_caps('Shield & Protection Rules')}** 🛡️\n\n"
            f"{to_small_caps('Command:')} `/protect <days>`\n"
            f"{to_small_caps('Purchase a protective shield for 1 or 2 days using 1500 coins per day.')}\n"
            f"{to_small_caps('An active shield blocks all /rob and /kill attempts directed at you!')}"
        )
    }

    rule_text = rules.get(rule_type, "No rules found.")

    btn_back = to_small_caps("Back to Menu")
    buttons = [[InlineKeyboardButton(f"⬅️ {btn_back}", callback_data="rules_index")]]

    await callback_query.message.edit_text(rule_text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^rules_index$"))
async def rules_index_callback(client: Client, callback_query: CallbackQuery):
    title = to_small_caps("Welora Games & Economy Index")
    desc = to_small_caps("Welcome to the Welora bot dashboard! Here you can check out all our games and rules.")

    btn_rocket = to_small_caps("Rocket / Crash")
    btn_scrabble = to_small_caps("Word Scrabble")
    btn_rpg = to_small_caps("Economy & RPG Rules")
    btn_shield = to_small_caps("Shield & Protection")

    buttons = [
        [
            InlineKeyboardButton(f"🚀 {btn_rocket}", callback_data="rules_rocket"),
            InlineKeyboardButton(f"🧩 {btn_scrabble}", callback_data="rules_scrabble")
        ],
        [
            InlineKeyboardButton(f"💰 {btn_rpg}", callback_data="rules_economy"),
            InlineKeyboardButton(f"🛡️ {btn_shield}", callback_data="rules_shield")
        ]
    ]

    await callback_query.message.edit_text(f"🎮 **{title}** 🎮\n\n{desc}", reply_markup=InlineKeyboardMarkup(buttons))
