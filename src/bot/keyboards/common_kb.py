"""Common keyboards"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from src.utils.i18n import i18n, LANG_RU, LANG_EN, LANG_HE

def yes_no_kb(language: str = LANG_RU):
    """Simple yes/no keyboard"""
    yes_text = {"ru": "✅ Да", "en": "✅ Yes", "he": "✅ כן"}.get(language, "✅ Yes")
    no_text = {"ru": "❌ Нет", "en": "❌ No", "he": "❌ לא"}.get(language, "❌ No")
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=yes_text), KeyboardButton(text=no_text)]
    ], resize_keyboard=True)

def main_menu(language: str = LANG_RU, is_admin: bool = False):
    """Main menu keyboard - supports all languages and admin mode"""
    buttons = {
        LANG_RU: [
            ["📅 Забронировать", "📋 Мои бронирования"],
            ["❓ Помощь", "🌐 Язык"]
        ],
        LANG_EN: [
            ["📅 Book Appointment", "📋 My Bookings"],
            ["❓ Help", "🌐 Language"]
        ],
        LANG_HE: [
            ["📅 הזמן תור", "📋 ההזמנות שלי"],
            ["❓ עזרה", "🌐 שפה"]
        ]
    }
    
    button_list = list(buttons.get(language, buttons[LANG_RU]))
    
    # Add admin button if user is admin
    if is_admin:
        admin_text = {
            LANG_RU: "👨‍💼 Админ",
            LANG_EN: "👨‍💼 Admin",
            LANG_HE: "👨‍💼 מנהל"
        }.get(language, "👨‍💼 Admin")
        button_list.append([admin_text])
    
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in button_list],
        resize_keyboard=True
    )

def admin_menu(language: str = LANG_RU):
    """Admin menu keyboard - supports all languages"""
    buttons = {
        LANG_RU: [
            ["📊 Панель", "👨‍🎨 Добавить"],
            ["⏰ Слот", "📅 Синхро"],
            ["👥 Клиенты", "📋 Бронирования"],
            ["✏️ Редактировать клиентов", "✏️ Редактировать мастеров"],
            ["✏️ Редактировать услуги"],
            ["💬 Чат", "📊 Статистика"],
            ["🏠 Главное меню", "🌐 Язык"]
        ],
        LANG_EN: [
            ["📊 Dashboard", "👨‍🎨 Add Master"],
            ["⏰ Add Slot", "📅 Sync Calendar"],
            ["👥 View Clients", "📋 View Bookings"],
            ["✏️ Edit Clients", "✏️ Edit Masters"],
            ["✏️ Edit Services"],
            ["💬 Admin Chat", "📊 Chat Stats"],
            ["🏠 Main Menu", "🌐 Language"]
        ],
        LANG_HE: [
            ["📊 לוח בקרה", "👨‍🎨 הוסף אומן"],
            ["⏰ הוסף משבצת", "📅 סנכרן לוח"],
            ["👥 צפה בלקוחות", "📋 צפה בהזמנות"],
            ["✏️ ערוך לקוחות", "✏️ ערוך אמנים"],
            ["✏️ ערוך שירותים"],
            ["💬 צ'אט", "📊 סטטיסטיקה"],
            ["🏠 תפריט ראשי", "🌐 שפה"]
        ]
    }
    
    button_list = buttons.get(language, buttons[LANG_RU])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in button_list],
        resize_keyboard=True
    )

def cancel_kb(language: str = LANG_RU):
    """Cancel button keyboard - supports all languages"""
    cancel_text = {"ru": "❌ Отмена", "en": "❌ Cancel", "he": "❌ ביטול"}.get(language, "❌ Cancel")
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=cancel_text)]
    ], resize_keyboard=True)

def back_kb(language: str = LANG_RU):
    """Back button keyboard - supports all languages"""
    back_text = {"ru": "⬅️ Назад", "en": "⬅️ Back", "he": "⬅️ חזור"}.get(language, "⬅️ Back")
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=back_text)]
    ], resize_keyboard=True)

def language_selection_kb():
    """Language selection keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇧 English")],
            [KeyboardButton(text="🇮🇱 עברית")],
        ],
        resize_keyboard=True
    )
