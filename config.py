import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Telegram API Configuration credentials
# Can be set via environment or default placeholder
API_ID = int(os.environ.get("TELEGRAM_API_ID", "37729457"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "bb68973b7efcbbd074cda984c95502d6")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")

# Application Configuration
DATABASE_PATH = os.environ.get("DATABASE_PATH", "bot_database.db")
SPAWN_INTERVAL = int(os.environ.get("SPAWN_INTERVAL", "100"))

# Bot Administrators configuration
raw_admin_ids = os.environ.get("BOT_ADMIN_IDS", "7777777,9999999")
BOT_ADMIN_IDS = [int(x.strip()) for x in raw_admin_ids.split(",") if x.strip().isdigit()]
if not BOT_ADMIN_IDS:
    BOT_ADMIN_IDS = [7777777, 9999999]
