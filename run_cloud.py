#!/usr/bin/env python3
"""
Telegram Bot для Cloud Run
Запуск бота с HTTP сервером для health checks
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from aiohttp import web
import sys

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# HTTP сервер для Cloud Run health checks
async def health_check(request):
    """Health check endpoint"""
    return web.Response(text='OK', status=200)

async def start_web_server():
    """Start web server for Cloud Run"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.getenv('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP server started on port {port}")
    return runner

async def main():
    """Main function"""
    try:
        # Запуск HTTP сервера для Cloud Run
        logger.info("Starting HTTP server...")
        web_runner = await start_web_server()
        
        logger.info("HTTP server started, keeping it running...")
        
        # Запуск Telegram бота в фоне
        from aiogram import Bot, Dispatcher, types
        from aiogram.contrib.fsm_storage.memory import MemoryStorage
        from aiogram.types import ParseMode
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not found")
            return
        
        logger.info("Bot token found, initializing bot...")
        
        bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)
        
        # Обработчики
        @dp.message_handler(commands=['start'])
        async def cmd_start(message: types.Message):
            user_name = message.from_user.first_name or "пользователь"
            await message.reply(
                f"👋 Привет, {user_name}!\n\n"
                f"🤖 Бот для тату-салона работает на Cloud Run 24/7.\n\n"
                f"📋 Доступные команды:\n"
                f"/help - Справка\n"
                f"/about - О боте"
            )
            logger.info(f"User {message.from_user.id} started bot")
        
        @dp.message_handler(commands=['help'])
        async def cmd_help(message: types.Message):
            await message.reply(
                "📋 Доступные команды:\n"
                "/start - Главное меню\n"
                "/help - Эта справка\n"
                "/about - О боте"
            )
        
        @dp.message_handler(commands=['about'])
        async def cmd_about(message: types.Message):
            await message.reply(
                "🤖 Telegram Bot для Тату-Салона\n"
                "Версия: 1.0.0\n"
                "Platform: Google Cloud Run 24/7\n\n"
                "Функции:\n"
                "✅ Запись на услуги\n"
                "✅ Просмотр мастеров\n"
                "✅ Управление расписанием\n"
                "✅ Административная панель"
            )
        
        @dp.message_handler()
        async def echo(message: types.Message):
            await message.reply(
                f"📨 Вы написали: {message.text}\n\n"
                f"Бот работает на Cloud Run 24/7!"
            )
        
        # Установка команд
        await bot.set_my_commands([
            types.BotCommand("start", "Главное меню"),
            types.BotCommand("help", "Справка"),
            types.BotCommand("about", "О боте"),
        ])
        
        logger.info("Starting bot polling...")
        await dp.start_polling()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
