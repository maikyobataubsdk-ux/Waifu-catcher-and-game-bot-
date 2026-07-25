import io
import os
import time
import random
import math
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import (
    get_db, create_or_get_user, get_group_settings, update_user_balance, dynamic_command
)
from utils.images import generate_spawn_card, to_small_caps

# Global spawn lock / tracker to simulate Redis caching behavior
SPAWN_TRACKER = {}

async def trigger_spawn(client: Client, chat_id: int):
    async with get_db() as db:
        async with db.execute("SELECT * FROM waifus ORDER BY RANDOM() LIMIT 1") as cursor:
            waifu = await cursor.fetchone()
            if not waifu:
                return

            # Store active spawn
            now = int(time.time())
            await db.execute(
                "INSERT OR REPLACE INTO active_spawns (chat_id, waifu_id, spawned_at) VALUES (?, ?, ?)",
                (chat_id, waifu["id"], now)
            )
            await db.commit()

            # Text formatting
            rarity_emoji = {
                "Common": "⚪",
                "Rare": "🔵",
                "Epic": "🟣",
                "Legendary": "🟡",
                "Velora": "🌟"
            }.get(waifu["rarity"], "❓")

            title = to_small_caps("A wild character has spawned!")
            lbl_name = to_small_caps("Name:")
            lbl_rarity = to_small_caps("Rarity:")
            lbl_value = to_small_caps("Value:")
            lbl_how = to_small_caps("Type /grasp or /claim to claim this character!")

            caption = (
                f"🚨 **{title}** 🚨\n\n"
                f"🌸 **{lbl_name}** {waifu['name']}\n"
                f"✨ **{lbl_rarity}** {rarity_emoji} {waifu['rarity']}\n"
                f"💰 **{lbl_value}** {waifu['price']} coins\n\n"
                f"{lbl_how}"
            )

            # Generate waifu card dynamically with PIL and send it
            try:
                card_bytes = generate_spawn_card(waifu["name"], waifu["rarity"], waifu["price"])
                bio = io.BytesIO(card_bytes)
                bio.name = f"spawn_{waifu['id']}.png"
                await client.send_photo(chat_id, bio, caption=caption)
            except Exception:
                # Fallback to plain text message
                try:
                    await client.send_message(chat_id, caption)
                except Exception:
                    pass

# Auto-spawn decorator/handler
@Client.on_message(filters.group & ~filters.service & ~filters.bot)
async def auto_spawn_handler(client: Client, message: Message):
    chat_id = message.chat.id

    # Exclude command messages from count
    text = message.text or ""
    settings = await get_group_settings(chat_id)
    prefix = settings["custom_prefix"] if settings else "/"
    if text.startswith("/") or text.startswith(prefix):
        return

    if chat_id not in SPAWN_TRACKER:
        SPAWN_TRACKER[chat_id] = {"counter": 0}

    SPAWN_TRACKER[chat_id]["counter"] += 1

    # Auto-spawn every 100 messages (configurable via test or environment)
    spawn_interval = int(os.environ.get("SPAWN_INTERVAL", "100"))
    if SPAWN_TRACKER[chat_id]["counter"] >= spawn_interval:
        SPAWN_TRACKER[chat_id]["counter"] = 0
        await trigger_spawn(client, chat_id)

@Client.on_message(dynamic_command(["grasp", "claim"]))
async def grasp_command(client: Client, message: Message):
    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or "unnamed"
    first_name = message.from_user.first_name or "User"

    # Get user profile
    await create_or_get_user(user_id, username, first_name)

    async with get_db() as db:
        # Check active spawn
        async with db.execute("""
            SELECT s.waifu_id, w.name, w.rarity, w.price
            FROM active_spawns s
            JOIN waifus w ON s.waifu_id = w.id
            WHERE s.chat_id = ?
        """, (chat_id,)) as cursor:
            spawn = await cursor.fetchone()
            if not spawn:
                err = to_small_caps("There is no active character to claim in this group!")
                await message.reply_text(f"❌ {err}")
                return

            waifu_id = spawn["waifu_id"]
            name = spawn["name"]
            rarity = spawn["rarity"]

            # Add to harem
            try:
                await db.execute(
                    "INSERT INTO user_harems (user_id, waifu_id) VALUES (?, ?)",
                    (user_id, waifu_id)
                )
                await db.execute("DELETE FROM active_spawns WHERE chat_id = ?", (chat_id,))
                await db.commit()

                # Reward user with some XP for catch
                await update_user_balance(user_id, xp_delta=50)
                title = to_small_caps(f"Congratulations {first_name}!")
                desc = to_small_caps(f"You have successfully claimed {name} ({rarity})!")
                added = to_small_caps("She has been added to your /harem! (+50 XP)")
                await message.reply_text(
                    f"🎉 **{title}**\n"
                    f"{desc}\n"
                    f"{added}"
                )
            except Exception:
                await db.rollback()
                err = to_small_caps("You already have this character in your harem!")
                await message.reply_text(f"❌ {err}")

