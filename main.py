import logging
import sys
from src.config import get_config
from src.channels.telegram_bot import setup_application

# Configure clean logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("RemoteDevBridge")


def main():
    print("=" * 60)
    print("        RemoteDevBridge - Remote AI Coding Bridge")
    print("=" * 60)

    try:
        config = get_config()
    except Exception as e:
        logger.error(f"Configuration Initialization Failed: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(config.projects)} project(s) from projects.json")
    logger.info(f"Active AI Engine: {config.ai_engine}")
    logger.info(f"Desktop IDE Launcher: {config.ide_command}")
    logger.info(f"Authorized Telegram Users: {len(config.allowed_user_ids)} registered ID(s)")
    logger.info("Initializing Telegram Bot...")

    try:
        app = setup_application(config)
        logger.info("Bot is polling for updates... Press Ctrl+C to stop.")
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("RemoteDevBridge shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error during bot runtime: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
