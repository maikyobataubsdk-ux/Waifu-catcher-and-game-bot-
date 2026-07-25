import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import (
    create_or_get_user, update_user_balance, dynamic_command
)

# Global word scrabble tracker: chat_id -> original_word
ACTIVE_SCRABBLES = {}

# Selection of words for scrabble mini-game
SCRABBLE_WORDS = [
    "pyrogram", "telethon", "waifu", "gacha", "rpg", "combat", "economy",
    "multiplier", "rocket", "protection", "legendary", "velora", "harem"
]

@Client.on_message(dynamic_command("rocket"))
async def rocket_command(client: Client, message: Message):
    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Usage: /rocket <bet_amount> <multiplier_target>
    # e.g., /rocket 1000 2.0
    if len(message.command) < 3:
        await message.reply_text("❌ Usage: `/rocket <bet_amount> <multiplier_target>`\nExample: `/rocket 1000 2.0` (target 2.0x multiplier)")
        return

    try:
        bet_amount = int(message.command[1])
        multiplier_target = float(message.command[2])
    except ValueError:
        await message.reply_text("❌ Bet amount must be an integer, and target multiplier must be a float!")
        return

    if bet_amount <= 0:
        await message.reply_text("❌ Bet amount must be positive!")
        return

    if multiplier_target < 1.01:
        await message.reply_text("❌ Target multiplier must be at least 1.01x!")
        return

    if user["coins"] < bet_amount:
        await message.reply_text(f"❌ Insufficient balance! You only have {user['coins']} coins.")
        return

    # Deduct bet amount
    await update_user_balance(user_id, coins_delta=-bet_amount)

    # Determine actual crash multiplier
    # Classic crash mechanic: crash on 1.00x with 10% chance, or random distribution
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
        await message.reply_text(
            f"🚀 **ROCKET TO THE MOON!** 🚀\n\n"
            f"📈 Rocket safely reached **{crash_point:.2f}x** (Target: {multiplier_target:.2f}x)!\n"
            f"🎉 **YOU WON!** Received **{winnings}** coins! (+20 XP)"
        )
    else:
        # Crash!
        await message.reply_text(
            f"💥 **BOOM! CRASHED!** 💥\n\n"
            f"📈 The rocket crashed at **{crash_point:.2f}x** before reaching your target of {multiplier_target:.2f}x!\n"
            f"💸 You lost your bet of **{bet_amount}** coins."
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

    ACTIVE_SCRABBLES[chat_id] = word

    await message.reply_text(
        f"🧩 **SCRABBLE MINI-GAME TRIGGERED!** 🧩\n\n"
        f"Unscramble the word below to win 500 coins:\n"
        f"👉 **`{scrambled}`** 👈\n\n"
        f"Type your answer directly in the group!"
    )

# Listener for Scrabble answers
@Client.on_message(filters.group & ~filters.service & ~filters.bot)
async def scrabble_listener(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in ACTIVE_SCRABBLES:
        return

    user_answer = (message.text or "").strip().lower()
    correct_word = ACTIVE_SCRABBLES[chat_id]

    if user_answer == correct_word:
        # Clear active scrabble game
        del ACTIVE_SCRABBLES[chat_id]

        user_id = message.from_user.id
        first_name = message.from_user.first_name or "User"
        await create_or_get_user(user_id, message.from_user.username, first_name)

        reward = 500
        await update_user_balance(user_id, coins_delta=reward, xp_delta=30)

        await message.reply_text(
            f"🎉 **CORRECT ANSWER!** 🎉\n\n"
            f"**{first_name}** unscrambled the word **{correct_word}** first!\n"
            f"💰 Reward of **{reward}** coins and **30 XP** has been awarded!"
        )

@Client.on_message(dynamic_command("game"))
async def game_menu_command(client: Client, message: Message):
    # Returns an interactive explanatory inline-menu for mini-games and economy rules
    text = (
        "🎮 **WELORA GAMES & ECONOMY INDEX** 🎮\n\n"
        "Welcome to the Welora bot dashboard! Here you can check out all our games and rules."
    )

    buttons = [
        [
            InlineKeyboardButton("🚀 Rocket / Crash", callback_data="rules_rocket"),
            InlineKeyboardButton("🧩 Word Scrabble", callback_data="rules_scrabble")
        ],
        [
            InlineKeyboardButton("💰 Economy & RPG Rules", callback_data="rules_economy"),
            InlineKeyboardButton("🛡️ Shield & Protection", callback_data="rules_shield")
        ]
    ]

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^rules_(\w+)$"))
async def rules_callback(client: Client, callback_query: CallbackQuery):
    rule_type = callback_query.matches[0].group(1)

    rules = {
        "rocket": (
            "🚀 **ROCKET / CRASH GAME RULES** 🚀\n\n"
            "Multiplier-based roulette. Place a bet and choose a multiplier target!\n"
            "Format: `/rocket <bet> <target>`\n"
            "• Example: `/rocket 1000 2.5`\n"
            "If the rocket reaches or exceeds your target, you win bet * target coins!\n"
            "Otherwise, your bet is lost."
        ),
        "scrabble": (
            "🧩 **WORD SCRABBLE RULES** 🧩\n\n"
            "Command: `/scrabble`\n"
            "The bot will scramble a random game/anime word and drop it in the group chat.\n"
            "The first user to type the unscrambled word correctly in chat wins **500 coins**!"
        ),
        "economy": (
            "💰 **ECONOMY & RPG RULES** 💰\n\n"
            "• `/bal`: Check balance & stats card.\n"
            "• `/daily`: Claim 2000+ coins daily and build a streak.\n"
            "• `/pay`: Pay or gift coins/waifus to active friends.\n"
            "• `/rob`: Reply to rob a user. 40% chance of failing and paying a penalty!\n"
            "• `/kill`: Attempt to assassinate a user. Sets target to dead status for 2 hours."
        ),
        "shield": (
            "🛡️ **SHIELD & PROTECTION RULES** 🛡️\n\n"
            "Command: `/protect <days>`\n"
            "Purchase a protective shield for 1 or 2 days using 1500 coins per day.\n"
            "An active shield blocks all `/rob` and `/kill` attempts directed at you!"
        )
    }

    rule_text = rules.get(rule_type, "No rules found.")

    # Back to index button
    buttons = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="rules_index")]]

    await callback_query.message.edit_text(rule_text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^rules_index$"))
async def rules_index_callback(client: Client, callback_query: CallbackQuery):
    text = (
        "🎮 **WELORA GAMES & ECONOMY INDEX** 🎮\n\n"
        "Welcome to the Welora bot dashboard! Here you can check out all our games and rules."
    )

    buttons = [
        [
            InlineKeyboardButton("🚀 Rocket / Crash", callback_data="rules_rocket"),
            InlineKeyboardButton("🧩 Word Scrabble", callback_data="rules_scrabble")
        ],
        [
            InlineKeyboardButton("💰 Economy & RPG Rules", callback_data="rules_economy"),
            InlineKeyboardButton("🛡️ Shield & Protection", callback_data="rules_shield")
        ]
    ]

    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
