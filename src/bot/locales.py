"""Multilingual support"""

TEXTS = {
    "en": {
        "start_message": "👋 Hello, {name}!\n\n🎨 I'm INKA Tattoo Studio bot.\n\nI can help you:\n• Book an appointment\n• View available time slots\n• Manage your bookings\n\nChoose an option:",
        "menu_book": "📅 Make Appointment",
        "menu_bookings": "📋 My Appointments",
        "menu_info": "ℹ️ Information",
        "menu_language": "🌐 Language",
        
        "choose_language": "🌐 Choose your language:",
        "language_changed": "✅ Language changed to English",
        
        "describe_tattoo": "🎨 Describe the tattoo you want:\n\nFor example:\n• Dragon on back, 20x30cm\n• Small rose on wrist\n• Latin text on forearm",
        "choose_date": "📅 Choose a convenient date:",
        "available_slots": "🕐 Choose convenient time for {date}:",
        "slots_error": "⚠️ Could not load available time.\nPlease try choosing another date.",
        "invalid_time": "⚠️ Invalid time format. Use HH:MM (e.g., 14:00)",
        "enter_phone": "📱 Please provide your phone number:\n\nFormat: +1234567890 or 1234567890",
        
        "confirm_booking": "✅ Booking confirmation:\n\n📝 Description: {description}\n📅 Date: {date}\n🕐 Time: {time} - {end_time}\n📱 Phone: {phone}\n\nConfirm booking? (Yes/No)",
        "booking_created": "✅ Booking created!\n\n📋 Booking ID: {booking_id}\n📅 Date: {date}\n🕐 Time: {time} - {end_time}\n\nWe'll send a reminder one day before your session.",
        "booking_error": "❌ Error creating booking.\nPlease try again later or contact @admin",
        "booking_cancelled": "❌ Booking cancelled.",
        
        "no_bookings": "📭 You have no appointments yet.\n\nPress '📅 Make Appointment' to create one.",
        "your_bookings": "📋 Your appointments:\n\n",
        "bookings_error": "❌ Error loading appointments",
        
        "info_text": "ℹ️ INKA Tattoo Studio\n\n📍 Address: [your address]\n📞 Phone: [your phone]\n🌐 Instagram: @inka_tattoo\n\n⏰ Working hours:\nMon-Fri: 10:00 - 20:00\nSat-Sun: 12:00 - 18:00\n\n💰 Prices from $50 for small work",
        "unknown_command": "🤔 Command not recognized.\n\nPlease use menu buttons:",
    },
    
    "ru": {
        "start_message": "👋 Привет, {name}!\n\n🎨 Я бот тату-студии INKA.\n\nЯ помогу вам:\n• Записаться на сеанс\n• Посмотреть свободное время\n• Управлять записями\n\nВыберите действие:",
        "menu_book": "📅 Записаться",
        "menu_bookings": "📋 Мои записи",
        "menu_info": "ℹ️ Информация",
        "menu_language": "🌐 Язык",
        
        "choose_language": "🌐 Выберите язык:",
        "language_changed": "✅ Язык изменен на Русский",
        
        "describe_tattoo": "🎨 Опишите какую татуировку хотите сделать:\n\nНапример:\n• Дракон на спине, 20x30см\n• Маленькая роза на запястье\n• Надпись на латыни на предплечье",
        "choose_date": "📅 Выберите удобную дату:",
        "available_slots": "🕐 Выберите удобное время на {date}:",
        "slots_error": "⚠️ Не удалось загрузить доступное время.\nПопробуйте выбрать другую дату.",
        "invalid_time": "⚠️ Неверный формат времени. Используйте ЧЧ:ММ (например, 14:00)",
        "enter_phone": "📱 Пожалуйста, укажите ваш номер телефона:\n\nФормат: +1234567890 или 1234567890",
        
        "confirm_booking": "✅ Подтверждение записи:\n\n📝 Описание: {description}\n📅 Дата: {date}\n🕐 Время: {time} - {end_time}\n📱 Телефон: {phone}\n\nПодтвердите запись? (Да/Нет)",
        "booking_created": "✅ Запись создана!\n\n📋 Номер записи: {booking_id}\n📅 Дата: {date}\n🕐 Время: {time} - {end_time}\n\nМы пришлём напоминание за день до сеанса.",
        "booking_error": "❌ Ошибка при создании записи.\nПопробуйте позже или напишите @admin",
        "booking_cancelled": "❌ Запись отменена.",
        
        "no_bookings": "📭 У вас пока нет записей.\n\nНажмите '📅 Записаться' чтобы создать запись.",
        "your_bookings": "📋 Ваши записи:\n\n",
        "bookings_error": "❌ Ошибка при загрузке записей",
        
        "info_text": "ℹ️ INKA Tattoo Studio\n\n📍 Адрес: [ваш адрес]\n📞 Телефон: [ваш телефон]\n🌐 Instagram: @inka_tattoo\n\n⏰ Часы работы:\nПн-Пт: 10:00 - 20:00\nСб-Вс: 12:00 - 18:00\n\n💰 Цены от $50 за маленькую работу",
        "unknown_command": "🤔 Не понял команду.\n\nИспользуйте кнопки меню:",
    },
    
    "he": {
        "start_message": "👋 שלום, {name}!\n\n🎨 אני בוט של אולפן קעקועים INKA.\n\nאני יכול לעזור לך:\n• לקבוע פגישה\n• לראות זמנים פנויים\n• לנהל הזמנות\n\nבחר אפשרות:",
        "menu_book": "📅 קביעת פגישה",
        "menu_bookings": "📋 הפגישות שלי",
        "menu_info": "ℹ️ מידע",
        "menu_language": "🌐 שפה",
        
        "choose_language": "🌐 בחר שפה:",
        "language_changed": "✅ השפה שונתה לעברית",
        
        "describe_tattoo": "🎨 תאר את הקעקוע שאתה רוצה:\n\nלדוגמה:\n• דרקון על הגב, 20x30 ס״מ\n• ורד קטן על פרק היד\n• כתובת לטינית על האמה",
        "choose_date": "📅 בחר תאריך נוח:",
        "available_slots": "🕐 בחר שעה נוחה ל-{date}:",
        "slots_error": "⚠️ לא ניתן לטעון זמנים זמינים.\nנסה לבחור תאריך אחר.",
        "invalid_time": "⚠️ פורמט זמן לא תקין. השתמש ב-HH:MM (לדוגמה, 14:00)",
        "enter_phone": "📱 אנא ספק את מספר הטלפון שלך:\n\nפורמט: +1234567890 או 1234567890",
        
        "confirm_booking": "✅ אישור הזמנה:\n\n📝 תיאור: {description}\n📅 תאריך: {date}\n🕐 זמן: {time} - {end_time}\n📱 טלפון: {phone}\n\nלאשר הזמנה? (כן/לא)",
        "booking_created": "✅ ההזמנה נוצרה!\n\n📋 מספר הזמנה: {booking_id}\n📅 תאריך: {date}\n🕐 זמן: {time} - {end_time}\n\nנשלח תזכורת יום לפני המפגש.",
        "booking_error": "❌ שגיאה ביצירת הזמנה.\nנסה שוב מאוחר יותר או צור קשר עם @admin",
        "booking_cancelled": "❌ ההזמנה בוטלה.",
        
        "no_bookings": "📭 אין לך הזמנות עדיין.\n\nלחץ על '📅 קביעת פגישה' כדי ליצור אחת.",
        "your_bookings": "📋 הפגישות שלך:\n\n",
        "bookings_error": "❌ שגיאה בטעינת הזמנות",
        
        "info_text": "ℹ️ INKA Tattoo Studio\n\n📍 כתובת: [הכתובת שלך]\n📞 טלפון: [הטלפון שלך]\n🌐 Instagram: @inka_tattoo\n\n⏰ שעות פעילות:\nא׳-ה׳: 10:00 - 20:00\nו׳-ש׳: 12:00 - 18:00\n\n💰 מחירים מ-$50 לעבודה קטנה",
        "unknown_command": "🤔 הפקודה לא זוהתה.\n\nאנא השתמש בכפתורי התפריט:",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    """Get localized text"""
    text = TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text

def get_menu_buttons(lang: str) -> list:
    """Get menu button texts for language"""
    return [
        get_text(lang, "menu_book"),
        get_text(lang, "menu_bookings"),
        get_text(lang, "menu_info"),
        get_text(lang, "menu_language")
    ]
