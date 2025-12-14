#!/usr/bin/env python3
"""
Production Telegram Bot для Cloud Run с WEBHOOK
Полная интеграция: INKA AI + Google Sheets + Advanced функции
Использует FastAPI для веб-интерфейса + Aiogram для Telegram webhook
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict
from contextlib import asynccontextmanager

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.utils.token import TokenValidationError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, BotCommand
import uvicorn

# Явно загружаем .env только если запущено локально (не в Cloud Run)
env_path = Path(__file__).parent / ".env"
if os.getenv("K_SERVICE") is None:  # K_SERVICE есть только в Cloud Run
    load_dotenv(env_path)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f"🔧 Загружаю переменные окружения")
logger.info(f"🔧 ADMIN_IDS: {os.getenv('ADMIN_IDS', 'не установлено')}")
logger.info(f"🔧 OPENAI_API_KEY: {'установлен' if os.getenv('OPENAI_API_KEY') else 'не установлен'}")

# Наши модули
from src.config.config import Config
from src.bot.handlers import inka_handler  # INKA AI dialog system
from src.web.app import create_app
from src.db.cloudsql_client import init_cloudsql_client
from src.db.repositories.admin_messages_repo import AdminMessagesRepo

# Глобальные объекты
bot: Bot = None
dp: Dispatcher = None
webhook_url: str = None
_webhook_setup_done = False
admin_messages_repo = None


def get_admin_messages_repo():
    """Get global admin messages repository instance"""
    return admin_messages_repo

async def setup_webhook():
    """Setup webhook - вызывается при первом запросе или при старте"""
    global bot, webhook_url, _webhook_setup_done

    if _webhook_setup_done:
        return
    # If bot is not configured (invalid or missing token) skip webhook setup
    if bot is None:
        logger.warning("⚠️ Bot not configured or token invalid; skipping webhook setup")
        _webhook_setup_done = True
        return

    try:
        # Get webhook secret for validation
        webhook_secret = os.getenv("WEBHOOK_SECRET", "")

        await bot.delete_webhook(drop_pending_updates=True)

        # Set webhook with secret token for security
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "my_chat_member"],
            secret_token=webhook_secret if webhook_secret else None
        )
        logger.info(f"✅ Webhook установлен: {webhook_url}")
        if webhook_secret:
            logger.info("✅ Webhook secret token configured for security")
        else:
            logger.warning("⚠️ No WEBHOOK_SECRET configured - webhook is less secure")

        # Удаляем команды бота (без кнопки Старт)
        await bot.delete_my_commands()
        logger.info("✅ Бот готов к работе (без команд/кнопок)")
        _webhook_setup_done = True
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")


def main():
    """Main function"""
    global bot, dp, webhook_url, admin_messages_repo

    try:
        # Initialize Cloud SQL connection first (used by DB init)
        try:
            cloudsql_client = init_cloudsql_client()
            if cloudsql_client.test_connection():
                admin_messages_repo = AdminMessagesRepo(cloudsql_client.get_engine())
                logger.info("✅ Cloud SQL connected successfully")
            else:
                logger.warning("⚠️ Cloud SQL connection test failed, running without database")
        except Exception as e:
            logger.warning(f"⚠️ Cloud SQL initialization failed: {e}, running without database")

        # Initialize PostgreSQL database schema (now Cloud SQL client is available)
        try:
            from src.db.init_postgres import init_database
            if init_database():
                logger.info("✅ PostgreSQL schema initialized")
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL schema init failed: {e}")

        # Загружаем конфиг и проверяем необходимые параметры
        config = Config.from_env()
        try:
            config.validate()
        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            sys.exit(2)
        logger.info("✅ Конфигурация загружена")
        logger.info(f"   BOT_TOKEN: {'установлен' if config.BOT_TOKEN else 'отсутствует'}")
        logger.info(f"   OPENAI_API_KEY: {'установлен' if config.OPENAI_API_KEY else 'отсутствует'}")
        
        # Инициализация бота — не прерываем запуск приложения, если токен неверен
        storage = MemoryStorage()
        try:
            bot = Bot(token=config.BOT_TOKEN)
            dp = Dispatcher(storage=storage)
        except TokenValidationError as e:
            logger.error(f"❌ Bot token invalid; running in web-only mode: {e}")
            bot = None
            dp = Dispatcher(storage=storage)
        
        # Register handlers based on BOT_MODE. Default to INKA-only for safety.
        bot_mode = os.getenv('BOT_MODE', 'inka').lower()
        logger.info(f"🔧 BOT_MODE: {bot_mode}")
        if bot_mode == 'advanced':
            # Register AI handler if explicitly required and configured
            try:
                from src.bot.handlers import ai_handler
                logger.info("🔧 Registering AI handler (advanced LLM flow) ...")
                ai_router = ai_handler.create_ai_router()
                dp.include_router(ai_router)
                logger.info("✅ AI Handler registered - advanced LLM flow")
            except Exception as e:
                logger.error(f"❌ Failed to register AI handler: {e}")
                logger.exception("Full error:")
                raise
        else:
            # Default behavior: register INKA only
            logger.info("🔧 Registering INKA handler (rule-based / LLM if configured) ...")
            try:
                inka_router = inka_handler.create_inka_router()
                dp.include_router(inka_router)
                logger.info("✅ INKA Handler registered - unified assistant (S1/S2)")
            except Exception as e:
                logger.error(f"❌ Failed to register INKA handler: {e}")
                logger.exception("Full error:")
                raise

        logger.info("✅ All handlers registered (INKA is active)")
        
        # Создание FastAPI приложения с админ панелью
        app = create_app()
        
        # Webhook endpoint для Telegram
        webhook_path = os.getenv('WEBHOOK_PATH', '/webhook/telegram')
        
        # Запуск сервера
        port = int(os.getenv('PORT', 8080))
        
        # Получаем корректный URL для Cloud Run
        if os.getenv('K_SERVICE'):  # Мы в Cloud Run
            # Try to get URL from Cloud Run environment variables (most reliable)
            # Cloud Run provides the full service URL via metadata or can be constructed
            service_url = os.getenv('SERVICE_URL')

            if not service_url:
                # Fallback: try to get from Google metadata server
                try:
                    import requests
                    metadata_url = 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/service-url'
                    headers = {'Metadata-Flavor': 'Google'}
                    response = requests.get(metadata_url, headers=headers, timeout=2)
                    if response.status_code == 200:
                        service_url = response.text.strip()
                except Exception:
                    pass

            if not service_url:
                # Final fallback: construct from K_SERVICE (but this is not guaranteed format)
                # Note: Cloud Run URLs use format: https://<service>-<hash>-<region>.a.run.app
                # Since we don't have hash, we use service name only (works for custom domains)
                service_name = os.getenv('K_SERVICE', 'tattoo-bot')
                # User should set SERVICE_URL env var in Cloud Run for production
                service_url = f"https://{service_name}.run.app"
                logger.warning(f"⚠️ SERVICE_URL not set, using fallback: {service_url}")
                logger.warning("⚠️ Set SERVICE_URL environment variable in Cloud Run for correct webhook URL")
        else:
            service_url = os.getenv('SERVICE_URL', 'http://localhost:8080')
        
        webhook_url = f"{service_url}{webhook_path}"
        
        @app.on_event("startup")
        async def on_startup():
            """Приложение готово - webhook можно настроить через /api/setup-webhook"""
            logger.info("✅ FastAPI started, ready to accept requests")
            logger.info(f"   Call POST {service_url}/api/setup-webhook to configure Telegram webhook")
        
        @app.post("/api/setup-webhook")
        async def setup_webhook_endpoint():
            """Endpoint to setup Telegram webhook - call this after deployment"""
            try:
                await setup_webhook()
                return {"ok": True, "message": f"Webhook configured: {webhook_url}"}
            except Exception as e:
                logger.error(f"Failed to setup webhook: {e}", exc_info=True)
                return {"ok": False, "error": str(e)}

        @app.post(webhook_path)
        async def telegram_webhook(update: Dict):
            """Telegram webhook endpoint"""
            try:
                update_obj = Update(**update)
                await dp.feed_update(bot=bot, update=update_obj)
                return {"ok": True}
            except Exception as e:
                logger.error(f"Webhook error: {e}", exc_info=True)
                return {"ok": False, "error": str(e)}

        # Also accept the alternate webhook path that some deploy scripts use (/telegram/webhook)
        try:
            app.post("/telegram/webhook")(telegram_webhook)
            logger.info("✅ Alias webhook path /telegram/webhook registered")
        except Exception:
            logger.warning("⚠️ Failed to register alias webhook path /telegram/webhook")
        
        logger.warning(f"⚠️  Webhook handler registered at {webhook_path}")
        
        logger.info(f"🚀 Starting FastAPI server on port {port}")
        logger.info(f"   Webhook URL: {webhook_url}")
        logger.info(f"   Admin Panel: {service_url}")
        logger.info(f"   API Health: {service_url}/api/health")
        
        # Запуск сервера Uvicorn с FastAPI
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
