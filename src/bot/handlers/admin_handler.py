from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import logging

from src.bot.keyboards import get_admin_menu, get_main_menu
from src.db.sheets_client import GoogleSheetsClient
from src.services.admin_service import AdminService
from src.config import get_config

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "👥 Управление клиентами")
async def manage_clients(message: Message):
    """Manage clients"""
    config = get_config()
    
    if message.from_user.id not in config.admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    admin_service = AdminService(sheets)
    
    data = admin_service.export_data()
    clients = data.get('clients', [])
    
    if not clients:
        await message.answer("👥 Нет клиентов")
        return
    
    text = f"👥 Всего клиентов: {len(clients)}\n\n"
    for client in clients[:10]:  # Show first 10
        text += f"👤 {client['name']}\n"
        text += f"📱 {client['phone']}\n"
        text += f"📧 {client['email']}\n\n"
    
    await message.answer(text)

@router.message(F.text == "📊 Статистика")
async def statistics(message: Message):
    """Show statistics"""
    config = get_config()
    
    if message.from_user.id not in config.admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    admin_service = AdminService(sheets)
    
    stats = admin_service.get_dashboard_stats()
    
    await message.answer(
        f"📊 Статистика\n\n"
        f"👥 Всего клиентов: {stats.get('total_clients', 0)}\n"
        f"👨‍💼 Всего мастеров: {stats.get('total_masters', 0)}"
    )

@router.message(F.text == "👨‍💼 Управление мастерами")
async def manage_masters(message: Message):
    """Manage masters"""
    config = get_config()
    
    if message.from_user.id not in config.admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    await message.answer("👨‍💼 Управление мастерами\n\nФункция временно недоступна.")

@router.message(F.text == "📅 Управление записями")
async def manage_bookings(message: Message):
    """Manage bookings"""
    config = get_config()
    
    if message.from_user.id not in config.admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    await message.answer("📅 Управление записями\n\nФункция временно недоступна.")
