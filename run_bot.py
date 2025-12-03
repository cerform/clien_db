#!/usr/bin/env python3
"""
Telegram Bot для Тату-Салона
Запуск бота (совместимо с aiogram 2.15)
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main bot function"""
    try:
        from aiogram import Bot, Dispatcher, types, executor
        from aiogram.contrib.fsm_storage.memory import MemoryStorage
        from aiogram.types import ParseMode
        
        # Получить токен из .env
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден в .env файле")
            print("📝 Перейди на https://t.me/BotFather и создай нового бота")
            return
        
        print("✅ Токен найден")
        
        # Инициализация бота и диспетчера
        bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)
        
        # Базовый обработчик /start
        @dp.message_handler(commands=['start'])
        async def cmd_start(message: types.Message):
            """Handle /start command"""
            user_name = message.from_user.first_name or "пользователь"
            await message.reply(
                f"👋 Привет, {user_name}!\n\n"
                f"🤖 Бот для тату-салона запущен.\n\n"
                f"📋 Доступные команды:\n"
                f"/help - Справка\n"
                f"/about - О боте"
            )
            logger.info(f"User {message.from_user.id} started bot")
        
        @dp.message_handler(commands=['help'])
        async def cmd_help(message: types.Message):
            """Handle /help command"""
            await message.reply(
                "📋 Доступные команды:\n"
                "/start - Главное меню\n"
                "/help - Эта справка\n"
                "/about - О боте"
            )
        
        @dp.message_handler(commands=['about'])
        async def cmd_about(message: types.Message):
            """Handle /about command"""
            await message.reply(
                "🤖 Telegram Bot для Тату-Салона\n"
                "Версия: 1.0.0\n"
                "Фреймворк: aiogram 2.15\n\n"
                "Функции:\n"
                "✅ Запись на услуги\n"
                "✅ Просмотр мастеров\n"
                "✅ Управление расписанием\n"
                "✅ Административная панель"
            )
        
        @dp.message_handler()
        async def echo(message: types.Message):
            """Echo handler"""
            await message.reply(
                f"📨 Вы написали: {message.text}\n\n"
                f"Полная функциональность бота будет доступна после настройки базы данных и Google API."
            )
        
        # Установка команд
        await bot.set_my_commands([
            types.BotCommand("start", "Главное меню"),
            types.BotCommand("help", "Справка"),
            types.BotCommand("about", "О боте"),
        ])
        
        print("🚀 Бот запущен успешно!")
        print("📌 Нажмите Ctrl+C для остановки\n")
        
        # Запуск бота
        await executor.start_polling(dp, skip_updates=True)
        
    except ModuleNotFoundError as e:
        print(f"❌ Ошибка: Не найден модуль {e}")
        print("Установите зависимости: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен")
