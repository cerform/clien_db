"""
Client message handler - все текстовые сообщения идят в INKA
Полностью убраны все меню и кнопки
Добавлена запись в БД
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging

from src.ai.advanced_inka import get_advanced_inka
from src.config import get_config
from src.db.sheets_client import GoogleSheetsClient
from src.calendars.calendar_init import get_calendar_service

logger = logging.getLogger(__name__)
router = Router()

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
    await message.answer(
        "👑 <b>Админ панель:</b>\n\n"
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
        sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
        
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
    """
    user_id = message.from_user.id
    user_text = message.text
    
    # Показываем typing indicator СРАЗУ
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        config = get_config()
        
        # Создаём sheets_client
        sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
        
        # Создаём calendar service
        calendar_service = get_calendar_service(config.google_credentials_json)
        
        # Создаём продвинутую INKA с доступом к данным
        inka = get_advanced_inka(
            api_key=config.openai_api_key,
            assistant_id=config.openai_assistant_id,
            sheets_client=sheets,
            calendar_service=calendar_service
        )
        
        # Получаем историю разговора из state
        state_data = await state.get_data()
        conversation_history = state_data.get("conversation_history", [])
        
        # Получаем ответ от продвинутой INKA
        response = await inka.chat(user_text, str(user_id), conversation_history)
        
        # Сохраняем в историю
        conversation_history.append({"role": "user", "content": user_text})
        conversation_history.append({"role": "assistant", "content": response})
        
        # Ограничиваем историю последними 10 сообщениями для эффективности
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        
        await state.update_data(conversation_history=conversation_history)
        
        # Отправляем ответ
        await message.answer(response)
        
        logger.info(f"User {user_id}: {user_text[:50]}... -> {response[:50]}...")
    
    except Exception as e:
        logger.error(f"Advanced INKA error: {e}", exc_info=True)
        await message.answer("Ой, что-то пошло не так! Попробуй ещё раз? 😊")

