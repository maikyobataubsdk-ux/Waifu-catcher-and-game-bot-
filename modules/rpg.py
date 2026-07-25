import time
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from database import (
    get_db, create_or_get_user, update_user_balance, dynamic_command
)
from utils.images import to_small_caps

# Global memory Cooldown tracker
RPG_COOLDOWN = {}

@Client.on_message(dynamic_command("rob"))
async def rob_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Must reply to someone
    if not message.reply_to_message or not message.reply_to_message.from_user:
        err = to_small_caps("You must reply to a user's message to attempt to rob them!")
        await message.reply_text(f"❌ {err}")
        return

    target = message.reply_to_message.from_user
    if target.id == user_id:
        err = to_small_caps("You cannot rob yourself!")
        await message.reply_text(f"❌ {err}")
        return

    target_user = await create_or_get_user(target.id, target.username, target.first_name)

    # Check cooldown
    now = int(time.time())
    cooldown_time = 300  # 5 minutes rob cooldown
    last_rob = RPG_COOLDOWN.get(user_id, {}).get("last_rob", 0)
    if (now - last_rob) < cooldown_time:
        time_left = cooldown_time - (now - last_rob)
        title = to_small_caps("Rob on Cooldown!")
        desc = to_small_caps(f"You must wait {time_left} more seconds before committing another robbery.")
        await message.reply_text(f"⏱️ **{title}**\n{desc}")
        return

    # Check if target is protected by a shield
    shield_time = target_user["is_protected_until"] or 0
    if shield_time > now:
        title = to_small_caps("Heavily Guarded!")
        desc = to_small_caps(f"has an active protection shield! Your robbery attempt was blocked.")
        await message.reply_text(f"🛡️ **{title}**\n**{target.first_name}** {desc}")
        return

    # Check if target is dead
    dead_time = target_user["is_dead_until"] or 0
    if dead_time > now:
        title = to_small_caps("Zero Target!")
        desc = to_small_caps("is currently dead and has nothing worth robbing!")
        await message.reply_text(f"💀 **{title}**\n**{target.first_name}** {desc}")
        return

    # Set cooldown
    if user_id not in RPG_COOLDOWN:
        RPG_COOLDOWN[user_id] = {}
    RPG_COOLDOWN[user_id]["last_rob"] = now

    # Check target coins
    target_coins = target_user["coins"]
    if target_coins < 100:
        err = to_small_caps("This user is too poor to be robbed!")
        await message.reply_text(f"❌ {err}")
        return

    # 40% chance of failure (penalty paid to target)
    if random.random() < 0.40:
        penalty = int(user["coins"] * 0.20)
        if penalty < 50:
            penalty = 50
        penalty = min(penalty, user["coins"])

        async with get_db() as db:
            await db.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (penalty, user_id))
            await db.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (penalty, target.id))
            await db.commit()

        title = to_small_caps("Robbery Failed!")
        caught = to_small_caps("You were caught by the city guards!")
        lost = to_small_caps(f"You paid a penalty of {penalty} coins to")
        await message.reply_text(
            f"🚨 **{title}** 🚨\n\n"
            f"{caught}\n"
            f"💸 {lost} **{target.first_name}**!"
        )
    else:
        # Success: Steal 10% - 30% of target coins
        percent = random.randint(10, 30)
        stolen = int(target_coins * (percent / 100))

        async with get_db() as db:
            await db.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (stolen, user_id))
            await db.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (stolen, target.id))
            await db.commit()

        title = to_small_caps("Heist Successful!")
        desc = to_small_caps(f"You sneaked behind and successfully stole {stolen} coins ({percent}%) from")
        await message.reply_text(
            f"💰 **{title}** 💰\n\n"
            f"{desc} **{target.first_name}**!"
        )

