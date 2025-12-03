"""
Расширенный админ-обработчик для управления салоном
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from datetime import datetime, timedelta

from src.bot.keyboards import get_admin_menu, get_main_menu
from src.db.sheets_client import GoogleSheetsClient
from src.services.admin_service import AdminService
from src.services.master_service import MasterService
from src.services.client_service import ClientService
from src.services.booking_service import BookingService
from src.config import get_config

logger = logging.getLogger(__name__)
router = Router()


class AdminStates(StatesGroup):
    """Состояния админ-панели"""
    add_master_name = State()
    add_master_specialty = State()
    add_master_phone = State()
    add_procedure_name = State()
    add_procedure_price = State()
    view_client_details = State()


def get_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели с кнопками"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Клиенты", callback_data="admin_clients")],
        [InlineKeyboardButton(text="👨‍💼 Мастера", callback_data="admin_masters")],
        [InlineKeyboardButton(text="💇 Услуги", callback_data="admin_procedures")],
        [InlineKeyboardButton(text="📅 Записи", callback_data="admin_bookings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")],
        [InlineKeyboardButton(text="🔙 Вернуться", callback_data="admin_back")]
    ])


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])


@router.message(F.text == "⚙️ Администратор")
async def admin_panel(message: Message):
    """Главная админ-панель"""
    config = get_config()
    
    if message.from_user.id not in config.admin_ids:
        await message.answer("❌ Доступ запрещен. Вы не администратор.")
        return
    
    await message.answer(
        """⚙️ АДМИНИСТРАТОРСКАЯ ПАНЕЛЬ

