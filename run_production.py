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
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, BotCommand
import uvicorn

# Явно загружаем .env только если запущено локально (не в Cloud Run)
# Cloud Run использует environment variables из service configuration
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
from src.config import get_config
from src.bot.handlers import start_handler, client_handler
from src.web.app import create_app

# Глобальные объекты
bot: Bot = None
dp: Dispatcher = None
webhook_url: str = None
_webhook_setup_done = False


async def setup_webhook():
    """Setup webhook - вызывается при первом запросе или при старте"""
    global bot, webhook_url, _webhook_setup_done
    
    if _webhook_setup_done:
        return
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "my_chat_member"]
        )
        logger.info(f"✅ Webhook установлен: {webhook_url}")
        
        # Установка команд
        await bot.set_my_commands([
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="help", description="Справка"),
        ])
        logger.info("✅ Бот готов к работе")
        _webhook_setup_done = True
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")


def main():
    """Main function"""
    global bot, dp, webhook_url
    
    try:
        # Загружаем конфиг
        config = get_config()
        logger.info("✅ Конфигурация загружена")
        logger.info(f"   Spreadsheet ID: {config.google_spreadsheet_id[:20]}...")
        logger.info(f"   OpenAI Assistant: {config.openai_assistant_id}")
        
        # Инициализация бота
        storage = MemoryStorage()
        bot = Bot(token=config.telegram_bot_token)
        dp = Dispatcher(storage=storage)
        
        # Регистрация обработчиков
        logger.warning("⚠️  REGISTERING HANDLERS...")
        try:
            dp.include_router(start_handler.router)
            logger.warning("⚠️  start_handler.router registered")
        except Exception as e:
            logger.error(f"❌ Failed to register start_handler: {e}")
        
        try:
            dp.include_router(client_handler.router)
            logger.warning("⚠️  client_handler.router registered")
        except Exception as e:
            logger.error(f"❌ Failed to register client_handler: {e}")
        
        logger.info("✅ Обработчики зарегистрированы")
        
        # Создание FastAPI приложения с админ панелью
        app = create_app()
        
        # Webhook endpoint для Telegram
        webhook_path = os.getenv('WEBHOOK_PATH', '/webhook/telegram')
        
        # Запуск сервера
        port = int(os.getenv('PORT', 8080))
        
        # Получаем корректный URL для Cloud Run
        if os.getenv('K_SERVICE'):  # Мы в Cloud Run
            # Cloud Run автоматически устанавливает эти переменные
            service_name = os.getenv('K_SERVICE', 'tattoo-bot')
            region = os.getenv('CLOUD_RUN_REGION', 'us-central1')
            project = os.getenv('GCLOUD_PROJECT', 'tattoo-480007')
            service_url = f"https://{service_name}-408800151466.{region}.run.app"
        else:
            service_url = os.getenv('SERVICE_URL', 'https://localhost:8080')
        
        webhook_url = f"{service_url}{webhook_path}"
        
        @app.on_event("startup")
        async def on_startup():
            """Setup webhook при старте приложения"""
            await setup_webhook()
        
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
