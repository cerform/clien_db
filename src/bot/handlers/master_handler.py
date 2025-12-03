from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import logging

from src.bot.keyboards import get_master_menu, get_main_menu
from src.db.sheets_client import GoogleSheetsClient
from src.services.booking_service import BookingService
from src.config import get_config, BOOKING_STATUS_CONFIRMED, BOOKING_STATUS_REJECTED

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "📅 Мой календарь")
async def master_calendar(message: Message):
    """Show master calendar"""
    await message.answer(
        "📅 Мой календарь\n\n"
        "Функция временно недоступна."
    )

@router.message(F.text == "✅ Подтвердить запись")
async def confirm_booking(message: Message):
    """Confirm booking"""
    await message.answer(
        "✅ Подтверждение записи\n\n"
        "Функция временно недоступна."
    )

@router.message(F.text == "❌ Отклонить запись")
async def reject_booking(message: Message):
    """Reject booking"""
    await message.answer(
        "❌ Отклонение записи\n\n"
        "Функция временно недоступна."
    )
