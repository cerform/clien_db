#!/usr/bin/env python3
"""
Telegram Bot для Тату-Салона (aiogram 2.15 с поддержкой LLM)
"""

import logging
import os
import sys
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Инициализация event loop для Windows перед импортом aiogram
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from aiogram import Bot, Dispatcher, types, executor
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    from aiogram.types import ParseMode
    from src.ai.processor import get_ai_processor
    
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
        sys.exit(1)
    
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
        logger.info(f"User {message.from_user.id} requested /help command")
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
        logger.info(f"User {message.from_user.id} received help")
    
    # Обработчик команды /about
    @dp.message_handler(commands=['about'])
    async def cmd_about(message: types.Message):
        """Обработка команды /about"""
        logger.info(f"User {message.from_user.id} requested /about command")
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
        logger.info(f"User {message.from_user.id} received about info")
    
    # Обработчик остальных сообщений (только текст, без команд)
    @dp.message_handler(lambda message: not message.text.startswith('/'), content_types=['text'])
    async def echo_handler(message: types.Message):
        """Обработка обычных сообщений через AI"""
        user_id = message.from_user.id
        user_text = message.text
        
        logger.info(f"Processing message from {user_id}: {user_text}")
        
        # Отправляем уведомление о обработке
        processing_msg = await message.reply(
            "⏳ <b>Обрабатываю ваш запрос...</b>",
            parse_mode=ParseMode.HTML
        )
        
        try:
            # Получаем AI процессор
            ai_processor = get_ai_processor()
            
            # Обработка текста через LLM
            result = await ai_processor.process_message(user_text, user_id)
            
            action = result.get("action", "general_question")
            response = result.get("response", "")
            parameters = result.get("parameters", {})
            
            # Логирование действия
            logger.info(f"User {user_id}: action={action}, params={parameters}")
            
            # Формируем итоговый ответ
            if action == "booking":
                # Запись на процедуру
                response_text = f"📅 <b>Запись на процедуру</b>\n\n{response}\n\n" \
                    f"<b>Параметры:</b>\n" \
                    f"• Дата: {parameters.get('date', 'не указана')}\n" \
                    f"• Время: {parameters.get('time', 'не указано')}\n" \
                    f"• Мастер: {parameters.get('master', 'не указан')}\n" \
                    f"• Процедура: {parameters.get('procedure', 'не указана')}\n\n" \
                    f"Для подтверждения напишите: /confirm"
            
            elif action == "masters_list":
                # Список мастеров
                response_text = f"👨‍💼 <b>Список мастеров</b>\n\n{response}"
            
            elif action == "profile_view":
                # Просмотр профиля
                response_text = f"👤 <b>Профиль мастера</b>\n\n{response}\n\n" \
                    f"Мастер: {parameters.get('master_name', 'не указан')}"
            
            elif action == "cancel_booking":
                # Отмена записи
                response_text = f"❌ <b>Отмена записи</b>\n\n{response}"
            
            elif action == "my_bookings":
                # Мои записи
                response_text = f"📋 <b>Ваши записи</b>\n\n{response}"
            
            else:  # general_question или error
                response_text = response
            
            # Удаляем сообщение о обработке и отправляем ответ
            await processing_msg.delete()
            await message.reply(
                response_text,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await processing_msg.delete()
            await message.reply(
                f"❌ <b>Ошибка обработки:</b>\n{str(e)}\n\n"
                f"<b>Используйте команды:</b>\n"
                f"/start - Главное меню\n"
                f"/help - Справка\n"
                f"/about - О боте",
                parse_mode=ParseMode.HTML
            )
        logger.info(f"Message from {message.from_user.id}: {message.text}")
    
    # Функция для установки команд при запуске
    async def on_startup(dispatcher):
        """Функция, вызываемая при запуске бота"""
        commands = [
            types.BotCommand("start", "Главное меню"),
            types.BotCommand("help", "Справка"),
            types.BotCommand("about", "О боте"),
        ]
        await bot.set_my_commands(commands)
        print("✅ Команды установлены")
    
    # Функция для очистки при завершении
    async def on_shutdown(dispatcher):
        """Функция, вызываемая при остановке бота"""
        await bot.session.close()
        print("\n⏹️  Бот остановлен")
    
    if __name__ == '__main__':
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
        
        # Создаём event loop явно
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Установка команд при запуске бота
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            loop=loop
        )
    
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
    sys.exit(1)
    
except ModuleNotFoundError as e:
    print(f"\n❌ Ошибка: Модуль не найден - {e}")
    print("📝 Попробуйте установить зависимости: pip install -r requirements.txt\n")
    sys.exit(1)
    
except Exception as e:
    logger.error(f"Critical error: {e}", exc_info=True)
    print(f"\n❌ Критическая ошибка: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)
