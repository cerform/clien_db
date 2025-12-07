#!/usr/bin/env python3
"""
Production Telegram Bot для Cloud Run с WEBHOOK
Полная интеграция: INKA AI + Google Sheets + Advanced функции
"""

import asyncio
import logging
import os
import sys
from aiohttp import web
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv

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

# Aiogram 3.x
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import BotCommand

# Наши модули
from src.config import get_config
from src.bot.handlers import start_handler, client_handler

# Глобальные объекты
bot = None
dp = None


async def run_app(app, port, webhook_url):
    """Запуск приложения с использованием AppRunner"""
    global bot
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✅ Server is listening on 0.0.0.0:{port}")
    logger.info("✅ Server is ready to receive messages (webhook setup is background task)")
    
    # Устанавливаем webhook в фоне (не блокируем стартап)
    async def setup_webhook_background():
        """Setup webhook в фоне, чтобы не задерживать стартап"""
        await asyncio.sleep(2)  # Даём серверу время на полную инициализацию
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query", "my_chat_member"]
            )
            logger.info(f"✅ Webhook установлен: {webhook_url}")
            
            # Установка команд
            from aiogram.types import BotCommand
            await bot.set_my_commands([
                BotCommand(command="start", description="Главное меню"),
                BotCommand(command="help", description="Справка"),
            ])
            logger.info("✅ Бот готов к работе")
        except Exception as e:
            logger.error(f"❌ Ошибка установки webhook: {e}")
    
    # Запускаем setup в фоне
    asyncio.create_task(setup_webhook_background())
    
    # Держим сервер запущенным
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except:
            pass
        await bot.session.close()
        await runner.cleanup()


def main():
    """Main function"""
    global bot, dp
    
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
        
        # Создание веб-приложения
        app = web.Application()
        
        # Health check endpoint
        async def health(request):
            return web.Response(text='Bot OK', status=200)
        
        app.router.add_get('/health', health)
        app.router.add_get('/', health)
        
        # Webhook endpoint
        webhook_path = os.getenv('WEBHOOK_PATH', '/webhook')
        
        # Добавляем middleware для логирования всех webhook запросов
        original_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        
        async def webhook_middleware(request):
            logger.warning(f"⚠️  WEBHOOK REQUEST: {request.method} {request.path}")
            logger.warning(f"    Content-Type: {request.content_type}")
            try:
                body = await request.text()
                logger.warning(f"    Body: {body[:200]}")
            except:
                pass
            return await original_handler.handle(request)
        
        original_handler.register(app, path=webhook_path)
        logger.warning(f"⚠️  Webhook handler registered at {webhook_path}")
        
        # Setup application
        setup_application(app, dp, bot=bot)
        
        # Запуск сервера
        port = int(os.getenv('PORT', 8080))
        
        # Получаем корректный URL для Cloud Run
        if os.getenv('K_SERVICE'):  # Мы в Cloud Run
            # Cloud Run автоматически устанавливает эти переменные
            service_name = os.getenv('K_SERVICE', 'tattoo-bot')
            region = os.getenv('CLOUD_RUN_REGION', 'europe-west6')
            project = os.getenv('GCLOUD_PROJECT', 'tattoo-480007')
            service_url = f"https://{service_name}-408800151466.{region}.run.app"
        else:
            service_url = os.getenv('SERVICE_URL', 'https://tattoo-bot-408800151466.europe-west6.run.app')
        
        webhook_url = f"{service_url}{webhook_path}"
        
        logger.info(f"🚀 Starting webhook server on port {port}")
        logger.info(f"   Webhook URL: {webhook_url}")
        
        # Используем AppRunner для корректного запуска
        asyncio.run(run_app(app, port, webhook_url))
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
