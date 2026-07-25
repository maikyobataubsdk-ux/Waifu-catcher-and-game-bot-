import os

# Telegram API Configuration credentials
# Can be set via environment or default placeholder
API_ID = int(os.environ.get("TELEGRAM_API_ID", "1234567"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "abcdef1234567890abcdef1234567890")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")

# Application Configuration
DATABASE_PATH = os.environ.get("DATABASE_PATH", "bot_database.db")
SPAWN_INTERVAL = int(os.environ.get("SPAWN_INTERVAL", "100"))
