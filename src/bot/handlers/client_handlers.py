"""Client-facing handlers for tattoo booking"""
from aiogram import types, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.config.env_loader import load_env
from src.config.config import Config
from src.db.sheets_client import SheetsClient
from src.services.booking_service import BookingService
from src.utils.time_utils import get_next_business_days
from src.utils.validation import is_valid_phone, phone_normalize, sanitize_name
from src.bot.keyboards.common_kb import main_menu, cancel_kb, back_kb
from src.utils.i18n import i18n, LANG_RU, LANG_EN, LANG_HE
import logging

logger = logging.getLogger(__name__)

def get_user_lang(user_id: int) -> str:
    """Helper to get user language with fallback to Russian"""
    return i18n.get_user_language(user_id) or LANG_RU

# Translations for booking messages
TEXTS = {
    "bot_not_configured": {
        LANG_RU: "❌ Бот не настроен",
        LANG_EN: "❌ Bot not configured",
        LANG_HE: "❌ הבוט לא מוגדר"
    },
    "ask_name": {
        LANG_RU: "📝 Как вас зовут?",
        LANG_EN: "📝 What's your name?",
        LANG_HE: "📝 מה שמך?"
    },
    "ask_phone": {
        LANG_RU: "📱 Телефон? (напр., +972501234567)",
        LANG_EN: "📱 Phone? (e.g., +972501234567)",
        LANG_HE: "📱 טלפון? (לדוגמה, +972501234567)"
    },
    "ask_tattoo": {
        LANG_RU: "🎨 Расскажите кратко о вашей идее татуировки:\n\n"
                  "Например:\n"
                  "• Маленький якорь на запястье\n"
                  "• Дракон на спине, 20x30см\n"
                  "• Имя на предплечье\n\n"
                  "Или просто напишите 'консультация', если хотите обсудить лично:",
        LANG_EN: "🎨 Tell me briefly about your tattoo idea:\n\n"
                  "For example:\n"
                  "• Small anchor on wrist\n"
                  "• Dragon on back, 20x30cm\n"
                  "• Name on forearm\n\n"
                  "Or just write 'consultation' if you want to discuss in person:",
        LANG_HE: "🎨 ספר לי בקצרה על רעיון הקעקוע שלך:\n\n"
                 "לדוגמה:\n"
                 "• עוגן קטן על היד\n"
                 "• דרקון על הגב, 20x30 ס\"מ\n"
                 "• שם על האמה\n\n"
                 "או פשוט כתוב 'ייעוץ' אם אתה רוצה לדון באופן אישי:"
    },
    "got_description": {
        LANG_RU: "✅ Понятно! Ваше описание будет сохранено.",
        LANG_EN: "✅ Got it! Your description will be saved.",
        LANG_HE: "✅ הבנתי! התיאור שלך יישמר."
    },
    "choose_date": {
        LANG_RU: "📅 Выберите дату приёма:",
        LANG_EN: "📅 Choose appointment date:",
        LANG_HE: "📅 בחר תאריך תור:"
    },
    "choose_master": {
        LANG_RU: "👨‍🎨 Выберите мастера:",
        LANG_EN: "👨‍🎨 Choose master:",
        LANG_HE: "👨‍🎨 בחר אמן:"
    },
    "choose_slot": {
        LANG_RU: "⏰ Выберите время:",
        LANG_EN: "⏰ Choose time slot:",
        LANG_HE: "⏰ בחר שעה:"
    },
    "cancelled": {
        LANG_RU: "❌ Отменено",
        LANG_EN: "❌ Cancelled",
        LANG_HE: "❌ בוטל"
    },
    "name_too_short": {
        LANG_RU: "❌ Имя слишком короткое (минимум 2 символа)",
        LANG_EN: "❌ Name too short (min 2 chars)",
        LANG_HE: "❌ שם קצר מדי (מינימום 2 תווים)"
    },
    "invalid_phone": {
        LANG_RU: "❌ Неверный формат телефона (напр., +972501234567 или 0501234567)",
        LANG_EN: "❌ Invalid phone format (e.g., +972501234567 or 0501234567)",
        LANG_HE: "❌ פורמט טלפון לא חוקי (לדוגמה, +972501234567 או 0501234567)"
    },
    "no_bookings": {
        LANG_RU: "📋 У вас пока нет бронирований.\nНажмите \"📅 Забронировать\", чтобы создать!",
        LANG_EN: "📋 You have no bookings yet.\nTap \"📅 Book Appointment\" to create one!",
        LANG_HE: "📋 אין לך הזמנות עדיין.\nלחץ על \"📅 הזמן תור\" כדי ליצור!"
    },
    "your_bookings": {
        LANG_RU: "📋 Ваши бронирования:\n\n",
        LANG_EN: "📋 Your Bookings:\n\n",
        LANG_HE: "📋 ההזמנות שלך:\n\n"
    },
    "error": {
        LANG_RU: "❌ Ошибка:",
        LANG_EN: "❌ Error:",
        LANG_HE: "❌ שגיאה:"
    }
}

