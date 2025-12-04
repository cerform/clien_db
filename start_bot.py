#!/usr/bin/env python3
"""
Простой запуск Telegram бота (aiogram 3.x)
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция"""
    
    # Получение токена
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        return
    
    logger.info("✅ Токен найден, инициализация бота...")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    
    # Обработчик команды /start
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        """Обработка команды /start"""
        user_name = message.from_user.first_name or "пользователь"
        await message.answer(
            f"👋 Привет, {user_name}!\n\n"
            f"🤖 Я бот тату-салона {os.getenv('SALON_NAME', 'Tattoo Salon')}\n\n"
            f"Доступные команды:\n"
            f"/start - Главное меню\n"
            f"/help - Помощь\n\n"
            f"✨ Бот работает и готов к использованию!"
        )
    
    # Обработчик команды /help
    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        """Обработка команды /help"""
        await message.answer(
            "ℹ️ Справка:\n\n"
            "Этот бот помогает управлять записями в тату-салоне.\n\n"
            "📋 Команды:\n"
            "/start - Начать работу\n"
            "/help - Эта справка\n\n"
            "💡 Для полной функциональности настройте интеграцию с Google Sheets"
        )
    
    # Обработчик всех остальных сообщений
    @dp.message()
    async def echo_message(message: types.Message):
        """Обработка текстовых сообщений"""
        await message.answer(
            f"Вы написали: {message.text}\n\n"
            f"Используйте /help для списка команд"
        )
    
    # Запуск бота
    try:
        logger.info("🚀 Бот запущен!")
        logger.info("=" * 50)
        me = await bot.get_me()
        logger.info(f"Bot ID: {me.id}")
        logger.info(f"Bot Username: @{me.username}")
        logger.info(f"Bot Name: {me.first_name}")
        logger.info("=" * 50)
        logger.info("Нажмите Ctrl+C для остановки")
        logger.info("=" * 50)
        
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("\n👋 Бот остановлен")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Завершение работы...")
