#!/usr/bin/env python3
"""
📋 ИНСТРУКЦИЯ: Где и как добавить Google Calendar ID для мастеров ИНКИ
═══════════════════════════════════════════════════════════════════════

🎯 СУТЬ:
   INKA получает Google Calendar ID каждого мастера из Google Sheets.
   ID используется для:
   • Получения расписания мастера
   • Проверки занятости (busy times)
   • Создания новых событий (бронирование)

📍 ГДЕ НАХОДЯТСЯ CALENDAR ID:

   📊 Google Sheets → Таблица "Мастера"
   
   Структура:
   ┌─────────────────────────────────────────────────────────┐
   │ A      B      C             D      E                    │
   ├─────────────────────────────────────────────────────────┤
   │ ID  │ Имя   │ Специальность │ Опыт │ Рейтинг │ ...     │
   ├─────────────────────────────────────────────────────────┤
   │ 1   │ Анна  │ Реализм       │ 8    │ 4.8     │ ...     │
   │ 2   │ Платон│ Минимализм    │ 12   │ 4.9     │ ...     │
   │ 3   │ Сара  │ Пирсинг       │ 6    │ 4.7     │ ...     │
   └─────────────────────────────────────────────────────────┘
   
   ВАЖНО: Google Calendar ID в колонке E (индекс 4)!

🔑 КАК ПОЛУЧИТЬ GOOGLE CALENDAR ID:

   Вариант 1️⃣: Использовать готовый скрипт
   ────────────────────────────────────────
   
   $ python scripts/get_calendar_id.py
   
   Результат:
   ✅ Google Calendar ID: anna@tattoo-480007.iam.gserviceaccount.com
      Summary: Anna's Calendar
      Timezone: Asia/Jerusalem
   
   📝 Скопировать этот ID и вставить в Google Sheets
   
   
   Вариант 2️⃣: Вручную в Google Calendar
   ──────────────────────────────────────
   
   1. Открыть Google Calendar: https://calendar.google.com
   2. На левой панели найти нужный календарь
   3. Нажать на три точки (...) → "Settings"
   4. Найти "Calendar ID" в разделе "Integrate calendar"
   5. Скопировать ID (обычно выглядит как email)
   
   
   Вариант 3️⃣: Через Google API Console
   ──────────────────────────────────────
   
   1. https://console.developers.google.com/
   2. Выбрать проект tattoo-480007
   3. API → Google Calendar API
   4. Credentials → Service Accounts
   5. Скопировать email service account (это календарь мастера)

📝 ШАГ ЗА ШАГОМ ДОБАВЛЕНИЕ CALENDAR ID:

   ШАГ 1: Получить ID
   ──────────────────
   Выполнить скрипт:
   $ python scripts/get_calendar_id.py
   
   Скопировать полученный ID, например:
   anna@tattoo-480007.iam.gserviceaccount.com

   ШАГ 2: Открыть Google Sheets
   ──────────────────────────────
   https://docs.google.com/spreadsheets/d/17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ
   (или вставить свой GOOGLE_SPREADSHEET_ID)

   ШАГ 3: Найти таблицу "Мастера"
   ────────────────────────────────
   Нижняя часть экрана → вкладка "Мастера"

   ШАГ 4: Найти нужного мастера и добавить ID в колонку E
   ────────────────────────────────────────────────────────
   
   Пример:
   Строка: Анна Леви | Реализм | 8 | 4.8 | [СЮДА ВСТАВИТЬ ID]
   
   Вставить:
   anna@tattoo-480007.iam.gserviceaccount.com

   ШАГ 5: Сохранить
   ────────────────
   Google Sheets автосохранит данные

📡 КАК INKA ИХ ИСПОЛЬЗУЕТ:

   Код в src/services/data_sync.py:
   
   ```python
   # Get masters with calendar_id
   for master in masters:
       calendar_id = master.get("calendar_id")  # ← Получаем из Sheets
       
       if not calendar_id:
           logger.debug(f"Master '{master.get('name')}' has no calendar_id")
           continue
       
       # Получить события из календаря
       events = service.events().list(
           calendarId=calendar_id,  # ← Используем ID
           timeMin=...,
           timeMax=...
       ).execute()
   ```

🗂️ СТРУКТУРА GOOGLE SHEETS "Мастера":

   Колонка │ Название      │ Пример значения
   ────────┼───────────────┼───────────────────────────────────
   A       │ ID            │ 1
   B       │ Имя           │ Анна Леви
   C       │ Специальность │ Реализм
   D       │ Опыт (лет)    │ 8
   E       │ Рейтинг       │ 4.8
   F       │ Телефон       │ +972-52-1234567
   G       │ Instagram     │ @m_anna_levi
   H       │ Цена за сеанс │ 250
   I       │ Статус        │ active
   J       │ Описание       │ Портреты, животные...
   
   ⚠️ ВАЖНО: Google Calendar ID должен быть в одной из первых колонок!

❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ:

   Q: Как узнать, какой ID привязан к конкретному мастеру?
   A: Открыть Google Sheets и посмотреть колонку E (или где указаны ID)

   Q: Может ли один календарь использоваться несколькими мастерами?
   A: Да, можно указать один ID для нескольких, но не рекомендуется
   
   Q: Что если забыть добавить ID?
   A: INKA будет показывать ошибку, не сможет получить расписание
   
   Q: Нужен ли ID для всех мастеров?
   A: Нет, только для тех, кто проводит процедуры с расписанием

✅ ПРОВЕРКА:

   Запустить тест:
   $ python -c "
   from src.services.master_service import MasterService
   from src.db.sheets_client import GoogleSheetsClient
   
   sheets = GoogleSheetsClient('credentials.json', 'SPREADSHEET_ID')
   masters = MasterService(sheets).get_all_masters()
   
   for m in masters:
       print(f\"{m['name']}: {m.get('calendar_id', 'NO ID')}\")
   "

═══════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(__doc__)
