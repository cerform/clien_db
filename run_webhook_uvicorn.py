"""
Headless запуск FastAPI webhook-сервера для Cloud Run с Telegram Bot интеграцией.
"""
import os
import sys
import asyncio
import logging
from typing import Dict
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загружаем .env только если запущено локально (не в Cloud Run)
env_path = Path(__file__).parent / ".env"
if os.getenv("K_SERVICE") is None:  # K_SERVICE есть только в Cloud Run
    load_dotenv(env_path)

# Наши модули
from src.config import get_config
from src.bot.handlers import client_handler
from src.web.app import create_app

# Глобальные объекты
bot: Bot = None
dp: Dispatcher = None
webhook_url: str = None
_webhook_setup_done = False

async def setup_webhook():
    """Setup webhook - вызывается при старте"""
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
        
        # Удаляем команды бота (без кнопки Старт)
        await bot.delete_my_commands()
        logger.info("✅ Бот готов к работе (без команд/кнопок)")
        _webhook_setup_done = True
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")

if __name__ == "__main__":
    try:
        # Загружаем конфиг
        config = get_config()
        logger.info("✅ Конфигурация загружена")
        
        # Инициализация бота
        storage = MemoryStorage()
        bot = Bot(token=config.telegram_bot_token)
        dp = Dispatcher(storage=storage)
        
        # Регистрация обработчиков
        logger.info("⚠️  Регистрация обработчиков...")
        try:
            dp.include_router(client_handler.router)
            logger.info("✅ client_handler.router зарегистрирован")
        except Exception as e:
            logger.error(f"❌ Ошибка регистрации client_handler: {e}")
        
        # Создание FastAPI приложения
        app = create_app()
        
        # Webhook endpoint для Telegram
        webhook_path = os.getenv('WEBHOOK_PATH', '/webhook/telegram')
        
        # Получаем корректный URL для Cloud Run
        if os.getenv('K_SERVICE'):  # Мы в Cloud Run
            service_name = os.getenv('K_SERVICE', 'tattoo-bot')
            region = os.getenv('CLOUD_RUN_REGION', 'us-central1')
            service_url = f"https://{service_name}-408800151466.{region}.run.app"
        else:
            service_url = os.getenv('SERVICE_URL', 'http://localhost:8080')
        
        webhook_url = f"{service_url}{webhook_path}"
        
        @app.on_event("startup")
        async def on_startup():
            """Setup webhook при старте приложения"""
            logger.info("🚀 Приложение запускается...")
            await setup_webhook()
        
        @app.post(webhook_path)
        async def telegram_webhook(update: Dict):
            """Telegram webhook endpoint"""
            try:
                update_obj = Update(**update)
                await dp.feed_update(bot=bot, update=update_obj)
                return {"ok": True}
            except Exception as e:
                logger.error(f"❌ Webhook error: {e}", exc_info=True)
                return {"ok": False, "error": str(e)}
        
        logger.info(f"✅ Webhook endpoint зарегистрирован: {webhook_path}")
        
        # Запуск сервера
        port = int(os.getenv("PORT", 8080))
        host = os.getenv("HOST", "0.0.0.0")
        
        logger.info(f"🚀 Запуск FastAPI сервера на {host}:{port}")
        logger.info(f"   Webhook URL: {webhook_url}")
        logger.info(f"   Admin Panel: {service_url}")
        
        uvicorn.run(app, host=host, port=port, log_level="info")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}", exc_info=True)
        sys.exit(1)