@Client.on_message(dynamic_command("kill"))
async def kill_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Must reply to someone
    if not message.reply_to_message or not message.reply_to_message.from_user:
        err = to_small_caps("You must reply to a user's message to execute /kill!")
        await message.reply_text(f"❌ {err}")
        return

    target = message.reply_to_message.from_user
    if target.id == user_id:
        err = to_small_caps("You cannot kill yourself!")
        await message.reply_text(f"❌ {err}")
        return

    target_user = await create_or_get_user(target.id, target.username, target.first_name)

    # Check cooldown
    now = int(time.time())
    cooldown_time = 600  # 10 minutes kill cooldown
    last_kill = RPG_COOLDOWN.get(user_id, {}).get("last_kill", 0)
    if (now - last_kill) < cooldown_time:
        time_left = cooldown_time - (now - last_kill)
        title = to_small_caps("Assassination on Cooldown!")
        desc = to_small_caps(f"You must wait {time_left} more seconds before trying again.")
        await message.reply_text(f"⏱️ **{title}**\n{desc}")
        return

    # Check protection shield
    shield_time = target_user["is_protected_until"] or 0
    if shield_time > now:
        title = to_small_caps("Attack Blocked!")
        desc = to_small_caps(f"has an active protective shield! Your attack bounced back.")
        await message.reply_text(f"🛡️ **{title}**\n**{target.first_name}** {desc}")
        return

    # Check if already dead
    dead_time = target_user["is_dead_until"] or 0
    if dead_time > now:
        title = to_small_caps("Dead Already!")
        desc = to_small_caps("is already in the afterlife.")
        await message.reply_text(f"💀 **{title}**\n**{target.first_name}** {desc}")
        return

    # Cost/requirement for assassination
    assassination_cost = 500
    if user["coins"] < assassination_cost:
        err = to_small_caps(f"Planning an assassination requires at least {assassination_cost} coins!")
        await message.reply_text(f"❌ {err}")
        return

    # Set cooldown
    if user_id not in RPG_COOLDOWN:
        RPG_COOLDOWN[user_id] = {}
    RPG_COOLDOWN[user_id]["last_kill"] = now

    # Deduct planning cost
    await update_user_balance(user_id, coins_delta=-assassination_cost)

    # 50% chance of assassination success
    if random.random() < 0.50:
        # Success: Steal 25% of XP & 15% of wealth, and set is_dead_until for 2 hours
        stolen_xp = int(target_user["xp"] * 0.25)
        stolen_coins = int(target_user["coins"] * 0.15)
        death_duration = 7200  # 2 hours

        async with get_db() as db:
            await db.execute("""
                UPDATE users SET
                    coins = coins + ?,
                    xp = xp + ?,
                    kill_count = kill_count + 1
                WHERE id = ?
            """, (stolen_coins, stolen_xp, user_id))

            await db.execute("""
                UPDATE users SET
                    coins = MAX(0, coins - ?),
                    xp = MAX(0, xp - ?),
                    is_dead_until = ?
                WHERE id = ?
            """, (stolen_coins, stolen_xp, now + death_duration, target.id))
            await db.commit()

        title = to_small_caps("Assassination Successful!")
        stolen = to_small_caps(f"Stolen: {stolen_coins} coins & {stolen_xp} XP!")
        effect = to_small_caps("Target status set to DEAD for 2 hours. Your Kill Count increased!")
        await message.reply_text(
            f"💀 **{title}** 💀\n\n"
            f"**{to_small_caps('You successfully assassinated')} {target.first_name}!**\n"
            f"🔥 {stolen}\n"
            f"🎯 {effect}"
        )
    else:
        # Fail: Robber dies instead (set dead for 1 hour)
        death_duration = 3600  # 1 hour
        async with get_db() as db:
            await db.execute("UPDATE users SET is_dead_until = ? WHERE id = ?", (now + death_duration, user_id))
            await db.commit()

        title = to_small_caps("Assassination Botched!")
        desc = to_small_caps("The target's guards overpowered you and retaliated!")
        dead = to_small_caps("You have been KILLED instead and are dead for 1 hour!")
        await message.reply_text(
            f"🚨 **{title}** 🚨\n\n"
            f"{desc}\n"
            f"💀 **{dead}**"
        )

@Client.on_message(dynamic_command("protect"))
async def protect_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Usage: /protect <days> (1 or 2 days)
    if len(message.command) < 2:
        usage = to_small_caps("Usage: /protect <1 or 2> (in days)")
        await message.reply_text(f"❌ {usage}")
        return

    days_str = message.command[1]
    if days_str not in ["1", "2"]:
        err = to_small_caps("You can only purchase a protective shield for 1 or 2 days!")
        await message.reply_text(f"❌ {err}")
        return

    days = int(days_str)
    cost = days * 1500  # 1500 per day

    if user["coins"] < cost:
        err = to_small_caps(f"You need at least {cost} coins to purchase a {days}-day shield!")
        await message.reply_text(f"❌ {err}")
        return

    now = int(time.time())
    shield_duration = days * 86400

    # Calculate base shield expiration (extend if already shielded)
    current_shield = user["is_protected_until"] or 0
    base_time = max(now, current_shield)
    new_shield_time = base_time + shield_duration

    async with get_db() as db:
        await db.execute("""
            UPDATE users SET
                coins = coins - ?,
                is_protected_until = ?
            WHERE id = ?
        """, (cost, new_shield_time, user_id))
        await db.commit()

    title = to_small_caps("SHIELD ACTIVATED!")
    desc = to_small_caps(f"You successfully purchased a {days}-day protective shield for {cost} coins!")
    effect = to_small_caps("This blocks all /rob and /kill attempts.")
    await message.reply_text(
        f"🛡️ **{title}** 🛡️\n\n"
        f"{desc}\n"
        f"{effect}"
    )
