"""
Простой бот для записи на тату с кнопками и календарем
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import logging

from src.bot.keyboards.client_kb import get_main_menu, get_calendar_keyboard, get_language_keyboard, get_time_slots_keyboard
from src.bot.locales import get_text, get_menu_buttons
from src.config.config import Config
from src.config.env_loader import load_env
from src.services.service_factory import get_booking_service, get_calendar_service

logger = logging.getLogger(__name__)
router = Router(name="simple_client")

# Store user language preferences
user_languages = {}

# Состояния для записи
class BookingStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_phone = State()
    waiting_for_confirmation = State()

def get_user_lang(user_id: int) -> str:
    """Получить язык пользователя"""
    return user_languages.get(user_id, "en")

def set_user_lang(user_id: int, lang: str):
    """Установить язык пользователя"""
    user_languages[user_id] = lang

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Стартовое сообщение"""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    
    await message.answer(
        get_text(lang, "start_message", name=message.from_user.first_name),
        reply_markup=get_main_menu(lang)
    )

@router.callback_query(F.data.startswith("lang:"))
async def process_language_selection(callback: CallbackQuery):
    """Выбор языка"""
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id
    set_user_lang(user_id, lang)
    
    await callback.message.edit_text(get_text(lang, "language_changed"))
    await callback.message.answer(
        get_text(lang, "start_message", name=callback.from_user.first_name),
        reply_markup=get_main_menu(lang)
    )

# === ОБРАБОТЧИКИ СОСТОЯНИЙ (должны быть ПЕРЕД общим F.text) ===

@router.message(BookingStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Получили описание тату"""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    
    await state.update_data(description=message.text)
    
    # Показываем календарь
    await state.set_state(BookingStates.waiting_for_date)
    await message.answer(
        get_text(lang, "choose_date"),
        reply_markup=get_calendar_keyboard()
    )

@router.callback_query(F.data.startswith("date:"))
async def process_date(callback: CallbackQuery, state: FSMContext):
    """Выбрана дата"""
    date_str = callback.data.split(":")[1]
    await state.update_data(date=date_str)
    
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    try:
        # Получаем доступные слоты на эту дату
        # Показываем кнопки с временными слотами
        await state.set_state(BookingStates.waiting_for_time)
        
        await callback.message.edit_text(
            get_text(lang, "available_slots", date=date_str),
            reply_markup=get_time_slots_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error getting slots: {e}")
        await callback.message.edit_text(
            get_text(lang, "slots_error"),
            reply_markup=get_time_slots_keyboard()
        )

@router.callback_query(F.data.startswith("time:"))
async def process_time(callback: CallbackQuery, state: FSMContext):
    """Выбрано время"""
    parts = callback.data.split(":")
    start_time = parts[1]
    end_time = parts[2]
    
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    
    await state.update_data(
        time=start_time,
        end_time=end_time
    )
    
    # Запрашиваем телефон
    await state.set_state(BookingStates.waiting_for_phone)
    await callback.message.edit_text(get_text(lang, "enter_phone"))

@router.message(BookingStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Получили телефон"""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    
    phone = message.text.strip()
    await state.update_data(phone=phone)
    
    # Показываем подтверждение
    data = await state.get_data()
    
    await state.set_state(BookingStates.waiting_for_confirmation)
    await message.answer(
        get_text(lang, "confirm_booking",
                description=data['description'],
                date=data['date'],
                time=data['time'],
                end_time=data['end_time'],
                phone=phone)
    )

@router.message(BookingStates.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    """Подтверждение записи"""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    answer = message.text.lower()
    
    if answer in ["yes", "да", "confirm", "ок", "ok", "כן"]:
        data = await state.get_data()
        
        try:
            # Сохраняем запись в Google Sheets
            booking_service = get_booking_service()
            
            load_env()
            cfg = Config.from_env()
            
            # Получаем мастера (пока первого доступного)
            from src.db.sheets_client import SheetsClient
            sheets_client = SheetsClient()
            masters = sheets_client.read_sheet(cfg.SPREADSHEET_ID, "masters")
            master_id = None
            for m in masters:
                if m.get("active", "").lower() in ("yes", "true"):
                    master_id = m.get("id")
                    break
            
            if not master_id:
                master_id = "master_001"  # fallback
            
            result = booking_service.create_booking(
                client_telegram_id=message.from_user.id,
                client_name=message.from_user.full_name,
                client_phone=data['phone'],
                date=data['date'],
                master_id=master_id,
                slot_start=data['time'],
                slot_end=data['end_time'],
                notes=data['description']
            )
            
            await message.answer(
                get_text(lang, "booking_created",
                        booking_id=result.get('booking_id', 'N/A'),
                        date=data['date'],
                        time=data['time'],
                        end_time=data['end_time']),
                reply_markup=get_main_menu(lang)
            )
            
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            await message.answer(
                get_text(lang, "booking_error"),
                reply_markup=get_main_menu(lang)
            )
        
        await state.clear()
        
    else:
        await message.answer(
            get_text(lang, "booking_cancelled"),
            reply_markup=get_main_menu(lang)
        )
        await state.clear()

# === ОБЩИЙ ОБРАБОТЧИК ТЕКСТА (должен быть последним) ===

@router.message(F.text)
async def handle_menu_buttons(message: Message, state: FSMContext):
    """Обработка кнопок меню (только когда пользователь не в процессе бронирования)"""
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    text = message.text
    
    # Проверяем, не находится ли пользователь в процессе бронирования
    current_state = await state.get_state()
    if current_state is not None:
        # Пользователь в процессе FSM - игнорируем текстовые сообщения
        # Текст обрабатывается только в специфичных обработчиках состояний
        return
    
    # Кнопка языка
    if text in [get_text("en", "menu_language"), get_text("ru", "menu_language"), get_text("he", "menu_language")]:
        await message.answer(
            get_text(lang, "choose_language"),
            reply_markup=get_language_keyboard()
        )
        return
    
    # Кнопка записи
    if text in [get_text("en", "menu_book"), get_text("ru", "menu_book"), get_text("he", "menu_book")]:
        await state.set_state(BookingStates.waiting_for_description)
        await message.answer(get_text(lang, "describe_tattoo"))
        return
    
    # Кнопка "Мои записи"
    if text in [get_text("en", "menu_bookings"), get_text("ru", "menu_bookings"), get_text("he", "menu_bookings")]:
        await show_my_bookings(message, lang)
        return
    
    # Кнопка информации
    if text in [get_text("en", "menu_info"), get_text("ru", "menu_info"), get_text("he", "menu_info")]:
        await message.answer(get_text(lang, "info_text"))
        return
    
    # Неизвестная команда
    await message.answer(
        get_text(lang, "unknown_command"),
        reply_markup=get_main_menu(lang)
    )

async def show_my_bookings(message: Message, lang: str):
    """Показать записи пользователя"""
    try:
        booking_service = get_booking_service()
        load_env()
        cfg = Config.from_env()
        
        bookings = await booking_service.get_user_bookings(
            user_id=message.from_user.id,
            spreadsheet_id=cfg.SPREADSHEET_ID
        )
        
        if not bookings:
            await message.answer(get_text(lang, "no_bookings"))
            return
        
        text = get_text(lang, "your_bookings")
        for booking in bookings:
            text += (
                f"🔸 #{booking['id']}\n"
                f"   📅 {booking['date']} at {booking['time']}\n"
                f"   📝 {booking['description'][:50]}...\n"
                f"   Status: {booking['status']}\n\n"
            )
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error getting bookings: {e}")
        await message.answer(get_text(lang, "bookings_error"))
