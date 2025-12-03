from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from src.bot.keyboards import get_main_menu, get_cancel_keyboard, get_admin_menu
from src.db.sheets_client import GoogleSheetsClient
from src.services.client_service import ClientService
from src.config import get_config

logger = logging.getLogger(__name__)
router = Router()

class StartStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    user_id = message.from_user.id
    
    # Initialize services
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    client_service = ClientService(sheets)
    
    # Check if user is admin
    if user_id in config.admin_ids:
        admin_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⚙️ Администратор")],
                [KeyboardButton(text="👤 Личный кабинет")],
                [KeyboardButton(text="📞 Контакты")],
                [KeyboardButton(text="❓ Помощь")]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        await message.answer(
            f"👋 Привет, администратор {message.from_user.first_name}!",
            reply_markup=admin_keyboard
        )
        return
    
    # Check if user is already registered
    if client_service.client_exists(user_id):
        await message.answer(
            f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
            "Выберите действие:",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Давайте зарегистрируемся. Как вас зовут?",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(StartStates.waiting_for_name)

@router.message(StartStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Process user name"""
    if message.text == "❌ Отмена":
        await state.clear()
        return
    
    await state.update_data(name=message.text)
    await message.answer("Спасибо! Теперь укажите ваш номер телефона:")
    await state.set_state(StartStates.waiting_for_phone)

@router.message(StartStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Process phone number"""
    if message.text == "❌ Отмена":
        await state.clear()
        return
    
    user_data = await state.get_data()
    user_id = message.from_user.id
    name = user_data.get('name')
    phone = message.text
    
    # Save to database
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    client_service = ClientService(sheets)
    
    if client_service.create_client(user_id, name, phone):
        await message.answer(
            "✅ Регистрация завершена!\n\n"
            "Выберите действие:",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "❌ Ошибка при регистрации. Попробуйте позже."
        )
    
    await state.clear()

@router.message(F.text == "❓ Помощь")
async def help_handler(message: Message):
    """Help handler"""
    await message.answer(
        "ℹ️ Справка по боту:\n\n"
        "👤 Личный кабинет - Управление вашим профилем\n"
        "📅 Записать на прием - Запишитесь на услугу\n"
        "📋 Мои записи - Просмотрите ваши записи\n"
        "👥 Выбрать мастера - Информация о мастерах\n"
        "📞 Контакты - Наши контакты\n\n"
        "Для получения дополнительной помощи свяжитесь с администратором."
    )

@router.message(F.text == "📞 Контакты")
async def contacts_handler(message: Message):
    """Contacts handler"""
    await message.answer(
        "📞 Наши контакты:\n\n"
        "📱 Телефон: +7 (999) 123-45-67\n"
        "📧 Email: info@tattoo-salon.ru\n"
        "🏪 Адрес: ул. Примерная, д. 42\n"
        "⏰ Режим работы: 10:00 - 22:00\n"
        "📅 Выходной: Понедельник"
    )
