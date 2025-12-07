#!/usr/bin/env python3
"""
☁️ CLOUD RUN ENTRYPOINT
Запуск бота в Cloud Run без интерактивного меню
Конфигурация загружается из переменных окружения и Secrets Manager
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.logging_config import setup_logging
from src.config import get_config
from src.bot.loader import init_bot, get_dispatcher
from src.bot.handlers import start_handler, client_handler, master_handler
from src.bot.handlers import admin_panel_text, debug_handler
from src.services.admin_db_manager import DatabaseManager, InkaLearningSystem
from aiogram import Dispatcher, Router
from aiogram.types import BotCommand

# Setup logging
logger = logging.getLogger(__name__)
setup_logging()


async def setup_bot_commands(dispatcher: Dispatcher):
    """Setup bot commands in Telegram"""
    commands = [
        BotCommand(command="start", description="🤖 Главное меню"),
        BotCommand(command="book", description="📅 Записаться на процедуру"),
        BotCommand(command="cancel", description="❌ Отменить запись"),
        BotCommand(command="help", description="❓ Справка"),
        BotCommand(command="admin", description="👨‍💼 Админ-панель"),
        BotCommand(command="debug_config", description="🔍 Диагностика (админ)"),
    ]
    
    # Get bot instance and set commands
    bot = dispatcher.bot
    await bot.set_my_commands(commands)
    logger.info(f"✅ Bot commands set: {len(commands)} commands")


async def main():
    """Main entry point for Cloud Run"""
    logger.info("="*70)
    logger.info("🚀 STARTING INKA BOT FOR CLOUD RUN")
    logger.info("="*70)
    
    try:
        # Load configuration from environment
        logger.info("📋 Loading configuration...")
        config = get_config()
        logger.info(f"✅ Configuration loaded")
        logger.info(f"   • Spreadsheet: {config.google_spreadsheet_id[:20]}...")
        logger.info(f"   • Calendar: {config.google_calendar_id[:20] if config.google_calendar_id else 'NOT SET'}...")
        logger.info(f"   • Admin IDs: {config.admin_ids}")
        logger.info(f"   • Timezone: {config.timezone}")
        
        # Initialize bot
        logger.info("🤖 Initializing Telegram bot...")
        bot = init_bot(config.telegram_bot_token)
        logger.info("✅ Bot initialized")
        
        # Get dispatcher
        logger.info("📡 Setting up dispatcher...")
        dp = get_dispatcher()
        
        # Setup routers
        main_router = Router()
        
        # Include all handlers
        main_router.include_router(start_handler.router)
        main_router.include_router(client_handler.router)
        main_router.include_router(master_handler.router)
        main_router.include_router(admin_panel_text.router)
        main_router.include_router(debug_handler.router)
        
        # Initialize admin services
        logger.info("🔧 Initializing admin services...")
        db_manager = DatabaseManager()
        learning_system = InkaLearningSystem()
        admin_panel_text.init_admin_handler(db_manager, learning_system)
        logger.info("✅ Admin services initialized")
        
        # Include main router
        dp.include_router(main_router)
        
        # Setup bot commands
        await setup_bot_commands(dp)
        
        # Register startup/shutdown handlers
        @dp.startup()
        async def on_startup():
            logger.info("🟢 Bot startup - webhook should be handling requests")
        
        @dp.shutdown()
        async def on_shutdown():
            logger.info("🔴 Bot shutdown")
        
        logger.info("="*70)
        logger.info("✅ BOT READY - Waiting for webhook updates...")
        logger.info("="*70)
        
        # Start polling (in Cloud Run, webhook handles updates instead)
        # This keeps the process alive for Cloud Run
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)
