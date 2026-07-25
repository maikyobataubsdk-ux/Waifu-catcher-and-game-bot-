import time
import io
from pyrogram import Client, filters
from pyrogram.types import Message
from database import (
    get_db, create_or_get_user, update_user_balance, get_global_rank, dynamic_command
)
from utils.images import generate_stats_card

@Client.on_message(dynamic_command("bal"))
async def bal_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unnamed"
    first_name = message.from_user.first_name or "User"

    # Target profile via reply or mention
    if message.reply_to_message:
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

    caption = (
        f"💳 **Interactive Stats Card for {first_name}**\n\n"
        f"💰 **ZEXIS / Coins:** {user['coins']}\n"
        f"💎 **Gems:** {user['gems']}\n"
        f"🏆 **Global Rank:** #{rank}\n"
        f"🔥 **Kill Count:** {user['kill_count']}\n"
        f"⭐ **Experience (XP):** {user['xp']}"
    )

    try:
        await client.send_photo(message.chat.id, bio, caption=caption)
    except Exception:
        # Fallback to text message if photo fails
        await message.reply_text(caption)

@Client.on_message(dynamic_command("daily"))
async def daily_command(client: Client, message: Message):
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
        await message.reply_text(
            f"❌ **Daily Reward Cooldown!**\n\n"
            f"You have already claimed your daily reward today!\n"
            f"Come back in **{hours}h {minutes}m**!"
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

    await message.reply_text(
        f"📆 **DAILY REWARD CLAIMED!** 📆\n\n"
        f"🎁 **Reward:** {reward_coins} coins & {reward_xp} XP!\n"
        f"🔥 **Daily Streak:** {streak} days in a row!"
    )

@Client.on_message(dynamic_command(["pay", "gift"]))
async def pay_or_gift_command(client: Client, message: Message):
    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Must reply to a message
    if not message.reply_to_message:
        await message.reply_text("❌ You must reply to a user's message to execute `/pay` or `/gift`!")
        return

    target_user = message.reply_to_message.from_user
    if target_user.id == user_id:
        await message.reply_text("❌ You cannot pay or gift yourself!")
        return

    await create_or_get_user(target_user.id, target_user.username, target_user.first_name)

    # Parse parameter
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: Reply to a user with `/pay <amount>` or `/gift <waifu name>`")
        return

    parameter = " ".join(message.command[1:]).strip()

    # Case 1: Transfer Coins (/pay <amount> or /gift <amount>)
    if parameter.isdigit():
        amount = int(parameter)
        if amount <= 0:
            await message.reply_text("❌ Transfer amount must be positive!")
            return

        if user["coins"] < amount:
            await message.reply_text("❌ Insufficient coin balance!")
            return

        # Perform coin transfer
        async with get_db() as db:
            await db.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (amount, user_id))
            await db.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, target_user.id))
            await db.commit()

        await message.reply_text(
            f"💸 **Transaction Complete!** 💸\n\n"
            f"Successfully transferred **{amount}** coins to **{target_user.first_name}**!"
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
                await message.reply_text("❌ You do not have this character in your harem to gift!")
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

                await message.reply_text(
                    f"🎁 **GIFT SENT!** 🎁\n\n"
                    f"You have successfully gifted **{waifu['name']}** to **{target_user.first_name}**!"
                )
            except Exception:
                await db.rollback()
                await message.reply_text(f"❌ {target_user.first_name} already owns this character!")
