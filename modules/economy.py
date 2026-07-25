import time
import io
from pyrogram import Client, filters
from pyrogram.types import Message
from database import (
    get_db, create_or_get_user, update_user_balance, get_global_rank, dynamic_command
)
from utils.images import generate_stats_card, to_small_caps

@Client.on_message(dynamic_command("bal"))
async def bal_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    username = message.from_user.username or "unnamed"
    first_name = message.from_user.first_name or "User"

    # Target profile via reply
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        username = message.reply_to_message.from_user.username or "unnamed"
        first_name = message.reply_to_message.from_user.first_name or "User"

    user = await create_or_get_user(user_id, username, first_name)
    rank = await get_global_rank(user_id)

    # Render customized stats card with Pillow
    card_bytes = generate_stats_card(
        username=first_name,
        balance=user["coins"],
        rank=rank,
        gems=user["gems"],
        kills=user["kill_count"],
        xp=user["xp"]
    )

    # Send image stream
    bio = io.BytesIO(card_bytes)
    bio.name = f"stats_{user_id}.png"

    card_title = to_small_caps(f"Interactive Stats Card for {first_name}")
    lbl_coins = to_small_caps("Coins / Zexis:")
    lbl_gems = to_small_caps("Gems:")
    lbl_rank = to_small_caps("Global Rank:")
    lbl_kills = to_small_caps("Kill Count:")
    lbl_xp = to_small_caps("Experience (XP):")

    caption = (
        f"💳 **{card_title}**\n\n"
        f"💰 **{lbl_coins}** {user['coins']}\n"
        f"💎 **{lbl_gems}** {user['gems']}\n"
        f"🏆 **{lbl_rank}** #{rank}\n"
        f"🔥 **{lbl_kills}** {user['kill_count']}\n"
        f"⭐ **{lbl_xp}** {user['xp']}"
    )

    try:
        await client.send_photo(message.chat.id, bio, caption=caption)
    except Exception:
        # Fallback to text message if photo fails
        await message.reply_text(caption)

@Client.on_message(dynamic_command("daily"))
async def daily_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    now = int(time.time())
    one_day = 86400  # 24 hours in seconds

    last_daily = user["last_daily"] or 0
    time_passed = now - last_daily

    if time_passed < one_day:
        time_left = one_day - time_passed
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        err_title = to_small_caps("Daily Reward Cooldown!")
        err_msg = to_small_caps("You have already claimed your daily reward today! Come back in")
        await message.reply_text(
            f"❌ **{err_title}**\n\n"
            f"{err_msg} **{hours}h {minutes}m**!"
        )
        return

    streak = user["daily_streak"]
    # Check if the streak was broken (missed more than 48 hours)
    if time_passed > (one_day * 2):
        streak = 1
    else:
        streak += 1

    reward_coins = 2000 + (streak * 100)  # Streak bonus
    reward_xp = 50 + (streak * 10)

    async with get_db() as db:
        await db.execute("""
            UPDATE users SET
                coins = coins + ?,
                xp = xp + ?,
                daily_streak = ?,
                last_daily = ?
            WHERE id = ?
        """, (reward_coins, reward_xp, streak, now, user_id))
        await db.commit()

    success_title = to_small_caps("DAILY REWARD CLAIMED!")
    lbl_reward = to_small_caps("Reward:")
    lbl_streak = to_small_caps("Daily Streak:")
    await message.reply_text(
        f"📆 **{success_title}** 📆\n\n"
        f"🎁 **{lbl_reward}** {reward_coins} coins & {reward_xp} XP!\n"
        f"🔥 **{lbl_streak}** {streak} days in a row!"
    )

@Client.on_message(dynamic_command(["pay", "gift"]))
async def pay_or_gift_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Must reply to a message
    if not message.reply_to_message or not message.reply_to_message.from_user:
        err = to_small_caps("You must reply to a user's message to execute /pay or /gift!")
        await message.reply_text(f"❌ {err}")
        return

    target_user = message.reply_to_message.from_user
    if target_user.id == user_id:
        err = to_small_caps("You cannot pay or gift yourself!")
        await message.reply_text(f"❌ {err}")
        return

    await create_or_get_user(target_user.id, target_user.username, target_user.first_name)

    # Parse parameter
    if len(message.command) < 2:
        err = to_small_caps("Usage: Reply to a user with /pay <amount> or /gift <waifu name>")
        await message.reply_text(f"❌ {err}")
        return

    parameter = " ".join(message.command[1:]).strip()

    # Case 1: Transfer Coins (/pay <amount> or /gift <amount>)
    if parameter.isdigit():
        amount = int(parameter)
        if amount <= 0:
            err = to_small_caps("Transfer amount must be positive!")
            await message.reply_text(f"❌ {err}")
            return

        if user["coins"] < amount:
            err = to_small_caps("Insufficient coin balance!")
            await message.reply_text(f"❌ {err}")
            return

        # Perform coin transfer
        async with get_db() as db:
            await db.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (amount, user_id))
            await db.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, target_user.id))
            await db.commit()

        title = to_small_caps("Transaction Complete!")
        desc = to_small_caps(f"Successfully transferred {amount} coins to")
        await message.reply_text(
            f"💸 **{title}** 💸\n\n"
            f"{desc} **{target_user.first_name}**!"
        )
        return

    # Case 2: Gift a waifu character (/gift <waifu_name>)
    waifu_name = parameter
    async with get_db() as db:
        # Check if current user owns this waifu
        async with db.execute("""
            SELECT w.id, w.name FROM user_harems h
            JOIN waifus w ON h.waifu_id = w.id
            WHERE h.user_id = ? AND LOWER(w.name) = LOWER(?)
        """, (user_id, waifu_name)) as cursor:
            waifu = await cursor.fetchone()

            if not waifu:
                err = to_small_caps("You do not have this character in your harem to gift!")
                await message.reply_text(f"❌ {err}")
                return

            waifu_id = waifu["id"]

            # Transfer character ownership
            try:
                # Add to target harem
                await db.execute(
                    "INSERT INTO user_harems (user_id, waifu_id) VALUES (?, ?)",
                    (target_user.id, waifu_id)
                )
                # Remove from sender harem
                await db.execute(
                    "DELETE FROM user_harems WHERE user_id = ? AND waifu_id = ?",
                    (user_id, waifu_id)
                )
                await db.commit()

                title = to_small_caps("Gift Sent!")
                desc = to_small_caps(f"You have successfully gifted {waifu['name']} to")
                await message.reply_text(
                    f"🎁 **{title}** 🎁\n\n"
                    f"{desc} **{target_user.first_name}**!"
                )
            except Exception:
                await db.rollback()
                err = to_small_caps(f"{target_user.first_name} already owns this character!")
                await message.reply_text(f"❌ {err}")
