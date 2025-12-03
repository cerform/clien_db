from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from datetime import datetime, timedelta

from src.bot.keyboards import (
    get_client_menu, get_main_menu, 
    get_masters_keyboard, get_slots_keyboard,
    get_procedures_keyboard
)
from src.db.sheets_client import GoogleSheetsClient
from src.services.client_service import ClientService
from src.services.master_service import MasterService
from src.services.booking_service import BookingService
from src.ai.inka import get_inka_processor
from src.config import get_config

logger = logging.getLogger(__name__)
router = Router()

class BookingStates(StatesGroup):
    waiting_for_master = State()
    waiting_for_procedure = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_confirmation = State()

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
    
    await message.answer(
        "👥 Выберите мастера:",
        reply_markup=get_masters_keyboard(masters)
    )

@router.message(F.text == "📅 Записать на прием")
async def book_appointment(message: Message, state: FSMContext):
    """Book appointment - start process with INKA S1 classification"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    master_service = MasterService(sheets)
    booking_service = BookingService(sheets)
    
    user_id = message.from_user.id
    
    # Используем INKA S1 для классификации
    inka = get_inka_processor(config.openai_api_key)
    
    # Получаем контекст
    has_active = booking_service.get_user_bookings(user_id)
    
    classification = inka.stage_1_classify(
        message.text,
        context={
            "client_status": "regular",
            "has_active_booking": bool(has_active)
        }
    )
    
    logger.info(f"S1 Classification: {classification}")
    
    # Проверяем route и stage
    route = classification.get("route", "other")
    stage = classification.get("stage", "none")
    
    if route == "booking" and stage == "offer_slots":
        masters = master_service.get_all_masters()
        if not masters:
            await message.answer("❌ Нет доступных мастеров")
            return
        
        await state.set_state(BookingStates.waiting_for_master)
        
        # Используем INKA S2 для текста предложения
        inka_s2_text = inka.stage_2_booking_engine(
            stage="offer_slots",
            available_slots=[]
        )
        
        await message.answer(
            "👥 Выберите мастера:",
            reply_markup=get_masters_keyboard(masters)
        )
    else:
        await message.answer("Что-то пошло не так. Давай попробуем заново.")

@router.callback_query(BookingStates.waiting_for_master, F.data.startswith("master_"))
async def select_master(callback: CallbackQuery, state: FSMContext):
    """Select master callback"""
    master_id = callback.data.split("_")[1]
    
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    
    # Сохраняем выбор мастера
    await state.update_data(master_id=master_id)
    
    # Получаем список процедур
    from src.services.procedure_service import ProcedureService
    procedure_service = ProcedureService(sheets)
    procedures = procedure_service.get_all_procedures()
    
    await state.set_state(BookingStates.waiting_for_procedure)
    await callback.message.edit_text(
        "💇 Выберите процедуру:",
        reply_markup=get_procedures_keyboard(procedures)
    )
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_procedure, F.data.startswith("proc_"))
async def select_procedure(callback: CallbackQuery, state: FSMContext):
    """Select procedure callback"""
    procedure_id = callback.data.split("_")[1]
    
    await state.update_data(procedure_id=procedure_id)
    
    # Генерируем доступные даты (следующие 14 дней)
    dates = []
    for i in range(1, 15):
        date = datetime.now() + timedelta(days=i)
        if date.weekday() < 6:  # Пн-Сб
            dates.append(date.strftime("%Y-%m-%d"))
    
    await state.set_state(BookingStates.waiting_for_date)
    await callback.message.edit_text(
        "📅 Выберите дату:",
        reply_markup=get_slots_keyboard(dates, "date")
    )
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_date, F.data.startswith("date_"))
async def select_date(callback: CallbackQuery, state: FSMContext):
    """Select date callback"""
    selected_date = callback.data.split("_", 1)[1]
    
    await state.update_data(date=selected_date)
    
    # Генерируем доступные времена (с 10:00 до 18:00 каждый час)
    times = [f"{h:02d}:00" for h in range(10, 18)]
    
    await state.set_state(BookingStates.waiting_for_time)
    await callback.message.edit_text(
        f"⏰ Выберите время на {selected_date}:",
        reply_markup=get_slots_keyboard(times, "time")
    )
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_time, F.data.startswith("time_"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    """Select time callback"""
    selected_time = callback.data.split("_", 1)[1]
    
    data = await state.get_data()
    await state.update_data(time=selected_time)
    
    # Показываем подтверждение
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    master_service = MasterService(sheets)
    
    from src.services.procedure_service import ProcedureService
    procedure_service = ProcedureService(sheets)
    
    master = master_service.get_master(data['master_id'])
    procedure = procedure_service.get_procedure(data['procedure_id'])
    
    confirmation_text = (
        f"✅ Подтверждение записи:\n\n"
        f"👨‍💼 Мастер: {master['name'] if master else 'N/A'}\n"
        f"💇 Услуга: {procedure['name'] if procedure else 'N/A'}\n"
        f"📅 Дата: {data['date']}\n"
        f"⏰ Время: {selected_time}\n\n"
        f"Подтвердить запись?"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, подтвердить", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="confirm_no")
        ]
    ])
    
    await state.set_state(BookingStates.waiting_for_confirmation)
    await callback.message.edit_text(confirmation_text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_confirmation, F.data == "confirm_yes")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    """Confirm booking with INKA S3"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    booking_service = BookingService(sheets)
    inka = get_inka_processor(config.openai_api_key)
    
    booking_data = {
        "user_id": user_id,
        "master_id": data['master_id'],
        "procedure_id": data['procedure_id'],
        "date": data['date'],
        "time": data['time'],
        "status": "pending"
    }
    
    success = booking_service.create_booking(booking_data)
    
    if success:
        # Используем INKA S3 для финального сообщения
        s3_message = inka.stage_3_post_booking(
            "confirm",
            booking_data={"date": data['date'], "time": data['time']}
        )
        await callback.message.edit_text(s3_message)
    else:
        await callback.message.edit_text("❌ Ошибка при создании записи. Попробуйте позже.")
    
    await state.clear()
    await callback.answer()

@router.callback_query(BookingStates.waiting_for_confirmation, F.data == "confirm_no")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    """Cancel booking"""
    inka = get_inka_processor()
    cancel_message = inka.stage_3_post_booking("cancel")
    
    await callback.message.edit_text(cancel_message)
    await state.clear()
    await callback.answer()

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
