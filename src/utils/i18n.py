"""
Internationalization (i18n) module for multi-language support
Supports: Russian, English, Hebrew
"""

from typing import Dict, Optional

# Language codes
LANG_RU = "ru"
LANG_EN = "en"
LANG_HE = "he"

SUPPORTED_LANGUAGES = [LANG_RU, LANG_EN, LANG_HE]

# Translations dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Main Menu
    "main_menu": {
        LANG_RU: "📅 Забронировать\n📋 Мои бронирования\n❓ Помощь",
        LANG_EN: "📅 Book Appointment\n📋 My Bookings\n❓ Help",
        LANG_HE: "📅 הזמן תור\n📋 ההזמנות שלי\n❓ עזרה",
    },
    "book_appointment": {
        LANG_RU: "📅 Забронировать",
        LANG_EN: "📅 Book Appointment",
        LANG_HE: "📅 הזמן תור",
    },
    "my_bookings": {
        LANG_RU: "📋 Мои бронирования",
        LANG_EN: "📋 My Bookings",
        LANG_HE: "📋 ההזמנות שלי",
    },
    "help": {
        LANG_RU: "❓ Помощь",
        LANG_EN: "❓ Help",
        LANG_HE: "❓ עזרה",
    },
    # Common
    "cancel": {
        LANG_RU: "❌ Отмена",
        LANG_EN: "❌ Cancel",
        LANG_HE: "❌ ביטול",
    },
    "back": {
        LANG_RU: "⬅️ Назад",
        LANG_EN: "⬅️ Back",
        LANG_HE: "⬅️ חזור",
    },
    # Admin
    "admin_menu": {
        LANG_RU: "📊 Админ-панель",
        LANG_EN: "📊 Admin Panel",
        LANG_HE: "📊 לוח בקרה",
    },
    "admin_chat": {
        LANG_RU: "💬 Чат администратора",
        LANG_EN: "💬 Admin Chat",
        LANG_HE: "💬 צ'אט מנהל",
    },
    "chat_stats": {
        LANG_RU: "📊 Статистика чата",
        LANG_EN: "📊 Chat Stats",
        LANG_HE: "📊 סטטיסטיקת צ'אט",
    },
    # Booking flow
    "enter_name": {
        LANG_RU: "👤 Введите ваше имя:",
        LANG_EN: "👤 Enter your name:",
        LANG_HE: "👤 הכנס את שמך:",
    },
    "enter_phone": {
        LANG_RU: "📱 Введите номер телефона:",
        LANG_EN: "📱 Enter your phone number:",
        LANG_HE: "📱 הכנס את מספר הטלפון שלך:",
    },
    "select_language": {
        LANG_RU: "🌐 Выберите язык / Select language / בחר שפה",
        LANG_EN: "🌐 Select your language",
        LANG_HE: "🌐 בחר שפה",
    },
    "language_selected": {
        LANG_RU: "✅ Язык установлен на Русский",
        LANG_EN: "✅ Language set to English",
        LANG_HE: "✅ השפה הוגדרה לעברית",
    },
    # Admin Chat
    "welcome_admin_chat": {
        LANG_RU: "👋 Добро пожаловать в чат администратора!\n\nВы можете общаться естественно о:\n• Клиентах\n• Мастерах\n• Ценах\n• Расписании\n\nВсё будет автоматически сохранено.",
        LANG_EN: "👋 Welcome to Admin Chat!\n\nYou can naturally discuss:\n• Clients\n• Masters\n• Prices\n• Schedule\n\nEverything will be automatically saved.",
        LANG_HE: "👋 ברוכים הבאים לצ'אט המנהל!\n\nאתה יכול לדבר בטבעיות על:\n• לקוחות\n• אמנים\n• מחירים\n• לוח זמנים\n\nהכל יישמר באופן אוטומטי.",
    },
    "saved": {
        LANG_RU: "✅ Сохранено!",
        LANG_EN: "✅ Saved!",
        LANG_HE: "✅ נשמר!",
    },
    "processing": {
        LANG_RU: "🤔 Обрабатываю...",
        LANG_EN: "🤔 Processing...",
        LANG_HE: "🤔 מעבד...",
    },
    "error": {
        LANG_RU: "❌ Ошибка:",
        LANG_EN: "❌ Error:",
        LANG_HE: "❌ שגיאה:",
    },
    # Categories
    "client_info": {
        LANG_RU: "👥 Информация о клиентах",
        LANG_EN: "👥 Client Information",
        LANG_HE: "👥 מידע לקוח",
    },
    "master_info": {
        LANG_RU: "👨‍🎨 Информация о мастерах",
        LANG_EN: "👨‍🎨 Master Information",
        LANG_HE: "👨‍🎨 מידע אמן",
    },
    "appointment_details": {
        LANG_RU: "📅 Детали бронирования",
        LANG_EN: "📅 Appointment Details",
        LANG_HE: "📅 פרטי התור",
    },
    "financial": {
        LANG_RU: "💰 Финансовая информация",
        LANG_EN: "💰 Financial Information",
        LANG_HE: "💰 מידע כספי",
    },
}


class I18n:
    """Internationalization handler"""

    def __init__(self):
        self.default_language = LANG_RU
        self.user_languages: Dict[int, str] = {}

    def set_user_language(self, user_id: int, language: str) -> bool:
        """Set language for user"""
        if language not in SUPPORTED_LANGUAGES:
            return False
        self.user_languages[user_id] = language
        return True

    def get_user_language(self, user_id: int) -> str:
        """Get user language or default"""
        return self.user_languages.get(user_id, self.default_language)

    def detect_language(self, text: str) -> Optional[str]:
        """Detect language from text"""
        # Simple detection based on Cyrillic, Latin, Hebrew characters
        if any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in text):
            return LANG_RU
        elif any(ord(c) >= 0x0590 and ord(c) <= 0x05FF for c in text):
            return LANG_HE
        elif all(ord(c) < 0x0400 or ord(c) > 0x04FF for c in text if c.isalpha()):
            return LANG_EN
        return None

    def get(self, key: str, language: Optional[str] = None) -> str:
        """Get translated string"""
        if language is None:
            language = self.default_language

        if key not in TRANSLATIONS:
            return key

        return TRANSLATIONS[key].get(language, TRANSLATIONS[key].get(self.default_language, key))

    def t(
        self, key: str, user_id: Optional[int] = None, language: Optional[str] = None
    ) -> str:
        """Translate with user context"""
        if language is None and user_id is not None:
            language = self.get_user_language(user_id)
        elif language is None:
            language = self.default_language

        return self.get(key, language)

    def get_language_buttons(self) -> Dict[str, str]:
        """Get language selection buttons"""
        return {
            "🇷🇺 Русский": LANG_RU,
            "🇬🇧 English": LANG_EN,
            "🇮🇱 עברית": LANG_HE,
        }

    def is_cancel_button(self, text: str) -> bool:
        """Check if text is a cancel button in any language"""
        return text in ["❌ Отмена", "❌ Cancel", "❌ ביטול"]

    def is_back_button(self, text: str) -> bool:
        """Check if text is a back button in any language"""
        return text in ["⬅️ Назад", "⬅️ Back", "⬅️ חזור"]

    def is_language_button(self, text: str) -> bool:
        """Check if text is a language button"""
        return text in ["🌐 Язык", "🌐 Language", "🌐 שפה"]


# Global instance
i18n = I18n()
