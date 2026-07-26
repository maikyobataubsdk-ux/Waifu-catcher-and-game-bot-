# 💖 Welora: Anime Waifu Gacha, RPG & Economy Bot 💖

Welcome to **Welora**, a multi-tenant, feature-rich Telegram Bot combining **Anime Waifu Gacha**, **RPG Guild Combat & Protection**, and a fully simulated dynamic **Economy System** using Pyrogram, Pillow (for stunning on-the-fly image rendering), and SQLite database storage.

This repository is built with high code quality, complete unit tests, and fully structured deployment steps to help you get the bot live easily and error-free!

---

## 📖 Table of Contents
1. [🌟 Features](#-features)
2. [⚙️ Environment Variables](#️-environment-variables)
3. [🚀 Quickstart & Setup Guide](#-quickstart--setup-guide)
4. [🎮 All Commands & How to Play](#-all-commands--how-to-play)
   - [General Commands](#general-commands)
   - [Economy & Gifts](#economy--gifts)
   - [Waifu & Gacha Catching](#waifu--gacha-catching)
   - [RPG, Combat & Protection](#rpg-combat--protection)
   - [Group Moderation & Admin Control](#group-moderation--admin-control)
5. [🧪 Testing & Verification](#-testing--verification)

---

## 🌟 Features

*   **Multi-Tenant Economy:** Each chat group can customize their experience. Users earn coins (Zexis), gems, and experience points (XP).
*   **Stunning Pillow Image Cards:**
    *   **Interactive Stats Cards (`/bal`):** Dynamic gradient styling showing your statistics, ranking, kills, and a visual experience progress bar.
    *   **Group Welcome Banners:** Automatically generates unique cards when the bot or new members join.
    *   **Character Spawn Cards:** Drop custom character graphics with rarity accents into group chats.
*   **Dynamic Command Prefixes:** Groups can set their own command prefix (e.g., `!`, `$`, `.`, `/`) using `/setgroup prefix <char>`.
*   **Auto Gacha Character Spawns:** Periodically triggers waifu/character spawns in group chats as people chat (controlled by message thresholds).
*   **Combat RPG & Theft:** Rob (`/rob`) or assassinate (`/kill`) other users, or purchase shield items (`/protect`) to stay safe.
*   **Mini-Games:** Rocket/Crash game (`/rocket`) and Word Scrabble (`/scrabble`) with direct in-chat answer detection.
*   **Elegant Text Rendering:** Dynamic elegant small-caps formatting for users!

---

## ⚙️ Environment Variables

These variables configure how your bot connects to Telegram and where it saves files. You can set them in your terminal environment or in a `.env` file (copied from `.env.example`):

| Variable Name | Required | Default Value | Description |
| :--- | :---: | :---: | :--- |
| `TELEGRAM_API_ID` | Yes | - | Your Telegram API ID from [my.telegram.org](https://my.telegram.org). |
| `TELEGRAM_API_HASH` | Yes | - | Your Telegram API HASH. |
| `TELEGRAM_BOT_TOKEN` | Yes | - | Bot Token received from [@BotFather](https://t.me/BotFather). |
| `DATABASE_PATH` | No | `bot_database.db` | The path to the SQLite3 database file. |
| `SPAWN_INTERVAL` | No | `100` | Number of messages required to spawn a random character in a group chat. |

---

## 🚀 Quickstart & Setup Guide

Getting Welora up and running is extremely fast and simple.

### Step 1: Install Dependencies
Run the following command to install all the required Python packages:
```bash
pip install -r requirements.txt
```

### Step 2: Run the Bot
Set your environment variables (or save them inside a `.env` file) and start the bot:
```bash
python3 bot.py
```

That's it! The bot is now live and will initialize the local SQLite database automatically.

---

## 🎮 All Commands & How to Play

Every command uses the dynamically configured group prefix (Default is `/`).

### General Commands

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/start` | `/start` | Initializes your profile, greets you, and explains game controls. |
| `/help` | `/help` | Displays help menu with instructions. |
| `/game` | `/game` | Opens the dashboard with interactive rules cards (via Telegram Inline Buttons). |

---

### Economy & Gifts

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/bal` | `/bal` (or reply to a user) | Generates and sends your personal custom **Stats Card Image** with coins, gems, rank, and XP. |
| `/daily` | `/daily` | Claims your daily rewards (starts at 2000 coins + streak bonuses!). |
| `/pay` | Reply to a user with `/pay <amount>` | Transfers a specified amount of coins securely to another player. |
| `/gift` | Reply with `/gift <character_name>` | Gifts one of your owned harem characters to another user. |

---

### Waifu & Gacha Catching

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/grasp` or `/claim` | `/grasp` or `/claim` | Claims the active spawned waifu character in the current group. |
| `/harem` | `/harem` (or reply to view others) | Opens your character collection book page-by-page using inline pagination. |
| `/marry` | `/marry <character_name>` | Marries a character inside your harem collection permanently. |
| `/propose` | Reply to a user with `/propose` | Proposes a lifetime virtual marriage bond to another user in the group. |
| `/explore` | `/explore` | Spends 200 coins to explore the wild forest and find characters manually (50% success rate!). |

---

### RPG, Combat & Protection

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/rob` | Reply to a target with `/rob` | Attempts to steal 10% - 30% of target user's wallet. Has a 40% chance of failing, resulting in paying penalty. |
| `/kill` | Reply to a target with `/kill` | Spends 500 coins to attempt an assassination. Success (50%) steals 25% XP, 15% coins, sets target status to dead. Failure kills the attacker. |
| `/protect` | `/protect <days>` | Purchase a protective shield for 1 or 2 days (1500 coins per day) to block all attacks & thefts. |

---

### Group Moderation & Admin Control

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/setgroup` | `/setgroup <setting> <value>` | Main control unit for Bot Admins or global Top 5 Richest users. |

#### Admin Subsettings available:
*   **Change Custom Prefix:**
    `/setgroup prefix !` (Changes group command trigger to `!`)
*   **Toggle Toxic Message Auto-Deletion Filter:**
    `/setgroup toxicity 1` (Enables toxicity block) or `/setgroup toxicity 0` (Disables toxicity block)
*   **Toggle NSFW Filter:**
    `/setgroup nsfw 1` (Enables NSFW words cleanup) or `/setgroup nsfw 0`
*   **Set Group Welcome Message:**
    `/setgroup welcome Welcome {name} to our magical guild!` (Use `{name}` as user placeholder)

---

## 🧪 Testing & Verification

To guarantee that the codebase remains fully functional and error-free, a set of unit tests using `pytest` is included.

Run all tests instantly with the following command:
```bash
python3 -m pytest tests/
```

All 15 integrated tests cover database creation, user storage, balancing transactions, gacha claiming, custom group configurations, and combat modules.

---
Enjoy building your own ultimate Waifu RPG & Economy community on Telegram! For questions, open a pull request or contact your system administrator. 💖
