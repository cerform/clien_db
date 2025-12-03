from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import logging

from src.bot.keyboards import get_client_menu, get_main_menu
from src.db.sheets_client import GoogleSheetsClient
from src.services.client_service import ClientService
from src.services.master_service import MasterService
from src.services.booking_service import BookingService
from src.config import get_config

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "👤 Личный кабинет")
async def client_cabinet(message: Message, state: FSMContext):
    """Client cabinet"""
    user_id = message.from_user.id
    
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    client_service = ClientService(sheets)
    
    client = client_service.get_client(user_id)
    if client:
        await message.answer(
            f"👤 Ваш профиль:\n\n"
            f"👤 Имя: {client['name']}\n"
            f"📱 Телефон: {client['phone']}\n"
            f"📧 Email: {client['email']}\n"
            f"📅 Дата регистрации: {client['created_at']}\n\n"
            "Выберите действие:",
            reply_markup=get_client_menu()
        )

@router.message(F.text == "👥 Выбрать мастера")
async def choose_master(message: Message):
    """Choose master"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    master_service = MasterService(sheets)
    
    masters = master_service.get_all_masters()
    if not masters:
        await message.answer("❌ Нет доступных мастеров")
        return
    
    text = "👥 Наши мастера:\n\n"
    for i, master in enumerate(masters, 1):
        text += f"{i}. {master['name']}\n"
        text += f"   Специализация: {master['specialization']}\n"
        text += f"   Телефон: {master['phone']}\n\n"
    
    await message.answer(text)

@router.message(F.text == "📅 Записать на прием")
async def book_appointment(message: Message):
    """Book appointment"""
    await message.answer(
        "📅 Запись на прием\n\n"
        "Функция временно недоступна. Пожалуйста, свяжитесь с администратором."
    )

@router.message(F.text == "📋 Мои записи")
async def my_bookings(message: Message):
    """Show user bookings"""
    user_id = message.from_user.id
    
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    booking_service = BookingService(sheets)
    
    bookings = booking_service.get_user_bookings(user_id)
    if not bookings:
        await message.answer("📋 У вас нет записей")
        return
    
    text = "📋 Ваши записи:\n\n"
    for booking in bookings:
        text += f"📅 {booking['date']} {booking['time']}\n"
        text += f"👨‍💼 Мастер: {booking['master_id']}\n"
        text += f"💇 Услуга: {booking['service']}\n"
        text += f"✅ Статус: {booking['status']}\n\n"
    
    await message.answer(text)

@router.message(F.text == "🔙 Назад")
async def back_to_menu(message: Message):
    """Back to main menu"""
    await message.answer("Выберите действие:", reply_markup=get_main_menu())
