from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    """Main menu for all users"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Личный кабинет")],
            [KeyboardButton(text="📞 Контакты")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_client_menu() -> ReplyKeyboardMarkup:
    """Client menu"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записать на прием")],
            [KeyboardButton(text="📋 Мои записи")],
            [KeyboardButton(text="👥 Выбрать мастера")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_master_menu() -> ReplyKeyboardMarkup:
    """Master menu"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Мой календарь")],
            [KeyboardButton(text="✅ Подтвердить запись")],
            [KeyboardButton(text="❌ Отклонить запись")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_admin_menu() -> ReplyKeyboardMarkup:
    """Admin menu"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Управление клиентами")],
            [KeyboardButton(text="👨‍💼 Управление мастерами")],
            [KeyboardButton(text="📅 Управление записями")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Cancel keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm/Cancel inline keyboard"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="confirm"),
                InlineKeyboardButton(text="❌ Нет", callback_data="cancel")
            ]
        ]
    )

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Back button inline keyboard"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
        ]
    )
