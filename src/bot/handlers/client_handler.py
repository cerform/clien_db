"""
Client message handler - все текстовые сообщения идят в INKA
Полностью убраны все меню и кнопки
Добавлена запись в БД
Оптимизирован для скорости с кэшированием
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging
import os
import asyncio

from src.ai.advanced_inka import get_advanced_inka
from src.config import get_config
from src.db.sheets_client import GoogleSheetsClient
from src.calendars.calendar_init import get_calendar_service

logger = logging.getLogger(__name__)
router = Router()

# Глобальные кэши для улучшения производительности
_sheet_client_cache = None
_calendar_service_cache = None
_inka_cache = None
_initialization_lock = None  # Инициализируется лениво


def get_initialization_lock():
    """Получить lock для инициализации (lazy создание в правильном event loop)"""
    global _initialization_lock
    if _initialization_lock is None:
        try:
            _initialization_lock = asyncio.Lock()
        except RuntimeError:
            # Если нет event loop, создаём простую заглушку
            return None
    return _initialization_lock


async def get_sheet_client_cached_async():
    """Get cached Google Sheets client (async, with lazy initialization)"""
    global _sheet_client_cache
    
    if _sheet_client_cache is not None:
        return _sheet_client_cache
    
    # Простая инициализация без lock (lock вызывает проблемы в FastAPI context)
    try:
        # Двойная проверка
        if _sheet_client_cache is not None:
            return _sheet_client_cache
        
        logger.info("⏳ Initializing Google Sheets client...")
        config = get_config()
        _sheet_client_cache = GoogleSheetsClient(
            "", 
            config.google_spreadsheet_id
        )
        logger.info("✅ Google Sheets client initialized (cached)")
    except Exception as e:
        logger.error(f"Failed to initialize Sheets client: {e}")
        return None
    
    return _sheet_client_cache


async def get_calendar_service_cached_async():
    """Get cached Google Calendar service (async, with lazy initialization)"""
    global _calendar_service_cache
    
    if _calendar_service_cache is not None:
        return _calendar_service_cache
    
    try:
        # Двойная проверка
        if _calendar_service_cache is not None:
            return _calendar_service_cache
        
        logger.info("⏳ Initializing Google Calendar service...")
        config = get_config()
        _calendar_service_cache = get_calendar_service("")
        
        if _calendar_service_cache:
            logger.info("✅ Google Calendar service initialized (cached)")
        else:
            logger.warning("⚠️ Google Calendar service unavailable - will use fallback")
    except Exception as e:
        logger.error(f"Failed to initialize Calendar service: {e}")
        # Не возвращаем ошибку, продолжаем работу без календаря
    
    return _calendar_service_cache


async def get_inka_cached_async(api_key, assistant_id, sheets_client, calendar_service):
    """Get cached INKA instance (async) with admin_ids"""
    global _inka_cache
    try:
        logger.info(f"🔴 get_inka_cached_async called")
        if _inka_cache is None:
            logger.info(f"🟡 Creating new INKA instance with admin support...")
            config = get_config()
            admin_ids = config.admin_ids if config.admin_ids else []
            logger.info(f"Admin IDs: {admin_ids}")
            
            _inka_cache = get_advanced_inka(
                api_key=api_key,
                assistant_id=assistant_id,
                sheets_client=sheets_client,
                calendar_service=calendar_service,
                admin_ids=admin_ids
            )
            logger.info(f"🟢 INKA instance created: {_inka_cache is not None}")
        else:
            logger.info(f"🟢 INKA instance cached (reusing)")
        logger.info("✅ INKA instance initialized (cached)")
        return _inka_cache
    except Exception as e:
        logger.error(f"❌ Error in get_inka_cached_async: {e}", exc_info=True)
        raise

# Загружаем админов из конфига
try:
    config = get_config()
    ADMIN_IDS = config.admin_ids if config.admin_ids else []
    logger.info(f"✅ Админы загружены: {ADMIN_IDS}")
except Exception as e:
    ADMIN_IDS = []
    logger.error(f"❌ Ошибка при загрузке админов: {e}")


def get_admin_ids():
    """Получить список админов (загружать динамически)"""
    try:
        config = get_config()
        return config.admin_ids if config.admin_ids else []
    except:
        return []


@router.message(Command("admin"))
async def admin_command(message: Message):
    """Admin panel access"""
    user_id = message.from_user.id
    admin_ids = get_admin_ids()  # Загружаем динамически
    
    # Проверяем если пользователь в списке админов
    if user_id not in admin_ids:
        logger.info(f"❌ User {user_id} не админ. Админы: {admin_ids}")
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    logger.info(f"✅ Admin {user_id} вошёл в панель")
    
    # URL админ-панели
    admin_url = "https://tattoo-bot-408800151466.us-central1.run.app"
    
    await message.answer(
        "👑 <b>Админ панель:</b>\n\n"
        f"🔗 <b>Веб-панель:</b> {admin_url}\n\n"
        "Доступные команды:\n"
        "/admin - Эта панель\n"
        "/stats - Статистика\n"
        "/bookings - Список записей\n"
        "/clients - Список клиентов\n\n"
        "Или просто пиши - INKA поможет! 😊",
        parse_mode="HTML"
    )


@router.message(Command("stats"))
async def stats_command(message: Message):
    """Show statistics"""
    user_id = message.from_user.id
    admin_ids = get_admin_ids()  # Загружаем динамически
    
    # Проверяем если пользователь в списке админов
    if user_id not in admin_ids:
        logger.info(f"❌ User {user_id} не админ (попытка /stats)")
        await message.answer("❌ У вас нет доступа.")
        return
    
    try:
        config = get_config()
        sheets = await get_sheet_client_cached_async()
        
        if sheets is None:
            await message.answer("❌ Ошибка подключения к БД")
            return
        
        bookings_data = sheets.get_all_rows("bookings")
        clients_data = sheets.get_all_rows("clients")
        
        total_bookings = len(bookings_data) - 1 if bookings_data else 0
        total_clients = len(clients_data) - 1 if clients_data else 0
        
        stats_text = (
            f"📊 <b>Статистика:</b>\n\n"
            f"📋 Записей: {total_bookings}\n"
            f"👥 Клиентов: {total_clients}\n"
        )
        
        await message.answer(stats_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.text)
async def handle_text_message(message: Message, state: FSMContext):
    """
    Обработка всех текстовых сообщений через продвинутую INKA
    Никаких меню - только чистое общение с AI
    Оптимизирован для скорости с асинхронной инициализацией
    """
    user_id = message.from_user.id
    user_text = message.text
    
    logger.warning(f"⚠️  TEXT MESSAGE RECEIVED FROM {user_id}: {user_text[:100]}")
    logger.info(f"📨 Message from {user_id}: {user_text[:100]}")
    
    # Показываем typing indicator СРАЗУ
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        config = get_config()
        
        logger.info(f"🔴 Getting Sheets client...")
        # Используем асинхронный лоадинг с кэшированием
        sheets = await get_sheet_client_cached_async()
        logger.info(f"🟡 Got Sheets: {sheets is not None}")
        
        calendar_service = await get_calendar_service_cached_async()
        logger.info(f"🟡 Got Calendar: {calendar_service is not None}")
        
        if sheets is None:
            logger.error("Sheets client is not available")
            await message.answer("❌ Ошибка подключения к базе данных")
            return
        
        logger.info(f"🔴 Getting INKA...")
        # Получаем кэшированную INKA
        inka = await get_inka_cached_async(
            api_key=config.openai_api_key,
            assistant_id=config.openai_assistant_id,
            sheets_client=sheets,
            calendar_service=calendar_service
        )
        logger.info(f"🟡 Got INKA: {inka is not None}")
        
        # Получаем историю разговора из state
        state_data = await state.get_data()
        conversation_history = state_data.get("conversation_history", [])
        
        logger.info(f"🔴 Calling inka.chat()...")
        # Получаем ответ от продвинутой INKA
        response = await inka.chat(user_text, str(user_id), conversation_history)
        logger.info(f"🟢 Got response: {response[:100]}")
        
        # Сохраняем в историю
        conversation_history.append({"role": "user", "content": user_text})
        conversation_history.append({"role": "assistant", "content": response})
        
        # Ограничиваем историю последними 10 сообщениями для эффективности
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        
        await state.update_data(conversation_history=conversation_history)
        
        # Отправляем ответ БЕЗ МЕНЮ И КНОПОК
        await message.answer(response)
        
        logger.info(f"User {user_id}: {user_text[:50]}... -> {response[:50]}...")
    
    except Exception as e:
        logger.error(f"Advanced INKA error: {e}", exc_info=True)
        await message.answer("Ой, что-то пошло не так! Попробуй ещё раз? 😊")

