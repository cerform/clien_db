# 🤖 INKA: LLM AI Assistant

## Что такое INKA?

INKA - это AI-ассистент на основе OpenAI GPT-4, интегрированный в Telegram бота. Она:

- 🎯 Помогает клиентам записаться на процедуры
- 📚 Отвечает на вопросы о мастерах, услугах, ценах
- 🔍 Ищет мастеров по специализации (реализм, минимализм, пирсинг)
- 📅 Показывает доступные слоты из календаря
- 💬 Ведёт естественный диалог на русском языке

## Архитектура

### Компоненты

```
Telegram Message
       ↓
client_handler.py (message router)
       ↓
advanced_inka.py (LLM orchestrator)
       ├─ OpenAI Assistant API (GPT-4o)
       ├─ DataSyncService (data access)
       │   ├─ Google Sheets (masters, services, schedule)
       │   ├─ Google Calendar (availability)
       │   └─ Cache (optimization)
       └─ Google Calendar API (events)
       ↓
Ответ клиенту
```

### Файлы

| Файл | Описание |
|------|---------|
| `src/ai/advanced_inka.py` | Главный класс INKA с методами LLM |
| `src/bot/handlers/client_handler.py` | Маршрутизация сообщений в INKA |
| `src/services/data_sync.py` | Унифицированный доступ к данным |

## Использование INKA

### Базовый чат

```python
from src.ai.advanced_inka import get_advanced_inka

inka = get_advanced_inka(
    api_key="sk-proj-...",
    assistant_id="asst_LBGeLxauJ3nYbauR3pilbifN",
    sheets_client=sheets,
    calendar_service=calendar
)

# Простой чат
response = await inka.chat("Когда ближайший слот?", user_id="123456")
print(response)  # "У Анны есть слот завтра в 14:00..."
```

### С историей диалога

```python
conversation_history = [
    {"role": "user", "content": "Кто из мастеров лучше?"},
    {"role": "assistant", "content": "Зависит от стиля..."}
]

response = await inka.chat(
    user_text="А кто делает реализм?",
    user_id="123456",
    conversation_history=conversation_history
)
```

### Поиск мастеров

```python
# Автоматический поиск через INKA
response = await inka.chat("Найди мастера по реализму", user_id="123456")

# Или прямой поиск через DataSync
masters = inka.data_sync.search_masters("реализм")
# Результат: [Platón Sosnitski (bio: "реализм, минимализм")]
```

### Получение доступных слотов

```python
# INKA сама запрашивает слоты
response = await inka.chat("Какие слоты на завтра?", user_id="123456")

# Или прямой доступ
slots = inka.data_sync.get_available_slots(
    master_id="m_anna_levi",
    date="2025-12-15",
    duration=60
)
```

## Методы INKA

### `chat(user_text, user_id, conversation_history=[])`

Главный метод для общения.

```python
response = await inka.chat(
    user_text="Запиши меня к Анне на тату",
    user_id="123456789",
    conversation_history=[]
)
```

**Возвращает**: Строка с ответом

**Примеры**:
- "Я помогу тебе записаться! Какой размер тату вы хотите?"
- "У Анны есть свободные слоты: завтра 14:00 или 16:00"

### `get_masters_unified()`

Получить всех мастеров.

```python
masters = inka.get_masters_unified()
# [
#   {"id": "m_anna_levi", "name": "Анна Леви", "specialization": "tattoo", ...},
#   {"id": "m_platon", "name": "Платон", "specialization": "tattoo", ...},
#   {"id": "m_moshe", "name": "Мойше", "specialization": "piercing", ...}
# ]
```

### `search_masters_unified(keyword)`

Поиск мастеров по ключевому слову.

```python
# Поиск "реализм" в поле bio
masters = inka.search_masters_unified("реализм")
# Результат: [Platón - "реализм, минимализм"]

# Поиск "пирсинг"
masters = inka.search_masters_unified("пирсинг")
# Результат: [Moshe - specialization: "piercing"]
```

### `get_available_slots_unified(master_id, date)`

Получить доступные слоты.

```python
slots = inka.get_available_slots_unified(
    master_id="m_anna_levi",
    date="2025-12-15"
)
# Результат: ["10:00-11:00", "14:00-15:00", "16:00-17:00"]
```

### `sync_all_data()`

