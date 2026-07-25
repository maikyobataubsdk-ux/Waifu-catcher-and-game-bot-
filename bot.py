import asyncio
import logging
from pyrogram import Client
from database import init_db
import config

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Pyrogram Bot Client
bot = Client(
    "welora_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="modules")
)

async def main():
    logger.info("Initializing SQLite database...")
    await init_db()

    logger.info("Starting Welora Gacha, RPG & Economy Bot...")
    await bot.start()

    logger.info("Bot is now online and active!")
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down bot. Goodbye!")
