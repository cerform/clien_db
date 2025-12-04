#!/usr/bin/env python3
"""
Telegram Bot для Cloud Run (aiogram 3.x)
Запуск бота с HTTP сервером для health checks
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from aiohttp import web

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорт aiogram 3.x
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message

# HTTP сервер для Cloud Run health checks
async def health_check(request):
    """Health check endpoint"""
    return web.Response(text='Bot is running OK', status=200)

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
    # Запуск HTTP сервера для Cloud Run
    logger.info("Starting HTTP server...")
    web_runner = await start_web_server()
    
    # Получить токен
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found")
        return
    
    logger.info("Bot token found, initializing bot...")
    
    # Инициализация бота и диспетчера (aiogram 3.x)
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    
    # Обработчик команды /start
    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        user_name = message.from_user.first_name or "пользователь"
        await message.reply(
            f"👋 Привет, {user_name}!\n\n"
            f"🤖 Бот для тату-салона работает на Cloud Run 24/7.\n\n"
            f"📋 Доступные команды:\n"
            f"/help - Справка\n"
            f"/about - О боте\n"
            f"/status - Статус бота"
        )
        logger.info(f"User {message.from_user.id} ({user_name}) started bot")
    
    # Обработчик команды /help
    @dp.message(Command("help"))
    async def cmd_help(message: Message):
        await message.reply(
            "📋 Справка по командам:\n\n"
            "/start - Главное меню\n"
            "/help - Эта справка\n"
            "/about - О боте\n"
            "/status - Проверить статус бота"
        )
    
    # Обработчик команды /about
    @dp.message(Command("about"))
    async def cmd_about(message: Message):
        await message.reply(
            "🤖 <b>Telegram Bot для Тату-Салона</b>\n\n"
            "📊 <b>Технические детали:</b>\n"
            "• Версия: 1.0.0\n"
            "• Framework: aiogram 3.22.0\n"
            "• Platform: Google Cloud Run\n"
            "• Uptime: 24/7\n\n"
            "✨ <b>Функции:</b>\n"
            "✅ Запись на услуги\n"
            "✅ Просмотр мастеров\n"
            "✅ Управление расписанием\n"
            "✅ Административная панель",
            parse_mode="HTML"
        )
    
    # Обработчик команды /status
    @dp.message(Command("status"))
    async def cmd_status(message: Message):
        await message.reply(
            "✅ <b>Статус бота:</b> ОНЛАЙН\n"
            "🌐 Платформа: Google Cloud Run\n"
            "⏰ Режим работы: 24/7\n"
            "💚 Все системы работают нормально!",
            parse_mode="HTML"
        )
    
    # Обработчик всех текстовых сообщений
    @dp.message(F.text)
    async def echo(message: Message):
        await message.reply(
            f"📨 Вы написали: <code>{message.text}</code>\n\n"
            f"Бот работает на Cloud Run 24/7!\n"
            f"Используйте /help для списка команд.",
            parse_mode="HTML"
        )
    
    # Установка команд в меню бота
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Главное меню"),
        types.BotCommand(command="help", description="Справка"),
        types.BotCommand(command="about", description="О боте"),
        types.BotCommand(command="status", description="Статус бота"),
    ])
    
    logger.info("Bot commands set successfully")
    logger.info("Starting bot polling...")
    
    try:
        # Запуск polling (aiogram 3.x)
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Error in polling: {e}", exc_info=True)
    finally:
        await bot.session.close()
        await web_runner.cleanup()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