def get_text(key: str, lang: str) -> str:
    """Get translated text"""
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get(LANG_EN, key))

def is_user_admin(user_id: int) -> bool:
    """Check if user is admin"""
    load_env()
    cfg = Config.from_env()
    return user_id in cfg.ADMIN_USER_IDS

def get_main_menu(user_id: int) -> types.ReplyKeyboardMarkup:
    """Get main menu with admin button if user is admin"""
    user_lang = get_user_lang(user_id)
    is_admin = is_user_admin(user_id)
    return main_menu(user_lang, is_admin)

class ClientStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_consultation = State()
    waiting_for_date = State()
    waiting_for_master = State()
    waiting_for_slot = State()
    confirming_booking = State()

def setup(dp: Dispatcher):
    """Register all client handlers"""
    dp.message.register(cmd_start, Command(commands=["start"]))
    # Admin button - all languages (must be before other handlers)
    dp.message.register(cmd_show_admin, F.text.in_(["👨‍💼 Admin", "👨‍💼 Админ", "👨‍💼 מנהל"]))
    # Book appointment - all languages
    dp.message.register(cmd_book, F.text.in_(["📅 Book Appointment", "📅 Забронировать", "📅 הזמן תור"]))
    # My bookings - all languages
    dp.message.register(cmd_my_bookings, F.text.in_(["📋 My Bookings", "📋 Мои бронирования", "📋 ההזמנות שלי"]))
    # Help - all languages
    dp.message.register(cmd_help, F.text.in_(["❓ Help", "❓ Помощь", "❓ עזרה"]))
    dp.message.register(cmd_cancel, F.text == "❌ Cancel")
    dp.message.register(process_name, ClientStates.waiting_for_name)
    dp.message.register(process_phone, ClientStates.waiting_for_phone)
    dp.message.register(process_consultation, ClientStates.waiting_for_consultation)
    dp.callback_query.register(process_date_choice, F.data.startswith("date:"))
    dp.callback_query.register(process_master_choice, F.data.startswith("master:"))
    dp.callback_query.register(process_slot_choice, F.data.startswith("slot:"))
    dp.callback_query.register(confirm_booking, F.data.startswith("confirm:"))

async def cmd_start(message: types.Message, state: FSMContext):
    """Start command - welcome menu"""
    # Get user's language preference
    from src.utils.i18n import i18n, LANG_RU, LANG_EN, LANG_HE
    user_lang = i18n.get_user_language(message.from_user.id)
    
    # Check if user is admin
    load_env()
    cfg = Config.from_env()
    is_admin = message.from_user.id in cfg.ADMIN_USER_IDS
    
    # Welcome messages in different languages
    welcome_messages = {
        LANG_RU: "🎨 Добро пожаловать в Tattoo Studio!\n\nЗабронируйте свою идеальную татуировку 🔥",
        LANG_EN: "🎨 Welcome to Tattoo Studio!\n\nBook your perfect tattoo appointment 🔥",
        LANG_HE: "🎨 ברוכים הבאים ל-Tattoo Studio!\n\nהזמן את קעקוע החלומות שלך 🔥"
    }
    
    await message.answer(
        welcome_messages.get(user_lang, welcome_messages[LANG_RU]),
        reply_markup=main_menu(user_lang, is_admin)
    )
    await state.clear()

async def cmd_show_admin(message: types.Message):
    """Show admin panel - redirect to admin handlers"""
    load_env()
    cfg = Config.from_env()
    if message.from_user.id not in cfg.ADMIN_USER_IDS:
        await message.answer("❌ Not admin")
        return
    
    # Import here to avoid circular dependency
    from src.bot.handlers.admin_handlers import cmd_admin
    await cmd_admin(message)

async def cmd_book(message: types.Message, state: FSMContext):
    """Start booking - ask name"""
    user_lang = get_user_lang(message.from_user.id)
    load_env()
    cfg = Config.from_env()
    if not cfg.SPREADSHEET_ID:
        await message.answer(get_text("bot_not_configured", user_lang))
        return
    await message.answer(get_text("ask_name", user_lang), reply_markup=cancel_kb())
    await state.set_state(ClientStates.waiting_for_name)

