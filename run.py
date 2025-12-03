#!/usr/bin/env python3
"""Bot entrypoint - loads config and starts the bot"""
import sys
import logging
import ssl
import os

# Disable SSL verification for development
os.environ['PYTHONHTTPSVERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context

from src.config.env_loader import load_env
from src.config.config import Config
from src.bot.entrypoint import start_bot
from src.utils.logging_setup import setup_logging

def main():
    """Load environment, setup logging, start bot"""
    try:
        # Load environment variables from .env
        load_env()
        
        # Load configuration
        cfg = Config.from_env()
        
        # Setup logging
        setup_logging(cfg)
        logger = logging.getLogger(__name__)
        
        logger.info("=" * 60)
        logger.info("🤖 Tattoo Appointment Bot Starting")
        logger.info(f"   ENV: {cfg.ENV}")
        logger.info(f"   Mode: {'WEBHOOK' if cfg.USE_WEBHOOK else 'POLLING'}")
        logger.info("=" * 60)
        
        # Validate configuration
        if not cfg.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN not set. Add to .env")
            sys.exit(1)
        if not cfg.SPREADSHEET_ID:
            logger.warning("⚠️ SPREADSHEET_ID not set. Run: python3 create_google_sheets_structure.py")
        
        # Start bot
        start_bot(cfg)
        
    except KeyboardInterrupt:
        logger.info("⚠️ Bot stopped by user")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
