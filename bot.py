import asyncio
import logging
from pyrogram import Client
from pyrogram.types import BotCommand
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

    logger.info("Registering bot commands...")
    try:
        commands = [
            BotCommand("start", "Start the bot and get instructions / बोट शुरू करें"),
            BotCommand("help", "Get help menu with all commands / मदद मेनू"),
            BotCommand("game", "Open interactive games dashboard and rules / गेम डैशबोर्ड"),
            BotCommand("bal", "Check profile balance & stats card / अपना बैलेंस देखें"),
            BotCommand("daily", "Claim daily rewards & streak bonuses / दैनिक इनाम"),
            BotCommand("pay", "Transfer coins to another user (reply with amount) / सिक्के भेजें"),
            BotCommand("gift", "Gift a harem character to another user / वाइफू गिफ्ट करें"),
            BotCommand("grasp", "Claim the active spawned character / वाइफू पकड़ें"),
            BotCommand("claim", "Claim the active spawned character / वाइफू पकड़ें"),
            BotCommand("harem", "Open and browse your character collection / अपना हरेम देखें"),
            BotCommand("marry", "Marry a character in your harem / वाइफू से शादी करें"),
            BotCommand("propose", "Propose virtual marriage to a user / शादी का प्रस्ताव"),
            BotCommand("explore", "Explore wild forest to find characters / वाइफू की खोज"),
            BotCommand("rob", "Attempt to steal coins from a user / चोरी का प्रयास"),
            BotCommand("kill", "Attempt to assassinate a user / हमला करें"),
            BotCommand("protect", "Purchase a protective shield / सुरक्षा कवच खरीदें"),
            BotCommand("setgroup", "Configure custom prefix & group settings / ग्रुप सेटिंग्स"),
        ]
        await bot.set_bot_commands(commands)
        logger.info("Successfully registered all bot commands!")
    except Exception as e:
        logger.error(f"Failed to register bot commands: {e}")

    logger.info("Bot is now online and active!")
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down bot. Goodbye!")