@Client.on_message(dynamic_command("harem"))
async def harem_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"

    # Check if target user profile was requested via reply
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        first_name = message.reply_to_message.from_user.first_name or "User"

    await create_or_get_user(user_id)

    async with get_db() as db:
        async with db.execute("""
            SELECT w.id, w.name, w.rarity, w.price, h.married_at
            FROM user_harems h
            JOIN waifus w ON h.waifu_id = w.id
            WHERE h.user_id = ?
            ORDER BY w.id ASC
        """, (user_id,)) as cursor:
            harems = await cursor.fetchall()

    if not harems:
        err = to_small_caps(f"{first_name} has no characters in their harem yet!")
        await message.reply_text(f"🌸 **{err}**")
        return

    # Render page 1
    total = len(harems)
    pages = math.ceil(total / 5)

    title = to_small_caps(f"{first_name}'s Collection (Total: {total})")
    text = f"🌸 **{title}** 🌸\n\n"
    for i, w in enumerate(harems[:5]):
        status = f" 💍 [{to_small_caps('MARRIED')}]" if w["married_at"] > 0 else ""
        text += f"{i+1}. **{w['name']}** - {w['rarity']} ({w['price']} coins){status}\n"

    lbl_page = to_small_caps("Page")
    lbl_of = to_small_caps("of")
    text += f"\n{lbl_page} **1** {lbl_of} **{pages}**"

    buttons = []
    if pages > 1:
        btn_next = to_small_caps("Next")
        buttons.append([
            InlineKeyboardButton(f"{btn_next} ➡️", callback_data=f"harem_{user_id}_2")
        ])

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)

# Harem callback pagination
@Client.on_callback_query(filters.regex(r"^harem_(\d+)_(\d+)$"))
async def harem_pagination(client: Client, callback_query: CallbackQuery):
    owner_id = int(callback_query.matches[0].group(1))
    page = int(callback_query.matches[0].group(2))

    async with get_db() as db:
        # Get owner details
        async with db.execute("SELECT first_name FROM users WHERE id = ?", (owner_id,)) as cursor:
            owner = await cursor.fetchone()
            first_name = owner["first_name"] if owner else "User"

        async with db.execute("""
            SELECT w.id, w.name, w.rarity, w.price, h.married_at
            FROM user_harems h
            JOIN waifus w ON h.waifu_id = w.id
            WHERE h.user_id = ?
            ORDER BY w.id ASC
        """, (owner_id,)) as cursor:
            harems = await cursor.fetchall()

    total = len(harems)
    pages = math.ceil(total / 5)

    if page < 1 or page > pages:
        err = to_small_caps("No more pages available!")
        await callback_query.answer(err, show_alert=True)
        return

    start_idx = (page - 1) * 5
    end_idx = start_idx + 5

    title = to_small_caps(f"{first_name}'s Collection (Total: {total})")
    text = f"🌸 **{title}** 🌸\n\n"
    for i, w in enumerate(harems[start_idx:end_idx]):
        status = f" 💍 [{to_small_caps('MARRIED')}]" if w["married_at"] > 0 else ""
        text += f"{start_idx+i+1}. **{w['name']}** - {w['rarity']} ({w['price']} coins){status}\n"

    lbl_page = to_small_caps("Page")
    lbl_of = to_small_caps("of")
    text += f"\n{lbl_page} **{page}** {lbl_of} **{pages}**"

    row = []
    if page > 1:
        btn_prev = to_small_caps("Prev")
        row.append(InlineKeyboardButton(f"⬅️ {btn_prev}", callback_data=f"harem_{owner_id}_{page-1}"))
    if page < pages:
        btn_next = to_small_caps("Next")
        row.append(InlineKeyboardButton(f"{btn_next} ➡️", callback_data=f"harem_{owner_id}_{page+1}"))

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([row]) if row else None
    )

