# 💖 Welora: Anime Waifu Gacha, RPG & Economy Bot 💖

Welcome to **Welora**, a multi-tenant, feature-rich Telegram Bot combining **Anime Waifu Gacha**, **RPG Guild Combat & Protection**, and a fully simulated dynamic **Economy System** using Pyrogram, Pillow (for stunning on-the-fly image rendering), and SQLite database storage.

This repository is built with high code quality, complete unit tests, and fully structured deployment steps to help you get the bot live easily and error-free!

---

## 📖 Table of Contents (अनुक्रमणिका)
1. [🌟 Features (विशेषताएं)](#-features-विशेषताएं)
2. [⚙️ Environment Variables (पर्यावरण चर)](#️-environment-variables-पर्यावरण-चर)
3. [🚀 Deployment & Setup Guides (डेवलपमेंट और सेटअप गाइड)](#-deployment--setup-guides-डेवलपमेंट-और-सेटअप-गाइड)
   - [Method 1: Local / VPS Run (Python)](#method-1-local--vps-run-python)
   - [Method 2: PM2 Process Manager (Recommended for VPS)](#method-2-pm2-process-manager-recommended-for-vps)
   - [Method 3: Docker Deployment (Fast & Clean Containerized Setup)](#method-3-docker-deployment-fast--clean-containerized-setup)
   - [Method 4: Systemd Service (VPS Run in Background)](#method-4-systemd-service-vps-run-in-background)
4. [🎮 All Commands & How to Play (सभी कमांड्स और कैसे खेलें)](#-all-commands--how-to-play-सभी-कमांड्स-और-कैसे-खेलें)
   - [General Commands](#general-commands)
   - [Economy & Gifts](#economy--gifts)
   - [Waifu & Gacha Catching](#waifu--gacha-catching)
   - [RPG, Combat & Protection](#rpg-combat--protection)
   - [Group Moderation & Admin Control](#group-moderation--admin-control)
5. [🧪 Testing & Verification (परीक्षण और सत्यापन)](#-testing--verification-परीक्षण-और-सत्यापन)

---

## 🌟 Features (विशेषताएं)

*   **Multi-Tenant Economy:** Each chat group can customize their experience. Users earn coins (Zexis), gems, and experience points (XP).
*   **Stunning Pillow Image Cards:**
    *   **Interactive Stats Cards (`/bal`):** Dynamic gradient styling showing your statistics, ranking, kills, and a visual experience progress bar.
    *   **Group Welcome Banners:** Automatically generates unique cards when the bot or new members join.
    *   **Character Spawn Cards:** Drop custom character graphics with rarity accents into group chats.
*   **Dynamic Command Prefixes:** Groups can set their own command prefix (e.g., `!`, `$`, `.`, `/`) using `/setgroup prefix <char>`.
*   **Auto Gacha Character Spawns:** Periodically triggers waifu/character spawns in group chats as people chat (controlled by message thresholds).
*   **Combat RPG & Theft:** Rob (`/rob`) or assassinate (`/kill`) other users, or purchase shield items (`/protect`) to stay safe.
*   **Mini-Games:** Rocket/Crash game (`/rocket`) and Word Scrabble (`/scrabble`) with direct in-chat answer detection.
*   **Bilingual Text Rendering:** Dynamic elegant small-caps formatting in Hindi-English representation for users!

---

## ⚙️ Environment Variables (पर्यावरण चर)

These variables configure how your bot connects to Telegram and where it saves files. You can set them in your terminal environment or in a `.env` file:

| Variable Name | Required | Default Value | Description |
| :--- | :---: | :---: | :--- |
| `TELEGRAM_API_ID` | Yes | - | Your Telegram API ID from [my.telegram.org](https://my.telegram.org). |
| `TELEGRAM_API_HASH` | Yes | - | Your Telegram API HASH. |
| `TELEGRAM_BOT_TOKEN` | Yes | - | Bot Token received from [@BotFather](https://t.me/BotFather). |
| `DATABASE_PATH` | No | `bot_database.db` | The path to the SQLite3 database file. |
| `SPAWN_INTERVAL` | No | `100` | Number of messages required to spawn a random character in a group chat. |

---

## 🚀 Deployment & Setup Guides (डेवलपमेंट और सेटअप गाइड)

Here are four solid methods to deploy your bot, making it completely error-free and continuous.

### Method 1: Local / VPS Run (Python)

Ensure Python 3.10+ and `pip` are installed on your machine.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Waifu-catcher-and-game-bot-.git
   cd Waifu-catcher-and-game-bot-
   ```

2. **Install system dependencies (needed for image rendering on Linux/Ubuntu):**
   ```bash
   sudo apt-get update
   sudo apt-get install -y build-essential libffi-dev libssl-dev fonts-dejavu-core
   ```

3. **Install python packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Export your variables and start the bot:**
   *On Linux/MacOS:*
   ```bash
   export TELEGRAM_API_ID="your_api_id"
   export TELEGRAM_API_HASH="your_api_hash"
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   python bot.py
   ```
   *On Windows (CMD):*
   ```cmd
   set TELEGRAM_API_ID=your_api_id
   set TELEGRAM_API_HASH=your_api_hash
   set TELEGRAM_BOT_TOKEN=your_bot_token
   python bot.py
   ```

---

### Method 2: PM2 Process Manager (Recommended for VPS)

PM2 is extremely helpful to ensure that the bot restarts automatically if it crashes or the server reboots.

1. **Install Node.js & PM2 on your server:**
   ```bash
   sudo apt update && sudo apt install -y nodejs npm
   sudo npm install -g pm2
   ```

2. **Create a PM2 start script `ecosystem.config.js` or start directly:**
   ```bash
   pm2 start bot.py --name "welora_bot" --interpreter python3 --env TELEGRAM_API_ID="your_id" --env TELEGRAM_API_HASH="your_hash" --env TELEGRAM_BOT_TOKEN="your_token"
   ```

3. **Save process list and set up startup hook:**
   ```bash
   pm2 save
   pm2 startup
   ```

---

### Method 3: Docker Deployment (Fast & Clean Containerized Setup)

Docker allows you to run the bot cleanly inside an isolated container with zero environmental installation issues!

1. **Build the Docker container:**
   ```bash
   docker build -t welora-bot .
   ```

2. **Run the container with your Telegram tokens:**
   ```bash
   docker run -d \
     --name welora_bot_container \
     -e TELEGRAM_API_ID="your_api_id" \
     -e TELEGRAM_API_HASH="your_api_hash" \
     -e TELEGRAM_BOT_TOKEN="your_bot_token" \
     -v $(pwd)/bot_database.db:/app/bot_database.db \
     --restart always \
     welora-bot
   ```

#### Alternatively, use **Docker Compose**:
1. Open the pre-configured `docker-compose.yml` file and edit your tokens.
2. Run:
   ```bash
   docker-compose up -d
   ```
3. Check status:
   ```bash
   docker-compose ps
   ```

---

### Method 4: Systemd Service (VPS Run in Background)

Create a persistent service on Linux systems to manage background execution automatically.

1. **Create the service file:**
   ```bash
   sudo nano /etc/systemd/system/welora.service
   ```

2. **Paste the following configuration (Update paths accordingly):**
   ```ini
   [Unit]
   Description=Welora Telegram Gacha and RPG Bot
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/Waifu-catcher-and-game-bot-
   Environment=TELEGRAM_API_ID=your_api_id
   Environment=TELEGRAM_API_HASH=your_api_hash
   Environment=TELEGRAM_BOT_TOKEN=your_bot_token
   ExecStart=/usr/bin/python3 bot.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. **Reload systemctl daemon, start the service, and enable on boot:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start welora
   sudo systemctl enable welora
   ```

4. **Verify live logs:**
   ```bash
   sudo journalctl -u welora -f
   ```

---

## 🎮 All Commands & How to Play (सभी कमांड्स और कैसे खेलें)

Every command uses the dynamically configured group prefix (Default is `/`).

### General Commands

| Command | Usage | Description | Hindi / Hinglish translation |
| :--- | :--- | :--- | :--- |
| `/start` | `/start` | Initializes your profile, greets you and explains game controls. | बोट को शुरू करता है, आपका प्रोफाइल बनाता है और खेलने के नियम बताता है। |
| `/help` | `/help` | Displays help menu with instructions. | मदद मेनू खोलता है और सारी जानकारी देता है। |
| `/game` | `/game` | Opens the dashboard with interactive rules cards (via Telegram Inline Buttons). | गेम डैशबोर्ड और रूल्स कार्ड को इनलाइन बटन्स के साथ खोलता है। |

---

### Economy & Gifts

| Command | Usage | Description | Hindi / Hinglish translation |
| :--- | :--- | :--- | :--- |
| `/bal` | `/bal` (or reply to a user) | Generates and sends your personal custom **Stats Card Image** with coins, gems, rank, and XP. | आपकी सुंदर **Stats Card Photo** भेजता है जिसमें आपके सिक्के, रत्न, रैंक और अनुभव (XP) दिखाई देते हैं। |
| `/daily` | `/daily` | Claims your daily rewards (starts at 2000 coins + streak bonuses!). | दैनिक इनाम (2000+ सिक्के और XP) पाने के लिए रोजाना इस कमांड का उपयोग करें। |
| `/pay` | Reply to a user with `/pay <amount>` | Transfers a specified amount of coins securely to another player. | किसी अन्य खिलाड़ी को सुरक्षित रूप से सिक्के ट्रांसफर करने के लिए उनके मैसेज पर रिप्लाई करें। |
| `/gift` | Reply with `/gift <character_name>` | Gifts one of your owned harem characters to another user. | अपने हरेम (Harem) के किसी कैरेक्टर को अपने दोस्त को तोहफे में देने के लिए इस्तेमाल करें। |

---

### Waifu & Gacha Catching

| Command | Usage | Description | Hindi / Hinglish translation |
| :--- | :--- | :--- | :--- |
| `/grasp` or `/claim` | `/grasp` or `/claim` | Claims the active spawned waifu character in the current group. | ग्रुप में स्पॉन हुई कैरेक्टर (Waifu) को अपने हरेम में पकड़ने के लिए इस कमांड का तुरंत प्रयोग करें। |
| `/harem` | `/harem` (or reply to view others) | Opens your character collection book page-by-page using inline pagination. | आपके द्वारा पकड़ी गयी सभी वाइफू (Collection) की सूची को पन्नों की तरह बटन के साथ खोलता है। |
| `/marry` | `/marry <character_name>` | Marries a character inside your harem collection permanently. | अपने हरेम में मौजूद किसी कैरेक्टर से आधिकारिक रूप से विवाह करने के लिए इस्तेमाल करें। |
| `/propose` | Reply to a user with `/propose` | Proposes a lifetime virtual marriage bond to another user in the group. | ग्रुप के किसी दूसरे खिलाड़ी को शादी का प्रस्ताव (Proposal) भेजने के लिए रिप्लाई करें। |
| `/explore` | `/explore` | Spends 200 coins to explore the wild forest and find characters manually (50% success rate!). | २०० सिक्के खर्च करके जंगल में नई वाइफू की खोज करें। ५०% मौका सफल होने का है! |

---

### RPG, Combat & Protection

| Command | Usage | Description | Hindi / Hinglish translation |
| :--- | :--- | :--- | :--- |
| `/rob` | Reply to a target with `/rob` | Attempts to steal 10% - 30% of target user's wallet. Has a 40% chance of failing, resulting in paying penalty. | किसी दूसरे यूजर के सिक्के चुराने की कोशिश करें (चोरी सफल होने पर सिक्के मिलेंगे, पकड़े जाने पर जुर्माना देना होगा)। |
| `/kill` | Reply to a target with `/kill` | Spends 500 coins to attempt an assassination. Success (50%) steals 25% XP, 15% coins, sets target status to dead. Failure kills the attacker. | ५०० सिक्के देकर टारगेट पर हमला करें। सफल होने पर २५% XP और १५% सिक्के मिलेंगे और वो २ घंटे के लिए मृत घोषित हो जायेगा। |
| `/protect` | `/protect <days>` | Purchase a protective shield for 1 or 2 days (1500 coins per day) to block all attacks & thefts. | १ या २ दिनों के लिए सुरक्षा कवच (Shield) खरीदें ताकि कोई आपको लूट न सके और न ही मार सके। |

---

### Group Moderation & Admin Control

| Command | Usage | Description | Hindi / Hinglish translation |
| :--- | :--- | :--- | :--- |
| `/setgroup` | `/setgroup <setting> <value>` | Main control unit for Bot Admins or global Top 5 Richest users. | ग्रुप सेटिंग्स बदलने के लिए एडमिन या टॉप ५ अमीर खिलाड़ी इस कमांड का उपयोग कर सकते हैं। |

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

## 🧪 Testing & Verification (परीक्षण और सत्यापन)

To guarantee that the codebase remains fully functional and error-free, a set of unit tests using `pytest` is included.

Run all tests instantly with the following command:
```bash
python3 -m pytest tests/
```

All 15 integrated tests cover database creation, user storage, balancing transactions, gacha claiming, custom group configurations, and combat modules.

---
Enjoy building your own ultimate Waifu RPG & Economy community on Telegram! For questions, open a pull request or contact your system administrator. 💖
