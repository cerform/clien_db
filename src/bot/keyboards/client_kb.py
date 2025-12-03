"""Client keyboards"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict
from src.bot.locales import get_text

def get_main_menu(lang: str = "en") -> ReplyKeyboardMarkup:
    """Главное меню клиента"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, "menu_book"))],
            [KeyboardButton(text=get_text(lang, "menu_bookings"))],
            [KeyboardButton(text=get_text(lang, "menu_info"))],
            [KeyboardButton(text=get_text(lang, "menu_language"))]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇮🇱 עברית", callback_data="lang:he")]
    ])
    return keyboard

def get_calendar_keyboard() -> InlineKeyboardMarkup:
    """Календарь на ближайшие 14 дней"""
    from datetime import datetime, timedelta
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    today = datetime.now()
    
    row = []
    for i in range(14):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        day_name = date.strftime("%a")[:2]  # Mo, Tu, We
        
        row.append(InlineKeyboardButton(
            text=f"{day_name}\n{date.strftime('%d.%m')}",
            callback_data=f"date:{date_str}"
        ))
        
        # 2 кнопки в ряд
        if len(row) == 2:
            kb.inline_keyboard.append(row)
            row = []
    
    if row:  # Добавляем остаток
        kb.inline_keyboard.append(row)
    
    return kb

def get_time_slots_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с временными слотами"""
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Слоты по 2 часа: 10:00-12:00, 12:00-14:00, и т.д.
    slots = [
        ("10:00", "12:00"),
        ("12:00", "14:00"),
        ("14:00", "16:00"),
        ("16:00", "18:00"),
        ("18:00", "20:00"),
    ]
    
    for start, end in slots:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🕐 {start} - {end}",
                callback_data=f"time:{start}:{end}"
            )
        ])
    
    return kb

def slots_keyboard(slots: List[Dict]) -> InlineKeyboardMarkup:
    """Keyboard for time slots"""
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for s in slots[:10]:
        start = s.get("slot_start", "")
        end = s.get("slot_end", "")
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{start} - {end}",
                callback_data=f"slot:{start}:{end}"
            )
        ])
    return kb

def masters_keyboard(masters: List[Dict]) -> InlineKeyboardMarkup:
    """Keyboard for selecting master"""
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for m in masters:
        if m.get("active", "").lower() in ("yes", "true"):
            kb.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"👨‍🎨 {m.get('name', 'Unknown')}",
                    callback_data=f"master:{m.get('id')}"
                )
            ])
    return kb

def dates_keyboard(dates: List[str]) -> InlineKeyboardMarkup:
    """Keyboard for selecting date"""
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for d in dates[:7]:
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=d, callback_data=f"date:{d}")
        ])
    return kb

def confirm_kb() -> InlineKeyboardMarkup:
    """Confirmation keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data="confirm:yes"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="confirm:no")
        ]
    ])
