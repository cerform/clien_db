# 📊 База Данных

## Архитектура

### Google Sheets (Источник истины)

Главная БД находится в Google Sheets с таблицами:

| Таблица | Описание | Строк | Колонки |
|---------|---------|-------|---------|
| **masters** | Мастера | 3 | id, name, specialization, bio, phone |
| **services** | Услуги | 8 | id, name, duration_min, price_min |
| **schedule** | Расписание мастеров | 21 | id, master_id, day_of_week, start_time, end_time |
| **bookings** | Записи клиентов | N | id, client_id, master_id, service_id, date, time |
| **clients** | Клиенты | N | id, chat_id, name, phone, first_booking_date |

### Структура данных

```
MASTERS
├── id: "m_anna_levi"
├── name: "Анна Леви"
├── specialization: "tattoo"
├── bio: "Реализм, черно-белая графика, 8+ лет опыта"
└── phone: "+972..."

SERVICES
├── id: "s_tattoo_small"
├── name: "Тату маленькое"
├── duration_min: 30
├── price_min: 3000

SCHEDULE (7 дней × 3 мастера = 21 запись)
├── id: "sch_anna_sun"
├── master_id: "m_anna_levi"
├── day_of_week: "Sunday"
├── start_time: "10:00"
└── end_time: "18:00"

BOOKINGS
├── id: "bk_001"
├── client_id: "cli_123456"
├── master_id: "m_anna_levi"
├── service_id: "s_tattoo_small"
├── date: "2025-12-15"
└── time: "14:00"

CLIENTS
├── id: "cli_123456"
├── chat_id: 123456789
├── name: "Иван"
└── phone: "+972..."
```

## Инициализация БД

### Первая настройка

```bash
# 1. Инициализировать схему
python init_database.py

# 2. Заполнить тестовыми данными
python populate_real_data.py

# 3. Проверить целостность
python pre_deploy_check.py
```

### Заполнение данных

**add_data.py** - добавить новые записи:
```python
# Добавить мастера
sheets.append_row("masters", {
    "id": "m_new",
    "name": "Новый мастер",
    "specialization": "tattoo",
    "bio": "Описание"
})

# Добавить услугу
sheets.append_row("services", {
    "id": "s_new",
    "name": "Новая услуга",
    "duration_min": 60,
    "price_min": 5000
})
```

**add_schedule.py** - добавить расписание:
```python
# Добавить для каждого дня недели
for day in ["Monday", "Tuesday", ...]:
    sheets.append_row("schedule", {
        "id": f"sch_name_{day}",
        "master_id": "m_name",
        "day_of_week": day,
        "start_time": "10:00",
        "end_time": "18:00"
    })
```

**fix_schedule.py** - исправить расписание:
```python
# Удалить неправильные записи
# Добавить новые корректные
```

## Синхронизация (DataSyncService)

### Поток данных

```
Google Sheets (источник)
    ↓
sheets_client.py (API)
    ↓
data_sync.py (кэширование + валидация)
    ↓
Cache (TTL 1 час)
    ↓
INKA AI / Клиенты
```

### Кэширование

- **Masters/Services/Schedule**: 1 час TTL
- **Bookings**: 15 минут TTL  
- **Calendar Events**: Реал-тайм

```python
from src.services.data_sync import get_data_sync_service

sync_service = get_data_sync_service()

# Получить все мастера (с кэшем)
masters = sync_service.get_masters()

# Поиск по ключевому слову
anna = sync_service.search_masters("реализм")

# Получить свободные слоты
slots = sync_service.get_available_slots(
    master_id="m_anna_levi",
    date="2025-12-15",
    duration=60
)

# Принудительная синхронизация
sync_service.sync_all()
```

### Валидация данных

DataSyncService автоматически:
1. ✅ Проверяет что все master_id существуют в таблице masters
2. ✅ Проверяет что все service_id существуют в таблице services
3. ✅ Синхронизирует календарь с расписанием
4. ✅ Удаляет прошедшие события из кэша

## Интеграция Календаря

### Google Calendar

- **Календарь**: Единый календарь для всех мастеров
- **События**: Автоматически создаются при новых бронях
- **Синхронизация**: Двусторонняя (Sheets ↔ Calendar)
- **Авторизация**: Service Account (Cloud Run)

```python
from src.calendars.calendar_init import get_calendar_service

calendar = get_calendar_service()

# Получить свободные слоты на дату
events = calendar.events().list(
    calendarId='primary',
    timeMin='2025-12-15T00:00:00Z',
    timeMax='2025-12-16T00:00:00Z'
).execute()
```

## Поиск в INKA

INKA использует **keyword matching** в биографии мастера:

```python
# Поиск "реализм"
masters = sync_service.search_masters("реализм")
# Результат: [Platón Sosnitski (bio: "... реализм ...")]

# Поиск "пирсинг"
masters = sync_service.search_masters("пирсинг")
# Результат: [Moshe (specialization: piercing)]
```

## Текущее состояние

- ✅ 3 мастера (Анна, Платон, Мойше)
- ✅ 8 услуг (тату, пирсинг, консультации)
- ✅ 21 запись расписания (7 дней × 3 мастера)
- ✅ Синхронизация с календарём работает
- ✅ Кэширование оптимизировано
- ✅ Валидация данных работает

## Проблемы и решения

### Проблема: Мастер не найден при поиске
**Решение**: Проверить что `search_masters()` ищет в поле `bio`, не в `specialization`

### Проблема: Расписание несинхронизировано
**Решение**: Запустить `sync_service.sync_all()` для полной переинициализации

### Проблема: Слоты не показываются
**Решение**: Проверить что события в Calendar не перекрывают расписание

## Ссылки

- 📌 [Таблица](https://docs.google.com/spreadsheets/d/17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ)
- 📌 [Календарь](https://calendar.google.com)
- 🔧 [Консоль Cloud](https://console.cloud.google.com)