Принудительная синхронизация всех данных.

```python
await inka.sync_all_data()
# Обновляет: мастеров, услуги, расписание, события календаря
```

## Integration Points

### DataSyncService (данные)

```python
from src.services.data_sync import get_data_sync_service

sync = get_data_sync_service()
masters = sync.get_masters()  # С кэшем (1 час TTL)
schedule = sync.get_schedule()  # Все расписание
services = sync.get_services()  # Все услуги
slots = sync.get_available_slots(master_id, date, duration)
```

### Google Sheets (источник)

```python
from src.db.sheets_client import GoogleSheetsClient

sheets = GoogleSheetsClient(creds_path, spreadsheet_id)
masters = sheets.get_all_rows("masters")
services = sheets.get_all_rows("services")
schedule = sheets.get_all_rows("schedule")
```

### Google Calendar (события)

```python
from src.calendars.calendar_init import get_calendar_service

calendar = get_calendar_service(creds_path)
events = calendar.events().list(calendarId='primary').execute()
```

## Примеры диалогов

### Пример 1: Запись на процедуру

```
Пользователь: Хочу записаться на тату
INKA: Отлично! 🎨 Какой стиль вас интересует?
      - Реализм
      - Минимализм  
      - Олдскул

Пользователь: Реализм
INKA: Отлично! Рекомендую мастера Платона - 
      он специализируется на реализме и минимализме.
      
      Он свободен:
      • Завтра в 14:00
      • 15 декабря в 10:00
      • 16 декабря в 15:00
      
      Какой слот подходит?
```

### Пример 2: Вопрос о мастерах

```
Пользователь: Кто лучше для женской тату?
INKA: Это зависит от стиля! 👩‍🎨
      
      • Анна Леви - Реализм, черно-белая графика
      • Платон - Реализм, минимализм
      • Мойше - Пирсинг, консультации
      
      Анна считается основательницей студии, у неё 8+ лет опыта.
      Что вам нравится?
```

### Пример 3: Вопрос о цене

```
Пользователь: Сколько стоит маленькая тату?
INKA: 💰 Цены зависят от сложности:

      • Маленькая тату: от 3,000₽
      • Средняя тату: от 5,000₽
      • Крупная тату: от 8,000₽
      • Текст: от 2,000₽
      • Пирсинг: от 1,500₽
      
      Хочешь записаться?
```

## Тестирование INKA

### Unit тесты

```bash
python test_unified_sync.py  # Тесты DataSync
python test_send_message.py  # Тест webhook
```

### Интерактивное тестирование

1. Запустить бота локально:
   ```bash
   python -u run_production.py
   ```

2. Отправить сообщение в Telegram

3. Проверить логи:
   ```bash
   tail -f logs/bot.log | grep "Message from"
   ```

## Оптимизация производительности

### Кэширование

INKA использует DataSyncService с TTL:
- Masters/Services/Schedule: 1 час
- Bookings: 15 минут
- Calendar events: реал-тайм

### Lazy loading

DataSyncService инициализируется лениво:
```python
@property
def data_sync(self):
    if self._data_sync is None:
        self._data_sync = get_data_sync_service()
    return self._data_sync
```

### Асинхронность

Все операции асинхронные через `asyncio`:
```python
response = await inka.chat(user_text, user_id)  # не блокирует
```

## Проблемы и решения

### Проблема: INKA долго отвечает
**Решение**: Проверить кэширование DataSync работает

### Проблема: INKA не находит мастеров
**Решение**: Проверить что `search_masters()` ищет в поле `bio`

### Проблема: INKA не видит слоты
**Решение**: Проверить что календарь синхронизирован

### Проблема: OpenAI API ошибка
**Решение**: Проверить API ключ и лимиты квоты

## Развитие INKA

### Будущие возможности

- [ ] Multi-language support (EN, HE)
- [ ] Booking confirmation via SMS/Email
- [ ] Integration with payment systems
- [ ] Telegram inline buttons for quick actions
- [ ] Client feedback and ratings

## Ссылки

- 🔗 [OpenAI Assistant Docs](https://platform.openai.com/docs/assistants)
- 🤖 [Aiogram Docs](https://docs.aiogram.dev)
- 📚 [Google Sheets API](https://developers.google.com/sheets/api)
- 📅 [Google Calendar API](https://developers.google.com/calendar/api)