@Client.on_message(dynamic_command("marry"))
async def marry_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    await create_or_get_user(user_id)

    # Expecting /marry <Waifu Name>
    if len(message.command) < 2:
        usage = to_small_caps("Usage: /marry <waifu name>")
        await message.reply_text(f"❌ {usage}")
        return

    waifu_name = " ".join(message.command[1:]).strip()

    async with get_db() as db:
        # Check if the user owns this waifu
        async with db.execute("""
            SELECT w.id, w.name, h.married_at
            FROM user_harems h
            JOIN waifus w ON h.waifu_id = w.id
            WHERE h.user_id = ? AND LOWER(w.name) = LOWER(?)
        """, (user_id, waifu_name)) as cursor:
            waifu = await cursor.fetchone()

            if not waifu:
                err = to_small_caps("You do not have this character in your harem!")
                await message.reply_text(f"❌ {err}")
                return

            if waifu["married_at"] > 0:
                err = to_small_caps(f"You are already married to {waifu['name']}!")
                await message.reply_text(f"💍 {err}")
                return

            # Perform marriage
            now = int(time.time())
            await db.execute("""
                UPDATE user_harems
                SET married_at = ?
                WHERE user_id = ? AND waifu_id = ?
            """, (now, user_id, waifu["id"]))
            await db.commit()

            title = to_small_caps("Marriage Bond Created!")
            desc = to_small_caps(f"Congratulations! You are now married to {waifu['name']}!")
            added = to_small_caps("A beautiful addition to your collection!")
            await message.reply_text(
                f"💍 **{title}** 💍\n\n"
                f"{desc}\n"
                f"{added}"
            )

# Propose mechanics between two users
@Client.on_message(dynamic_command("propose"))
async def propose_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    username = message.from_user.username or "unnamed"
    first_name = message.from_user.first_name or "User"

    await create_or_get_user(user_id, username, first_name)

    # Must reply to someone
    if not message.reply_to_message or not message.reply_to_message.from_user:
        err = to_small_caps("You must reply to the user you want to propose to!")
        await message.reply_text(f"❌ {err}")
        return

    target_user = message.reply_to_message.from_user
    if target_user.id == user_id:
        err = to_small_caps("You cannot propose to yourself!")
        await message.reply_text(f"❌ {err}")
        return

    await create_or_get_user(target_user.id, target_user.username, target_user.first_name)

    async with get_db() as db:
        # Verify if either user is already married
        async with db.execute("""
            SELECT * FROM user_marriages
            WHERE user_one_id = ? OR user_two_id = ? OR user_one_id = ? OR user_two_id = ?
        """, (user_id, user_id, target_user.id, target_user.id)) as cursor:
            existing = await cursor.fetchone()
            if existing:
                err = to_small_caps("One of you is already in a marriage bond!")
                await message.reply_text(f"❌ {err}")
                return

    # Create interactive inline-keyboard
    btn_accept = to_small_caps("Accept Propose")
    btn_reject = to_small_caps("Reject")
    buttons = [
        [
            InlineKeyboardButton(f"💍 {btn_accept}", callback_data=f"propose_accept_{user_id}_{target_user.id}"),
            InlineKeyboardButton(f"❌ {btn_reject}", callback_data=f"propose_reject_{user_id}_{target_user.id}")
        ]
    ]

    title = to_small_caps("Proposal in the Air!")
    desc = to_small_caps(f"has proposed to")
    question = to_small_caps("Do you accept this lifetime bond?")
    await message.reply_text(
        f"💖 **{title}** 💖\n\n"
        f"🌸 **{first_name}** {desc} **{target_user.first_name}**!\n"
        f"{question}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^propose_(accept|reject)_(\d+)_(\d+)$"))
