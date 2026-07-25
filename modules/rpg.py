import time
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from database import (
    get_db, create_or_get_user, update_user_balance, dynamic_command
)

# Global memory Cooldown tracker
# keys are user_id -> { "last_rob": timestamp, "last_kill": timestamp }
RPG_COOLDOWN = {}

@Client.on_message(dynamic_command("rob"))
async def rob_command(client: Client, message: Message):
    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Must reply to someone
    if not message.reply_to_message:
        await message.reply_text("❌ You must reply to a user's message to attempt to rob them!")
        return

    target = message.reply_to_message.from_user
    if target.id == user_id:
        await message.reply_text("❌ You cannot rob yourself!")
        return

    target_user = await create_or_get_user(target.id, target.username, target.first_name)

    # Check cooldown
    now = int(time.time())
    cooldown_time = 300  # 5 minutes rob cooldown
    last_rob = RPG_COOLDOWN.get(user_id, {}).get("last_rob", 0)
    if (now - last_rob) < cooldown_time:
        time_left = cooldown_time - (now - last_rob)
        await message.reply_text(f"⏱️ **Rob on Cooldown!**\nYou must wait {time_left} more seconds before committing another robbery.")
        return

    # Check if target is protected by a shield
    shield_time = target_user["is_protected_until"] or 0
    if shield_time > now:
        await message.reply_text(f"🛡️ **Heavily Guarded!**\n**{target.first_name}** has an active protection shield! Your robbery attempt was blocked.")
        return

    # Check if target is dead
    dead_time = target_user["is_dead_until"] or 0
    if dead_time > now:
        await message.reply_text(f"💀 **Zero Target!**\n**{target.first_name}** is currently dead and has nothing worth robbing!")
        return

    # Set cooldown
    if user_id not in RPG_COOLDOWN:
        RPG_COOLDOWN[user_id] = {}
    RPG_COOLDOWN[user_id]["last_rob"] = now

    # Check target coins
    target_coins = target_user["coins"]
    if target_coins < 100:
        await message.reply_text("❌ This user is too poor to be robbed!")
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

        await message.reply_text(
            f"🚨 **ROBBERY FAILED!** 🚨\n\n"
            f"You were caught by the city guards!\n"
            f"💸 You paid a penalty of **{penalty}** coins to **{target.first_name}**!"
        )
    else:
        # Success: Steal 10% - 30% of target coins
        percent = random.randint(10, 30)
        stolen = int(target_coins * (percent / 100))

        async with get_db() as db:
            await db.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (stolen, user_id))
            await db.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (stolen, target.id))
            await db.commit()

        await message.reply_text(
            f"💰 **HEIST SUCCESSFUL!** 💰\n\n"
            f"You sneaked behind **{target.first_name}** and successfully stole **{stolen}** coins ({percent}%)!"
        )

@Client.on_message(dynamic_command("kill"))
async def kill_command(client: Client, message: Message):
    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Must reply to someone
    if not message.reply_to_message:
        await message.reply_text("❌ You must reply to a user's message to execute `/kill`!")
        return

    target = message.reply_to_message.from_user
    if target.id == user_id:
        await message.reply_text("❌ You cannot kill yourself!")
        return

    target_user = await create_or_get_user(target.id, target.username, target.first_name)

    # Check cooldown
    now = int(time.time())
    cooldown_time = 600  # 10 minutes kill cooldown
    last_kill = RPG_COOLDOWN.get(user_id, {}).get("last_kill", 0)
    if (now - last_kill) < cooldown_time:
        time_left = cooldown_time - (now - last_kill)
        await message.reply_text(f"⏱️ **Assassination on Cooldown!**\nYou must wait {time_left} more seconds before trying again.")
        return

    # Check protection shield
    shield_time = target_user["is_protected_until"] or 0
    if shield_time > now:
        await message.reply_text(f"🛡️ **Attack Blocked!**\n**{target.first_name}** has an active protective shield! Your attack bounced back.")
        return

    # Check if already dead
    dead_time = target_user["is_dead_until"] or 0
    if dead_time > now:
        await message.reply_text(f"💀 **Dead Already!**\n**{target.first_name}** is already in the afterlife.")
        return

    # Cost/requirement for assassination
    assassination_cost = 500
    if user["coins"] < assassination_cost:
        await message.reply_text(f"❌ Planning an assassination requires at least {assassination_cost} coins!")
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

        await message.reply_text(
            f"💀 **ASSASSINATION SUCCESSFUL!** 💀\n\n"
            f"You successfully assassinated **{target.first_name}**!\n"
            f"🔥 **Stolen:** {stolen_coins} coins & {stolen_xp} XP!\n"
            f"🎯 Target status set to **DEAD** for 2 hours. Your Kill Count increased!"
        )
    else:
        # Fail: Robber dies instead (set dead for 1 hour)
        death_duration = 3600  # 1 hour
        async with get_db() as db:
            await db.execute("UPDATE users SET is_dead_until = ? WHERE id = ?", (now + death_duration, user_id))
            await db.commit()

        await message.reply_text(
            f"🚨 **ASSASSINATION BOTCHED!** 🚨\n\n"
            f"The target's guards overpowered you and retaliated!\n"
            f"💀 **You have been KILLED** instead and are dead for 1 hour!"
        )

@Client.on_message(dynamic_command("protect"))
async def protect_command(client: Client, message: Message):
    user_id = message.from_user.id
    user = await create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    # Usage: /protect <days> (1 or 2 days)
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/protect <1 or 2>` (in days)")
        return

    days_str = message.command[1]
    if days_str not in ["1", "2"]:
        await message.reply_text("❌ You can only purchase a protective shield for 1 or 2 days!")
        return

    days = int(days_str)
    cost = days * 1500  # 1500 per day

    if user["coins"] < cost:
        await message.reply_text(f"❌ You need at least {cost} coins to purchase a {days}-day shield!")
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

    await message.reply_text(
        f"🛡️ **SHIELD ACTIVATED!** 🛡️\n\n"
        f"You successfully purchased a **{days}-day protective shield** for {cost} coins!\n"
        f"This blocks all /rob and /kill attempts."
    )