async def cmd_my_bookings(message: types.Message):
    """Show user's bookings"""
    user_lang = get_user_lang(message.from_user.id)
    load_env()
    cfg = Config.from_env()
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        bs = BookingService(sc, cfg.SPREADSHEET_ID)
        bookings = bs.list_bookings_by_client(message.from_user.id)
        
        if not bookings:
            await message.answer(
                get_text("no_bookings", user_lang),
                reply_markup=get_main_menu(message.from_user.id)
            )
            return
        
        msg = get_text("your_bookings", user_lang)
        for b in bookings:
            status = "✅" if b.get("status") == "confirmed" else "⏳"
            msg += f"{status} {b.get('date')} {b.get('slot_start')}-{b.get('slot_end')}\n"
        
        await message.answer(msg, reply_markup=get_main_menu(message.from_user.id))
    except Exception as e:
        await message.answer(f"{get_text('error', user_lang)} {str(e)[:100]}", reply_markup=get_main_menu(message.from_user.id))
        logger.exception("Error getting bookings")

async def cmd_help(message: types.Message):
    """Show help"""
    user_lang = get_user_lang(message.from_user.id)
    await message.answer(
        "❓ How to Book:\n\n"
        "1. Tap \"📅 Book Appointment\"\n"
        "2. Enter your name\n"
        "3. Enter your phone\n"
        "4. Choose date, master & time\n"
        "5. Confirm booking\n\n"
        "📞 Support: contact@tattoo.studio",
        reply_markup=get_main_menu(message.from_user.id)
    )

async def cmd_cancel(message: types.Message, state: FSMContext):
    """Cancel current operation"""
    user_lang = get_user_lang(message.from_user.id)
    await state.clear()
    await message.answer(get_text("cancelled", user_lang), reply_markup=get_main_menu(message.from_user.id))

async def process_name(message: types.Message, state: FSMContext):
    """Process name"""
    user_lang = get_user_lang(message.from_user.id)
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer(get_text("cancelled", user_lang), reply_markup=get_main_menu(message.from_user.id))
        return
    
    name = sanitize_name(message.text.strip())
    if len(name) < 2:
        await message.answer(get_text("name_too_short", user_lang), reply_markup=cancel_kb())
        return
    await state.update_data(name=name)
    await message.answer(get_text("ask_phone", user_lang), reply_markup=cancel_kb())
    await state.set_state(ClientStates.waiting_for_phone)

async def process_phone(message: types.Message, state: FSMContext):
    """Process phone and ask for tattoo description"""
    user_lang = get_user_lang(message.from_user.id)
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer(get_text("cancelled", user_lang), reply_markup=get_main_menu(message.from_user.id))
        return
    
    if not is_valid_phone(message.text):
        await message.answer(get_text("invalid_phone", user_lang), reply_markup=cancel_kb())
        return
    
    phone = phone_normalize(message.text.strip())
    await state.update_data(phone=phone, telegram_id=message.from_user.id)
    
    # Ask for tattoo description
    await message.answer(
        get_text("ask_tattoo", user_lang),
        reply_markup=cancel_kb()
    )
    await state.set_state(ClientStates.waiting_for_consultation)

async def process_consultation(message: types.Message, state: FSMContext):
    """Process tattoo description and proceed to booking"""
    user_lang = get_user_lang(message.from_user.id)
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer(get_text("cancelled", user_lang), reply_markup=get_main_menu(message.from_user.id))
        return
    
    # Save tattoo description
    tattoo_description = message.text.strip()
    await state.update_data(tattoo_notes=tattoo_description)
    
    await message.answer(get_text("got_description", user_lang), reply_markup=types.ReplyKeyboardRemove())
    await show_date_selection(message, state)

async def show_date_selection(message: types.Message, state: FSMContext):
    """Show date selection calendar"""
    user_lang = get_user_lang(message.from_user.id)
    dates = get_next_business_days(7)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=d, callback_data=f"date:{d}") for d in dates[:3]],
        [types.InlineKeyboardButton(text=d, callback_data=f"date:{d}") for d in dates[3:6]],
    ])
    await message.answer(get_text("choose_date", user_lang), reply_markup=kb)
    await state.set_state(ClientStates.waiting_for_date)

async def process_date_choice(callback: types.CallbackQuery, state: FSMContext):
    """Process date selection"""
    user_lang = get_user_lang(callback.from_user.id)
    date_str = callback.data.split(":")[1]
    await state.update_data(date=date_str)
    load_env()
    cfg = Config.from_env()
    sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
    masters = sc.read_sheet(cfg.SPREADSHEET_ID, "masters")
    if not masters:
        await callback.answer("No masters")
        return
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text=m.get("name"), callback_data=f"master:{m.get('id')}")
    ] for m in masters if m.get("active", "").lower() in ("yes", "true")])
    await callback.message.edit_text(get_text("choose_master", user_lang), reply_markup=kb)
    await callback.answer()

