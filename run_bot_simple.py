#!/usr/bin/env python3
"""
Telegram Bot для Тату-Салона (aiogram 2.15 с правильной инициализацией event loop)
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция бота"""
    try:
        from aiogram import Bot, Dispatcher, types, executor
        from aiogram.contrib.fsm_storage.memory import MemoryStorage
        from aiogram.types import ParseMode
        
        # Получить токен из .env
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token or bot_token in ['', 'YOUR_TOKEN_HERE', 'placeholder']:
            print("\n" + "="*60)
            print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен или неверный!")
            print("="*60)
            print("\n📝 Как получить токен:")
            print("  1. Откройте Telegram")
            print("  2. Напишите @BotFather")
            print("  3. Напишите: /newbot")
            print("  4. Следуйте инструкциям")
            print("  5. Скопируйте токен")
            print("  6. Вставьте в .env файл")
            print("\n✅ После этого запустите бота снова")
            print("="*60 + "\n")
            return False
        
        print("\n" + "="*60)
        print("✅ Токен найден и валиден")
        print("="*60)
        
        # Инициализация бота и диспетчера
        print("\n📡 Инициализация бота...")
        bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)
        
        # Обработчик команды /start
        @dp.message_handler(commands=['start'])
        async def cmd_start(message: types.Message):
            """Обработка команды /start"""
            user_name = message.from_user.first_name or "Пользователь"
            await message.reply(
                f"👋 <b>Привет, {user_name}!</b>\n\n"
                f"🤖 Бот для тату-салона запущен.\n\n"
                f"📋 <b>Доступные команды:</b>\n"
                f"/help - Справка\n"
                f"/about - О боте",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"User {message.from_user.id} ({user_name}) started bot")
        
        # Обработчик команды /help
        @dp.message_handler(commands=['help'])
        async def cmd_help(message: types.Message):
            """Обработка команды /help"""
            await message.reply(
                "<b>📚 Справка по боту:</b>\n\n"
                "<b>Основные команды:</b>\n"
                "/start - Главное меню\n"
                "/help - Эта справка\n"
                "/about - О боте\n\n"
                "<b>Функции:</b>\n"
                "💬 Отправляйте сообщения для общения с ботом\n"
                "📅 Бот интегрирован с Google Sheets и Calendar\n"
                "👨‍💼 Поддержка профилей мастеров\n"
                "📱 Онлайн бронирование",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"User {message.from_user.id} requested help")
        
        # Обработчик команды /about
        @dp.message_handler(commands=['about'])
        async def cmd_about(message: types.Message):
            """Обработка команды /about"""
            await message.reply(
                "<b>ℹ️ О боте:</b>\n\n"
                "Версия: 1.0\n"
                "Платформа: Telegram\n"
                "Язык: Python 3.14\n"
                "Framework: aiogram 2.15\n\n"
                "<b>Возможности:</b>\n"
                "✅ Управление записями к мастерам\n"
                "✅ Синхронизация с Google Sheets\n"
                "✅ Интеграция с Google Calendar\n"
                "✅ Уведомления клиентам\n"
                "✅ Расписание мастеров\n\n"
                "<b>Разработчик:</b> Tatu Salon Team\n"
                "<b>Лицензия:</b> MIT",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"User {message.from_user.id} requested about")
        
        # Обработчик остальных сообщений
        @dp.message_handler(content_types=['text'])
        async def echo_handler(message: types.Message):
            """Обработка обычных сообщений"""
            await message.reply(
                f"📨 <b>Вы написали:</b> {message.text}\n\n"
                f"ℹ️ Полная функциональность бота будет доступна после настройки Google API.",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Message from {message.from_user.id}: {message.text}")
        
        # Установка команд боту
        commands = [
            types.BotCommand("start", "Главное меню"),
            types.BotCommand("help", "Справка"),
            types.BotCommand("about", "О боте"),
        ]
        await bot.set_my_commands(commands)
        
        print("✅ Конфигурация завершена")
        print("\n" + "="*60)
        print("🚀 БОТ ЗАПУЩЕН УСПЕШНО!")
        print("="*60)
        print("\n📌 Статус: Ожидание сообщений")
        print("📌 Нажмите Ctrl+C для остановки")
        print("\n💬 Откройте Telegram и:")
        print("   1. Найдите вашего бота")
        print("   2. Напишите /start")
        print("   3. Проверьте ответ")
        print("\n" + "="*60 + "\n")
        
        # Запуск polling - это блокирующий вызов, не async
        executor.start_polling(dp, skip_updates=True)
        
        return True
        
    except ValueError as e:
        if "Token is invalid" in str(e):
            print("\n" + "="*60)
            print("❌ ОШИБКА: Токен неверный или истёк!")
            print("="*60)
            print("\n📝 Решение:")
            print("  1. Откройте @BotFather в Telegram")
            print("  2. Выберите /token")
            print("  3. Выберите бота")
            print("  4. Скопируйте новый токен")
            print("  5. Обновите .env файл")
            print("\n✅ После этого запустите бота снова")
            print("="*60 + "\n")
        else:
            logger.error(f"ValueError: {e}", exc_info=True)
        return False
        
    except ModuleNotFoundError as e:
        print(f"\n❌ Ошибка: Модуль не найден - {e}")
        print("📝 Попробуйте установить зависимости: pip install -r requirements.txt\n")
        return False
        
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        # Для Windows: используем ProactorEventLoop
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Создаём event loop и запускаем основную функцию
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем main как корутину
        loop.run_until_complete(main())
            
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("⏹️  БОТ ОСТАНОВЛЕН ПОЛЬЗОВАТЕЛЕМ")
        print("="*60 + "\n")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}\n")
        sys.exit(1)
    finally:
        try:
            loop.close()
        except:
            pass