Выберите раздел для управления:""",
        reply_markup=get_admin_dashboard_keyboard()
    )


@router.callback_query(F.data == "admin_clients")
async def view_clients(callback: CallbackQuery):
    """Просмотр списка клиентов"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    client_service = ClientService(sheets)
    
    clients = client_service.get_all_clients()
    
    if not clients:
        await callback.message.edit_text(
            "👥 КЛИЕНТЫ\n\nНет клиентов в базе",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    # Показываем первых 5 клиентов с кнопками
    text = f"""👥 СПИСОК КЛИЕНТОВ ({len(clients)} всего)

"""
    
    buttons = []
    for i, client in enumerate(clients[:10]):
        name = client.get('name', 'Unknown')
        client_id = client.get('id', str(i))
        
        text += f"{i+1}. {name}\n"
        buttons.append([InlineKeyboardButton(
            text=f"👤 {name}",
            callback_data=f"client_view_{client_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("client_view_"))
async def view_client_details(callback: CallbackQuery):
    """Просмотр деталей клиента"""
    client_id = callback.data.split("_")[2]
    
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    client_service = ClientService(sheets)
    booking_service = BookingService(sheets)
    
    client = client_service.get_client(client_id)
    
    if not client:
        await callback.message.edit_text(
            "❌ Клиент не найден",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    bookings = booking_service.get_user_bookings(client_id)
    
    text = f"""👤 ПРОФИЛЬ КЛИЕНТА

📝 Имя: {client.get('name', 'N/A')}
📱 Телефон: {client.get('phone', 'N/A')}
📧 Email: {client.get('email', 'N/A')}
🆔 Telegram: {client.get('telegram_id', 'N/A')}
📅 Зареги: {client.get('created_at', 'N/A')}
📊 Всего визитов: {client.get('total_bookings', '0')}
💰 Потрачено: {client.get('total_spent', '0')} ₽

📅 Последние записи: {len(bookings)}"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"client_delete_{client_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_clients")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_masters")
async def view_masters(callback: CallbackQuery):
    """Просмотр списка мастеров"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    master_service = MasterService(sheets)
    
    masters = master_service.get_all_masters()
    
    text = f"""👨‍💼 МАСТЕРА ({len(masters)} всего)

"""
    
    buttons = []
    for i, master in enumerate(masters):
        name = master.get('name', 'Unknown')
        master_id = master.get('id', str(i))
        spec = master.get('specialty', master.get('specialization', ''))
        
        text += f"{i+1}. {name} ({spec})\n"
        buttons.append([InlineKeyboardButton(
            text=f"👨‍💼 {name}",
            callback_data=f"master_view_{master_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="➕ Добавить мастера", callback_data="master_add")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("master_view_"))
async def view_master_details(callback: CallbackQuery):
    """Просмотр деталей мастера"""
    master_id = callback.data.split("_")[2]
    
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    master_service = MasterService(sheets)
    
    master = master_service.get_master(master_id)
    
    if not master:
        await callback.message.edit_text(
            "❌ Мастер не найден",
            reply_markup=get_back_keyboard()
        )
        await callback.answer()
        return
    
    text = f"""👨‍💼 ПРОФИЛЬ МАСТЕРА

📝 Имя: {master.get('name', 'N/A')}
🎨 Специальность: {master.get('specialty', master.get('specialization', 'N/A'))}
⭐ Рейтинг: {master.get('rating', '0')}/5
📱 Телефон: {master.get('phone', 'N/A')}
📸 Instagram: {master.get('instagram', 'N/A')}
💰 Цена: {master.get('price', 'N/A')} ₽
⏰ Опыт: {master.get('experience', 'N/A')} лет"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"master_edit_{master_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"master_delete_{master_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_masters")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_procedures")
async def view_procedures(callback: CallbackQuery):
    """Просмотр услуг"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    
    from src.services.procedure_service import ProcedureService
    proc_service = ProcedureService(sheets)
    
    procedures = proc_service.get_all_procedures()
    
    text = f"""💇 УСЛУГИ ({len(procedures)} всего)

"""
    
    buttons = []
    for i, proc in enumerate(procedures):
        name = proc.get('name', 'Unknown')
        price = proc.get('price', '0')
        proc_id = proc.get('id', str(i))
        
        text += f"{i+1}. {name} - {price} ₽\n"
        buttons.append([InlineKeyboardButton(
            text=f"💇 {name}",
            callback_data=f"proc_view_{proc_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="➕ Добавить услугу", callback_data="proc_add")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_bookings")
async def view_bookings(callback: CallbackQuery):
    """Просмотр всех записей"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    booking_service = BookingService(sheets)
    
    bookings = booking_service.get_all_bookings()
    
    # Фильтруем по статусу
    pending = [b for b in bookings if b.get('status', '').lower() in ['pending', 'ожидание']]
    confirmed = [b for b in bookings if b.get('status', '').lower() in ['confirmed', 'подтверждена']]
    
    text = f"""📅 ВСЕ ЗАПИСИ

✅ Подтвержденные: {len(confirmed)}
⏳ На рассмотрении: {len(pending)}
📋 Всего: {len(bookings)}
"""
    
    buttons = [
        [InlineKeyboardButton(text=f"✅ Подтвержденные ({len(confirmed)})", callback_data="bookings_confirmed")],
        [InlineKeyboardButton(text=f"⏳ На рассмотрении ({len(pending)})", callback_data="bookings_pending")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def view_statistics(callback: CallbackQuery):
    """Просмотр статистики"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    admin_service = AdminService(sheets)
    
    stats = admin_service.get_dashboard_stats()
    
    text = f"""📊 СТАТИСТИКА

👥 Клиентов: {stats.get('total_clients', 0)}
👨‍💼 Мастеров: {stats.get('total_masters', 0)}
💇 Услуг: {stats.get('total_procedures', 0)}
📅 Записей: {stats.get('total_bookings', 0)}
✅ Подтверждено: {stats.get('confirmed_bookings', 0)}
⏳ На рассмотрении: {stats.get('pending_bookings', 0)}

📈 Общий доход: {stats.get('total_income', 0)} ₽
⭐ Средний рейтинг: {stats.get('avg_rating', 0)}/5"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    """Настройки салона"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    
    text = """⚙️ НАСТРОЙКИ САЛОНА

📝 Здесь можно изменить параметры работы салона."""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Контакты", callback_data="settings_contacts")],
        [InlineKeyboardButton(text="🕐 Режим работы", callback_data="settings_hours")],
        [InlineKeyboardButton(text="💰 Валюта", callback_data="settings_currency")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Вернуться в главное меню админ-панели"""
    await callback.message.edit_text(
        """⚙️ АДМИНИСТРАТОРСКАЯ ПАНЕЛЬ

Выберите раздел для управления:""",
        reply_markup=get_admin_dashboard_keyboard()
    )
    await callback.answer()


# ==================== Дополнительные обработчики ====================

@router.callback_query(F.data == "master_add")
async def add_master_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления мастера"""
    await state.set_state(AdminStates.add_master_name)
    await callback.message.edit_text("📝 Введите имя мастера:")
    await callback.answer()


@router.callback_query(F.data == "proc_add")
async def add_procedure_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления услуги"""
    await state.set_state(AdminStates.add_procedure_name)
    await callback.message.edit_text("📝 Введите название услуги:")
    await callback.answer()


@router.callback_query(F.data == "bookings_confirmed")
async def view_confirmed_bookings(callback: CallbackQuery):
    """Подтвержденные записи"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    booking_service = BookingService(sheets)
    
    bookings = booking_service.get_all_bookings()
    confirmed = [b for b in bookings if b.get('status', '').lower() in ['confirmed', 'подтверждена']]
    
    text = f"""✅ ПОДТВЕРЖДЕННЫЕ ЗАПИСИ ({len(confirmed)})

"""
    
    for booking in confirmed[:10]:
        date = booking.get('date', 'N/A')
        time = booking.get('time', 'N/A')
        client = booking.get('client_name', 'N/A')
        text += f"📅 {date} {time}\n👤 {client}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "bookings_pending")
async def view_pending_bookings(callback: CallbackQuery):
    """Записи на рассмотрении"""
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    booking_service = BookingService(sheets)
    
    bookings = booking_service.get_all_bookings()
    pending = [b for b in bookings if b.get('status', '').lower() in ['pending', 'ожидание']]
    
    text = f"""⏳ ЗАПИСИ НА РАССМОТРЕНИИ ({len(pending)})

"""
    
    buttons = []
    for booking in pending[:10]:
        date = booking.get('date', 'N/A')
        time = booking.get('time', 'N/A')
        client = booking.get('client_name', 'N/A')
        booking_id = booking.get('id', 'unknown')
        
        text += f"📅 {date} {time} - {client}\n"
        buttons.append([
            InlineKeyboardButton(text=f"✅ {date} {time}", callback_data=f"approve_booking_{booking_id}"),
            InlineKeyboardButton(text="❌", callback_data=f"reject_booking_{booking_id}")
        ])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_bookings")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
