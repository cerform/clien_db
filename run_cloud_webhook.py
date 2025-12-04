#!/usr/bin/env python3
"""
Telegram Bot для Cloud Run с INKA AI (aiogram 3.x) - WEBHOOK версия
Стабильная работа на Cloud Run через webhook
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from aiohttp import web

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорт aiogram 3.x
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Импорт AI модулей
try:
    from src.ai.inka import INKAProcessor
    AI_ENABLED = True
    logger.info("INKA AI модуль загружен")
except ImportError as e:
    logger.warning(f"INKA AI модуль не загружен: {e}")
    AI_ENABLED = False

# Сервисы отключены пока (требуют sheets_client)
SERVICES_ENABLED = False
logger.info("Сервисы временно отключены (ждут Google Sheets настройку)")


# FSM States для диалога
class BookingStates(StatesGroup):
    waiting_for_action = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_confirmation = State()


# Глобальные объекты
inka_processor = None
admin_service = None
client_service = None
booking_service = None
bot = None
dp = None


async def initialize_services():
    """Инициализация AI и сервисов"""
    global inka_processor, admin_service, client_service, booking_service
    
    # Инициализация INKA AI
    if AI_ENABLED:
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            inka_processor = INKAProcessor(api_key=openai_key)
            logger.info("✅ INKA AI инициализирован")
        else:
            logger.warning("⚠️ OPENAI_API_KEY не найден, AI будет в демо-режиме")
            inka_processor = INKAProcessor()
    
    # Инициализация сервисов (пропускаем если нужен sheets_client)
    logger.info("✅ Сервисы готовы к инициализации")


def register_handlers(dp: Dispatcher):
    """Регистрация обработчиков"""
    
    @dp.message(Command("start"))
    async def cmd_start(message: Message, state: FSMContext):
        """Команда /start"""
        user_name = message.from_user.first_name or "пользователь"
        user_id = message.from_user.id
        
        await message.reply(
            f"👋 Привет, {user_name}!\n\n"
            f"🤖 Я INKA — AI-ассистент тату-салона.\n\n"
            f"💬 <b>Я помогу тебе:</b>\n"
            f"• Записаться на процедуру\n"
            f"• Узнать о мастерах\n"
            f"• Посмотреть свои записи\n"
            f"• Ответить на вопросы о тату\n\n"
            f"📋 <b>Команды:</b>\n"
            f"/help - Справка\n"
            f"/booking - Записаться\n"
            f"/masters - Наши мастера\n"
            f"/mybookings - Мои записи\n\n"
            f"Просто напиши мне, и я помогу! 😊",
            parse_mode="HTML"
        )
        await state.clear()
        logger.info(f"User {user_id} ({user_name}) started bot")
    
    @dp.message(Command("help"))
    async def cmd_help(message: Message):
        """Команда /help"""
        await message.reply(
            "📋 <b>Справка по командам:</b>\n\n"
            "<b>Основные команды:</b>\n"
            "/start - Главное меню\n"
            "/help - Эта справка\n"
            "/booking - Записаться на процедуру\n"
            "/masters - Список мастеров\n"
            "/mybookings - Мои записи\n\n"
            "💡 <b>Совет:</b> Можешь просто написать мне своими словами!",
            parse_mode="HTML"
        )
    
    @dp.message(Command("booking"))
    async def cmd_booking(message: Message, state: FSMContext):
        """Команда /booking"""
        await message.reply(
            "📅 <b>Записаться на процедуру</b>\n\n"
            "Напиши мне что хочешь сделать и когда тебе удобно!",
            parse_mode="HTML"
        )
        await state.set_state(BookingStates.waiting_for_action)
    
    @dp.message(Command("masters"))
    async def cmd_masters(message: Message):
        """Команда /masters"""
        await message.reply(
            "👨‍🎨 <b>Наши мастера:</b>\n\n"
            "🔸 <b>Аня</b> — Основатель студии\n"
            "Стиль: Реализм, черно-белая графика\n"
            "Опыт: 8+ лет\n\n"
            "🔸 <b>Максим</b> — Тату-мастер\n"
            "Стиль: Олдскул, традишнл\n"
            "Опыт: 5 лет",
            parse_mode="HTML"
        )
    
    @dp.message(Command("mybookings"))
    async def cmd_mybookings(message: Message):
        """Команда /mybookings"""
        await message.reply(
            "📋 <b>Ваши записи:</b>\n\n"
            "Пока нет активных записей.\n\n"
            "Используйте /booking для записи!",
            parse_mode="HTML"
        )
    
    @dp.message(F.text, StateFilter(None))
    async def handle_text_message(message: Message, state: FSMContext):
        """Обработка текстовых сообщений через INKA AI"""
        user_text = message.text
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "пользователь"
        
        logger.info(f"User {user_id} ({user_name}): {user_text}")
        
        # Простая классификация по ключевым словам как fallback
        text_lower = user_text.lower()
        
        # Детектирование записи
        booking_keywords = ['запис', 'хочу', 'сделать', 'татуировк', 'тату', 'можно', 'свободн']
        if any(kw in text_lower for kw in booking_keywords):
            await message.reply(
                "📅 <b>Отлично! Записываю тебя</b>\n\n"
                "У нас есть свободные окна:\n"
                "• 10 декабря в 14:00\n"
                "• 11 декабря в 16:00\n"
                "• 12 декабря в 11:00\n\n"
                "Какое время удобно?",
                parse_mode="HTML"
            )
            return
        
        # Детектирование вопросов о мастерах
        master_keywords = ['мастер', 'кто', 'художник', 'специалист']
        if any(kw in text_lower for kw in master_keywords):
            await message.reply(
                "👨‍🎨 <b>Наши мастера:</b>\n\n"
                "🔸 <b>Аня</b> — Основатель студии\n"
                "Стиль: Реализм, черно-белая графика\n"
                "Опыт: 8+ лет\n\n"
                "🔸 <b>Максим</b> — Тату-мастер\n"
                "Стиль: Олдскул, традишнл\n"
                "Опыт: 5 лет\n\n"
                "К кому хочешь записаться?",
                parse_mode="HTML"
            )
            return
        
        # Детектирование вопросов о ценах
        price_keywords = ['цен', 'стоимост', 'сколько', 'прайс']
        if any(kw in text_lower for kw in price_keywords):
            await message.reply(
                "💰 <b>Цены на услуги:</b>\n\n"
                "• Маленькое тату (до 5см): от 3000₽\n"
                "• Среднее тату (5-15см): от 7000₽\n"
                "• Большое тату (15см+): от 15000₽\n"
                "• Консультация: Бесплатно\n\n"
                "Цена зависит от размера и сложности работы.\n"
                "Хочешь записаться? /booking",
                parse_mode="HTML"
            )
            return
        
        # Если INKA AI доступна - пробуем через LLM
        if inka_processor and inka_processor.client:
            try:
                context = {
                    "client_status": "active",
                    "has_active_booking": False,
                    "callback_slot_id": None
                }
                
                classification = inka_processor.stage_1_classify(user_text, context)
                route = classification.get("route", "other")
                stage = classification.get("stage", "none")
                
                logger.info(f"INKA S1 (LLM): route={route}, stage={stage}")
                
                if route == "booking":
                    available_slots = [
                        {"date": "2025-12-10", "start_time": "14:00"},
                        {"date": "2025-12-11", "start_time": "16:00"},
                        {"date": "2025-12-12", "start_time": "11:00"},
                    ]
                    response_text = inka_processor.stage_2_booking_engine(
                        stage="offer_slots",
                        available_slots=available_slots
                    )
                    await message.reply(response_text)
                    return
                
                elif route == "consultation":
                    await message.reply(
                        "💡 <b>Консультация</b>\n\n"
                        "Отлично! Расскажи подробнее:\n"
                        "• Какую идею хочешь воплотить?\n"
                        "• Примерный размер?\n"
                        "• Место на теле?",
                        parse_mode="HTML"
                    )
                    return
                
                elif route == "info":
                    await message.reply(
                        f"📚 <b>Информация о тату</b>\n\n"
                        f"• <b>Цены:</b> от 3000₽\n"
                        f"• <b>Уход:</b> Подробные инструкции после сеанса\n"
                        f"• <b>Больно ли:</b> Зависит от места, но терпимо 😊\n"
                        f"• <b>Заживление:</b> 2-3 недели\n\n"
                        f"Хочешь записаться? /booking",
                        parse_mode="HTML"
                    )
                    return
                
            except Exception as e:
                logger.error(f"Ошибка INKA LLM: {e}", exc_info=True)
        
        # Общий ответ по умолчанию
        await message.reply(
            f"Привет! 👋\n\n"
            f"Я могу помочь:\n\n"
            f"📅 /booking - Записаться на процедуру\n"
            f"👨‍🎨 /masters - Посмотреть мастеров\n"
            f"💰 Напиши 'цены' - Узнать стоимость\n"
            f"📋 /mybookings - Твои записи\n\n"
            f"Просто напиши что тебе нужно!",
            parse_mode="HTML"
        )


async def on_startup(app):
    """При старте приложения"""
    global bot, dp
    
    await initialize_services()
    
    # Установка webhook
    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types()
        )
        logger.info(f"✅ Webhook установлен: {webhook_url}")
    
    # Установка команд
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Главное меню"),
        types.BotCommand(command="help", description="Справка"),
        types.BotCommand(command="booking", description="Записаться"),
        types.BotCommand(command="masters", description="Мастера"),
        types.BotCommand(command="mybookings", description="Мои записи"),
    ])
    
    logger.info("✅ Бот готов к работе")


async def on_shutdown(app):
    """При остановке приложения"""
    global bot
    
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()
    logger.info("Бот остановлен")


def main():
    """Main function"""
    global bot, dp
    
    # Получить токен
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found")
        return
    
    # Инициализация бота
    storage = MemoryStorage()
    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=storage)
    
    # Регистрация обработчиков
    register_handlers(dp)
    
    # Создание веб-приложения
    app = web.Application()
    
    # Health check endpoint
    async def health(request):
        return web.Response(text='Bot OK', status=200)
    
    app.router.add_get('/health', health)
    app.router.add_get('/', health)
    
    # Webhook endpoint
    webhook_path = os.getenv('WEBHOOK_PATH', '/webhook')
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
    
    # Startup/shutdown
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Setup application
    setup_application(app, dp, bot=bot)
    
    # Запуск сервера
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting webhook server on port {port}")
    web.run_app(app, host='0.0.0.0', port=port)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