async def process_master_choice(callback: types.CallbackQuery, state: FSMContext):
    """Process master selection"""
    master_id = callback.data.split(":")[1]
    load_env()
    cfg = Config.from_env()
    sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
    
    # Get master name from masters sheet
    masters = sc.read_sheet(cfg.SPREADSHEET_ID, "masters")
    master_name = None
    for m in masters:
        if str(m.get("id")) == str(master_id):
            master_name = m.get("name")
            break
    
    # Save both master_id and master_name
    await state.update_data(master_id=master_id, master_name=master_name or f"Master {master_id}")
    
    user_lang = get_user_lang(callback.from_user.id)
    bs = BookingService(sc, cfg.SPREADSHEET_ID)
    data = await state.get_data()
    slots = bs.list_available_slots(data.get("date"), master_id)
    if not slots:
        await callback.answer("No slots")
        return
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text=f"{s.get('slot_start')}-{s.get('slot_end')}", callback_data=f"slot:{s.get('slot_start')}:{s.get('slot_end')}")
    ] for s in slots[:6]])
    await callback.message.edit_text(get_text("choose_slot", user_lang), reply_markup=kb)
    await callback.answer()

async def process_slot_choice(callback: types.CallbackQuery, state: FSMContext):
    """Process slot selection"""
    parts = callback.data.split(":")
    start, end = parts[1], parts[2]
    await state.update_data(slot_start=start, slot_end=end)
    data = await state.get_data()
    
    # Проверка наличия необходимых данных
    if not data.get('name') or not data.get('date'):
        await callback.answer("❌ Session expired. Please start booking again.", show_alert=True)
        await state.clear()
        await callback.message.edit_text("❌ Session expired. Please start booking again with /start")
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Confirm", callback_data="confirm:yes"),
         types.InlineKeyboardButton(text="❌ Cancel", callback_data="confirm:no")]
    ])
    summary = f"Name: {data['name']}\nDate: {data['date']}\nTime: {start}-{end}\nOK?"
    await callback.message.edit_text(summary, reply_markup=kb)
    await callback.answer()

async def confirm_booking(callback: types.CallbackQuery, state: FSMContext):
    """Confirm booking"""
    if "no" in callback.data:
        await callback.message.edit_text("❌ Booking cancelled")
        await state.clear()
        await callback.answer()
        return
    
    data = await state.get_data()
    
    # Проверка наличия всех необходимых данных
    required_fields = ['name', 'phone', 'date', 'master_name', 'slot_start', 'slot_end']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        await callback.answer(f"❌ Missing data: {', '.join(missing_fields)}. Please start again.", show_alert=True)
        await state.clear()
        await callback.message.edit_text("❌ Session expired. Please start booking again with /start")
        return
    
    load_env()
    cfg = Config.from_env()
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        bs = BookingService(sc, cfg.SPREADSHEET_ID)
        result = bs.create_booking(
            client_telegram_id=callback.from_user.id,
            client_name=data.get("name", ""),
            client_phone=data.get("phone", ""),
            date=data.get("date", ""),
            master_id=data.get("master_id", ""),
            slot_start=data.get("slot_start", ""),
            slot_end=data.get("slot_end", ""),
            notes=data.get("tattoo_notes", "")
        )
        await callback.message.edit_text(
            f"✅ Booking confirmed!\n\n"
            f"📋 ID: {result['booking_id'][:8]}\n"
            f"📅 {data.get('date')}\n"
            f"⏰ {data.get('slot_start')}-{data.get('slot_end')}\n"
            f"📞 We'll contact you at {data.get('phone', 'N/A')}"
        )
        await state.clear()
        logger.info(f"Booking created: {result['booking_id']} for {callback.from_user.id}")
    except Exception as e:
        await callback.message.edit_text(f"❌ Error: {str(e)[:100]}")
        logger.exception("Booking failed")
    await callback.answer()

async def cmd_my_bookings(message: types.Message):
    """Show user's bookings"""
    load_env()
    cfg = Config.from_env()
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        bookings = sc.read_sheet(cfg.SPREADSHEET_ID, "bookings")
        if not bookings:
            await message.answer("No bookings")
            return
        msg = "Bookings:\n" + "\n".join([f"{b['date']} {b['slot_start']}-{b['slot_end']} ({b['status']})" for b in bookings[:5]])
        await message.answer(msg)
    except Exception as e:
        await message.answer(f"Error: {str(e)[:50]}")