async def propose_callback(client: Client, callback_query: CallbackQuery):
    action = callback_query.matches[0].group(1)
    proposer_id = int(callback_query.matches[0].group(2))
    proposed_id = int(callback_query.matches[0].group(3))

    if callback_query.from_user.id != proposed_id:
        err = to_small_caps("Only the proposed user can reply!")
        await callback_query.answer(err, show_alert=True)
        return

    async with get_db() as db:
        if action == "reject":
            desc = to_small_caps("The marriage proposal was rejected. Heartbroken! 💔")
            await callback_query.message.edit_text(f"❌ {desc}")
            return

        # Check marriage existence once again
        async with db.execute("""
            SELECT * FROM user_marriages
            WHERE user_one_id = ? OR user_two_id = ? OR user_one_id = ? OR user_two_id = ?
        """, (proposer_id, proposer_id, proposed_id, proposed_id)) as cursor:
            existing = await cursor.fetchone()
            if existing:
                err = to_small_caps("Propose failed. One of you is already married!")
                await callback_query.message.edit_text(f"❌ {err}")
                return

        # Commit marriage
        now = int(time.time())
        await db.execute(
            "INSERT INTO user_marriages (user_one_id, user_two_id, married_at) VALUES (?, ?, ?)",
            (proposer_id, proposed_id, now)
        )
        await db.commit()

        # Get users profiles names
        async with db.execute("SELECT first_name FROM users WHERE id = ?", (proposer_id,)) as c1:
            p1 = await c1.fetchone()
        async with db.execute("SELECT first_name FROM users WHERE id = ?", (proposed_id,)) as c2:
            p2 = await c2.fetchone()

        n1 = p1["first_name"] if p1 else "User"
        n2 = p2["first_name"] if p2 else "User"

        title = to_small_caps("Congratulations!")
        desc = to_small_caps(f"and {n2} are now officially married!")
        wish = to_small_caps("May their love and virtual wealth flourish together! 💖")
        await callback_query.message.edit_text(
            f"🎉 **{title}** 🎉\n\n"
            f"💍 **{n1}** {desc}\n"
            f"{wish}"
        )

# Explore command
@Client.on_message(dynamic_command("explore"))
async def explore_command(client: Client, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    user = await create_or_get_user(user_id)

    coins = user["coins"]
    cost = 200  # Small manual exploration fee
    if coins < cost:
        err = to_small_caps(f"Exploring requires {cost} coins. You currently only have {coins} coins!")
        await message.reply_text(f"❌ {err}")
        return

    # Charge explore fee
    await update_user_balance(user_id, coins_delta=-cost)

    # 50% chance of discovering a waifu
    if random.random() < 0.50:
        async with get_db() as db:
            async with db.execute("SELECT * FROM waifus ORDER BY RANDOM() LIMIT 1") as cursor:
                waifu = await cursor.fetchone()

        if waifu:
            # Check ownership to avoid duplication constraint failures
            async with get_db() as db:
                async with db.execute(
                    "SELECT 1 FROM user_harems WHERE user_id = ? AND waifu_id = ?",
                    (user_id, waifu["id"])
                ) as check:
                    is_owned = await check.fetchone()

            if is_owned:
                desc = to_small_caps(f"You explored the deep mountains and discovered {waifu['name']}!")
                greet = to_small_caps("But wait, you already have her in your harem. She waved hello and left! 👋")
                await message.reply_text(f"🧭 {desc}\n{greet}")
            else:
                async with get_db() as db:
                    await db.execute(
                        "INSERT INTO user_harems (user_id, waifu_id) VALUES (?, ?)",
                        (user_id, waifu["id"])
                    )
                    await db.commit()
                await update_user_balance(user_id, xp_delta=20)
                title = to_small_caps("Exploration Successful!")
                desc = to_small_caps(f"Deep inside the magical forest, you encountered and captured {waifu['name']} ({waifu['rarity']})!")
                added = to_small_caps("She has joined your harem! (+20 XP)")
                await message.reply_text(
                    f"🧭 **{title}** 🧭\n\n"
                    f"{desc}\n"
                    f"{added}"
                )
    else:
        desc = to_small_caps("You explored the surrounding areas but found nothing of interest today...")
        await message.reply_text(f"🧭 {desc}")
