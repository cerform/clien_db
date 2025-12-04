#!/usr/bin/env python3
"""
Telegram Bot для Cloud Run с INKA AI (aiogram 3.x)
Полнофункциональная система администрирования пользователей
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

# Импорт AI модулей
try:
    from src.ai.inka import INKAProcessor
    AI_ENABLED = True
    logger.info("INKA AI модуль загружен")
except ImportError as e:
    logger.warning(f"INKA AI модуль не загружен: {e}")
    AI_ENABLED = False

# Импорт сервисов
try:
    from src.services.admin_service import AdminService
    from src.services.client_service import ClientService
    from src.services.booking_service import BookingService
    SERVICES_ENABLED = True
    logger.info("Сервисы загружены")
except ImportError as e:
    logger.warning(f"Сервисы не загружены: {e}")
    SERVICES_ENABLED = False


# FSM States для диалога
class BookingStates(StatesGroup):
    waiting_for_action = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_confirmation = State()


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


# Глобальные объекты
inka_processor = None
admin_service = None
client_service = None
booking_service = None


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
    
    # Инициализация сервисов
    if SERVICES_ENABLED:
        try:
            admin_service = AdminService()
            client_service = ClientService()
            booking_service = BookingService()
            logger.info("✅ Сервисы администрирования инициализированы")
        except Exception as e:
            logger.warning(f"⚠️ Сервисы не инициализированы: {e}")


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
    storage = MemoryStorage()
    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=storage)
    
    # Инициализация сервисов
    await initialize_services()
    
    # ==================== КОМАНДЫ ====================
    
    @dp.message(Command("start"))
    async def cmd_start(message: Message, state: FSMContext):
        """Команда /start"""
        user_name = message.from_user.first_name or "пользователь"
        user_id = message.from_user.id
        
        # Регистрируем пользователя если есть сервисы
        if client_service:
            try:
                await client_service.register_or_get_client(
                    telegram_id=user_id,
                    username=message.from_user.username,
                    first_name=user_name
                )
                logger.info(f"Пользователь {user_id} зарегистрирован/обновлён")
            except Exception as e:
                logger.error(f"Ошибка регистрации пользователя: {e}")
        
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
            f"/mybookings - Мои записи\n"
            f"/cancel - Отменить запись\n\n"
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
            "/mybookings - Мои записи\n"
            "/cancel - Отменить запись\n\n"
            "<b>Админ-команды:</b>\n"
            "/admin - Админ-панель (только для админов)\n"
            "/stats - Статистика\n\n"
            "💡 <b>Совет:</b> Можешь просто написать мне своими словами, "
            "например: 'Хочу записаться на тату' или 'Кто ваши мастера?'",
            parse_mode="HTML"
        )
    
    @dp.message(Command("booking"))
    async def cmd_booking(message: Message, state: FSMContext):
        """Команда /booking - запись"""
        await message.reply(
            "📅 <b>Записаться на процедуру</b>\n\n"
            "Напиши мне:\n"
            "• Что хочешь сделать (тату, консультация)\n"
            "• Когда тебе удобно\n"
            "• К какому мастеру\n\n"
            "Или просто напиши 'хочу записаться', и я задам уточняющие вопросы 😊",
            parse_mode="HTML"
        )
        await state.set_state(BookingStates.waiting_for_action)
    
    @dp.message(Command("masters"))
    async def cmd_masters(message: Message):
        """Команда /masters - список мастеров"""
        await message.reply(
            "👨‍🎨 <b>Наши мастера:</b>\n\n"
            "🔸 <b>Аня</b> — Основатель студии\n"
            "Стиль: Реализм, черно-белая графика\n"
            "Опыт: 8+ лет\n\n"
            "🔸 <b>Максим</b> — Тату-мастер\n"
            "Стиль: Олдскул, традишнл\n"
            "Опыт: 5 лет\n\n"
            "Чтобы записаться к конкретному мастеру, напиши: "
            "'Хочу к Ане' или используй /booking",
            parse_mode="HTML"
        )
    
    @dp.message(Command("mybookings"))
    async def cmd_mybookings(message: Message):
        """Команда /mybookings - мои записи"""
        user_id = message.from_user.id
        
        if booking_service:
            try:
                bookings = await booking_service.get_user_bookings(user_id)
                if bookings:
                    text = "📋 <b>Ваши записи:</b>\n\n"
                    for booking in bookings:
                        text += f"• {booking['date']} в {booking['time']}\n"
                        text += f"  Мастер: {booking['master']}\n"
                        text += f"  Услуга: {booking['service']}\n\n"
                    await message.reply(text, parse_mode="HTML")
                else:
                    await message.reply("У вас пока нет записей.\n\nИспользуйте /booking для записи!")
            except Exception as e:
                logger.error(f"Ошибка получения записей: {e}")
                await message.reply("Произошла ошибка при получении записей.")
        else:
            await message.reply(
                "📋 <b>Ваши записи:</b>\n\n"
                "Пока нет активных записей.\n\n"
                "Используйте /booking для записи!",
                parse_mode="HTML"
            )
    
    @dp.message(Command("admin"))
    async def cmd_admin(message: Message):
        """Команда /admin - админ-панель"""
        user_id = message.from_user.id
        
        # Проверка прав админа
        is_admin = False
        if admin_service:
            try:
                is_admin = await admin_service.is_admin(user_id)
            except Exception as e:
                logger.error(f"Ошибка проверки прав админа: {e}")
        
        if is_admin:
            await message.reply(
                "👑 <b>Админ-панель</b>\n\n"
                "Доступные команды:\n"
                "/stats - Статистика бота\n"
                "/users - Список пользователей\n"
                "/broadcast - Рассылка сообщения\n"
                "/settings - Настройки",
                parse_mode="HTML"
            )
        else:
            await message.reply("❌ У вас нет прав администратора.")
    
    # ==================== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ЧЕРЕЗ INKA AI ====================
    
    @dp.message(F.text, StateFilter(None))
    async def handle_text_message(message: Message, state: FSMContext):
        """Обработка текстовых сообщений через INKA AI"""
        user_text = message.text
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "пользователь"
        
        logger.info(f"User {user_id} ({user_name}): {user_text}")
        
        # Если INKA AI доступна
        if inka_processor and inka_processor.client:
            try:
                # S1 - Классификация намерения
                context = {
                    "client_status": "active",
                    "has_active_booking": False,
                    "callback_slot_id": None
                }
                
                classification = inka_processor.stage_1_classify(user_text, context)
                route = classification.get("route", "other")
                stage = classification.get("stage", "none")
                
                logger.info(f"INKA S1: route={route}, stage={stage}")
                
                # Обработка маршрутов
                if route == "booking":
                    # S2 - Booking Engine
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
                
                elif route == "consultation":
                    await message.reply(
                        "💡 <b>Консультация</b>\n\n"
                        "Отлично! Расскажи подробнее:\n"
                        "• Какую идею хочешь воплотить?\n"
                        "• Примерный размер?\n"
                        "• Место на теле?\n\n"
                        "Можешь прислать референсы (фото), если есть!",
                        parse_mode="HTML"
                    )
                
                elif route == "info":
                    await message.reply(
                        f"📚 Спасибо за вопрос!\n\n"
                        f"Вот что я могу рассказать:\n\n"
                        f"• <b>Цены:</b> от 3000₽ (зависит от размера и сложности)\n"
                        f"• <b>Уход:</b> Подробные инструкции дам после сеанса\n"
                        f"• <b>Больно ли:</b> Индивидуально, но терпимо 😊\n\n"
                        f"Хочешь записаться? Используй /booking",
                        parse_mode="HTML"
                    )
                
                else:
                    # Общий ответ
                    await message.reply(
                        f"Понял тебя! Вот что я могу:\n\n"
                        f"📅 /booking - Записаться\n"
                        f"👨‍🎨 /masters - Наши мастера\n"
                        f"📋 /mybookings - Твои записи\n\n"
                        f"Или задай вопрос своими словами!"
                    )
                
            except Exception as e:
                logger.error(f"Ошибка обработки через INKA: {e}", exc_info=True)
                await message.reply(
                    "Произошла ошибка при обработке сообщения. "
                    "Попробуй еще раз или используй команды:\n"
                    "/help - Справка\n"
                    "/booking - Записаться"
                )
        else:
            # Без AI - простой ответ
            await message.reply(
                f"📨 Получил твоё сообщение: <i>{user_text}</i>\n\n"
                f"Доступные команды:\n"
                f"/booking - Записаться\n"
                f"/masters - Наши мастера\n"
                f"/help - Справка\n\n"
                f"<i>💡 Подсказка: для полной функциональности AI нужен OPENAI_API_KEY</i>",
                parse_mode="HTML"
            )
    
    # Установка команд в меню бота
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Главное меню"),
        types.BotCommand(command="help", description="Справка"),
        types.BotCommand(command="booking", description="Записаться"),
        types.BotCommand(command="masters", description="Наши мастера"),
        types.BotCommand(command="mybookings", description="Мои записи"),
        types.BotCommand(command="cancel", description="Отменить запись"),
    ])
    
    logger.info("✅ Bot commands set successfully")
    logger.info("✅ Starting bot polling...")
    
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
