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

def get_masters_keyboard(masters: list) -> InlineKeyboardMarkup:
    """Keyboard with masters as buttons"""
    buttons = []
    
    for master in masters:
        master_id = master.get('id', master.get('name', 'unknown'))
        master_name = master.get('name', 'Unknown')
        master_spec = master.get('specialty', master.get('specialization', ''))
        
        button_text = f"👨‍💼 {master_name}"
        if master_spec:
            button_text += f" ({master_spec})"
        
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"master_{master_id}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_procedures_keyboard(procedures: list) -> InlineKeyboardMarkup:
    """Keyboard with procedures as buttons"""
    buttons = []
    
    for proc in procedures:
        proc_id = proc.get('id', proc.get('name', 'unknown'))
        proc_name = proc.get('name', 'Unknown')
        proc_price = proc.get('price', '')
        
        button_text = f"💇 {proc_name}"
        if proc_price:
            button_text += f" ({proc_price}₽)"
        
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"proc_{proc_id}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_slots_keyboard(slots: list, slot_type: str = "time") -> InlineKeyboardMarkup:
    """Keyboard with time or date slots"""
    buttons = []
    
    # Добавляем слоты по 2 в ряд
    for i in range(0, len(slots), 2):
        row = []
        for j in range(2):
            if i + j < len(slots):
                slot = slots[i + j]
                
                if slot_type == "time":
                    button_text = f"⏰ {slot}"
                    callback = f"time_{slot}"
                elif slot_type == "date":
                    button_text = f"📅 {slot}"
                    callback = f"date_{slot}"
                else:
                    button_text = str(slot)
                    callback = f"{slot_type}_{slot}"
                
                row.append(InlineKeyboardButton(text=button_text, callback_data=callback))
        
        if row:
            buttons.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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
