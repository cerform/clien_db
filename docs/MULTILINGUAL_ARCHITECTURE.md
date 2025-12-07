# ИНКА Многоязычная Архитектура

## 🌍 Обзор

ИНКА теперь поддерживает полную многоязычную коммуникацию через элегантную архитектуру:
- **Схема БД**: английский (clean, maintainable)
- **Локализация**: русский, английский, иврит (теги в БД)
- **Обработка**: автоматическое определение языка, динамический перевод
- **Пользователи**: видят все на своем языке

## 📊 Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    TELEGRAM CLIENT                       │
│  (User sends message in Russian/English/Hebrew)         │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            INKA Localization Middleware                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Language Detection (detect_language)          │   │
│  │ 2. Message Translation (if needed)               │   │
│  │ 3. Extract Booking Intent                        │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Advanced INKA (OpenAI)                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │ - Process user intent in English                 │   │
│  │ - Query database for available slots/masters     │   │
│  │ - Generate response in English                   │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    ┌────────┐        ┌────────┐        ┌─────────┐
    │Sheets  │        │Calendar│        │Services │
    │Client  │        │API     │        │Layer    │
    └────────┘        └────────┘        └─────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│         Google Sheets Database (English Schema)         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Sheet: Masters                                   │   │
│  │ - Columns: id, name, specialization, bio        │   │
│  │ - Localization: name_ru, name_en, name_he       │   │
│  │ - calendar_id: linked to Google Calendar        │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Sheet: Services                                  │   │
│  │ - Columns: id, name, description, duration      │   │
│  │ - Localization: name_ru, name_en, name_he       │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Sheet: Schedule                                  │   │
│  │ - day_of_week, is_working, start_time, end_time │   │
│  │ - Proper relationship with Google Calendar      │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│         Localization Service (Response)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Get localized database fields                 │   │
│  │ 2. Translate response (GPT-4 or glossary)        │   │
│  │ 3. Format in user's language                     │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 TELEGRAM RESPONSE                       │
│        (User sees reply in their language)              │
└─────────────────────────────────────────────────────────┘
```

## 🏗️ Компоненты

### 1. LocalizationService (`src/services/localization_service.py`)

**Функции:**
- `detect_language(text)` - определить язык текста (RU/EN/HE)
- `translate_text(text, target_language)` - перевести текст используя GPT
- `translate_database_row()` - локализовать БД запросы
- `get_response()` - получить предварительно переведенный ответ

**Поддерживаемые языки:**
- Russian (ru) - 🇷🇺
- English (en) - 🇬🇧  
- Hebrew (he) - 🇮🇱

**Глоссарий:**
Быстрые переводы основных терминов (не требуют GPT):
```python
"master" → {"ru": "мастер", "en": "master", "he": "מהיר"}
"service" → {"ru": "услуга", "en": "service", "he": "שירות"}
"available" → {"ru": "доступно", "en": "available", "he": "זמין"}
```

### 2. InkaLocalizationMiddleware (`src/ai/inka_localization.py`)

**Функции:**
- `get_user_language()` - сохранить и получить язык пользователя
- `process_incoming_message()` - определить язык, перевести на английский для INKA
- `localize_database_response()` - взять нужные _ru/_en/_he поля из БД
- `format_outgoing_message()` - перевести ответ INKA на язык пользователя

**Workflow:**
```
User (Hebrew) → "אני רוצה קעקוע"
    ↓
Middleware: detect_language() → HEBREW
    ↓
Middleware: translate_text() → "I want a tattoo"
    ↓
INKA: process & generate response in English
    ↓
INKA response: "Great! What style do you prefer?"
    ↓
Middleware: translate_text() → "מה סגנון מעדיף?"
    ↓
User sees: "מה סגנון מעדיף?"
```

### 3. Database Schema (English + Localization)

**Мастера (Masters):**
```
id | name | specialization | ... | calendar_id
---|------|-----------------|-----|------------
   | (English base)         |     | Google Cal ID

+ name_ru, name_en, name_he (translations)
+ specialization_ru, specialization_en, specialization_he
+ bio_ru, bio_en, bio_he
```

**Услуги (Services):**
```
id | name | description | duration_min | ...
---|------|-------------|--------------|----
   | (English base)    |      |

+ name_ru, name_en, name_he
+ description_ru, description_en, description_he
```

**Клиенты (Clients):**
```
id | name | ... | preferred_language | language_code
---|------|-----|------------------|---------------
   |      |     | Russian/English/Hebrew | ru/en/he
```

## 🚀 Запуск и Тестирование

### 1. Инициализировать БД с новой схемой

```bash
# Первый раз - создать таблицы
python3 setup/init_database.py

# Заполнить многоязычными данными (новое!)
python3 setup/populate_multilingual.py
```

### 2. Тестирование LocalizationService

```python
from src.services.localization_service import LocalizationService, Language

loc = LocalizationService(openai_api_key="sk-...")

# Определить язык
lang = loc.detect_language("Привет! Хочу тату")
print(lang)  # Language.RUSSIAN

# Перевести
en_text = loc.translate_text("Привет! Хочу тату", Language.ENGLISH)
print(en_text)  # "Hello! I want a tattoo"

# Получить локализованный ответ
msg = loc.get_response("greeting", Language.HEBREW)
print(msg)  # "שלום! 😊 מעוניין בקעקוע או פירסינג?"
```

### 3. Тестирование Middleware

```python
from src.ai.inka_localization import create_inka_localization_middleware

middleware = create_inka_localization_middleware(openai_api_key="sk-...")

# Обработать входящее сообщение от пользователя
result = middleware.process_incoming_message(
    user_id="123456",
    message="אני רוצה קעקוע קטן"
)
print(result)
# {
#   'original_message': 'אני רוצה קעקוע קטן',
#   'processed_message': 'I want a small tattoo',
#   'detected_language': Language.HEBREW,
#   'user_id': '123456'
# }

# Локализовать БД ответ
master_data = {
    "id": "123",
    "name": "Anna Levi",
    "name_ru": "Анна Леви",
    "name_he": "אנה לוי",
    "specialization": "Realistic Tattoos",
    "specialization_ru": "Реалистичные татуировки",
    "specialization_he": "קעקועים אמיתיים"
}
localized = middleware.localize_database_response(
    master_data, 
    Language.HEBREW,
    data_type="master"
)
print(localized["name"])  # "אנה לוי"
print(localized["specialization"])  # "קעקועים אמיתיים"
```

## 📝 Добавление Новых Данных с Локализацией

При добавлении нового мастера или услуги:

```python
new_master = {
    "id": uuid.uuid4(),
    "name": "David Cohen",  # English base
    "specialization": "Minimalist Design",
    # Локализационные поля
    "name_ru": "Дэвид Коэн",
    "name_en": "David Cohen",
    "name_he": "דוד כהן",
    "specialization_ru": "Минималистичный дизайн",
    "specialization_en": "Minimalist Design",
    "specialization_he": "עיצוב מינימליסטי"
}
```

## 🔄 Интеграция с Advanced INKA

### В `src/ai/advanced_inka.py` добавить:

```python
from src.ai.inka_localization import create_inka_localization_middleware

class AdvancedINKA:
    def __init__(self, api_key, assistant_id, ..., openai_api_key=None):
        # ... existing code ...
        self.localization = create_inka_localization_middleware(openai_api_key or api_key)
    
    def process_message(self, user_id: str, message: str, from_user_language_code: str = None):
        # 1. Обработать входящее сообщение
        msg_info = self.localization.process_incoming_message(user_id, message)
        processed_msg = msg_info['processed_message']
        user_lang = msg_info['detected_language']
        
        # 2. Отправить в OpenAI
        response = self.client.chat.completions.create(
            messages=[...processed_msg...],
            system_prompt=self.localization.create_system_prompt_with_localization(user_lang)
        )
        
        # 3. Получить ответ INKA
        inka_response = response.choices[0].message.content
        
        # 4. Локализовать ответ
        final_response = self.localization.format_outgoing_message(inka_response, user_lang)
        
        return final_response
```

### В обработчике Telegram:

```python
@dp.message_handler(content_types=['text'])
async def handle_message(message: types.Message):
    user_id = str(message.from_user.id)
    user_text = message.text
    language_code = message.from_user.language_code  # 'ru', 'en', 'he' и т.д.
    
    # Обработать через INKA с многоязычной поддержкой
    response = inka.process_message(user_id, user_text, language_code)
    
    await message.reply(response)
```

## 🎯 Ключевые Особенности

### ✅ Англоязычная Схема БД
- **Плюсы:**
  - Clean, maintainable code
  - Easy for developers
  - Standard naming conventions
  - Better integration with APIs

### ✅ Локализационные Теги в БД
- **Преимущества:**
  - No need for separate translation tables
  - All data in one row
  - Fast lookups
  - Scales well

### ✅ Автоматическое Определение Языка
- По символам в тексте (Cyrillic, Hebrew, ASCII)
- Сохранение предпочтения пользователя
- Fallback на русский язык

### ✅ Умное Кэширование Переводов
- Глоссарий для частых терминов
- GPT только для уникальных фраз
- Снижает время отклика

### ✅ Прозрачная Интеграция
- Middleware pattern (не нужно менять INKA)
- Backward compatible
- Easy to extend

## 📚 Примеры Использования

### Пример 1: Русскоговорящий клиент

```
User: "Привет, хочу маленькую тату с надписью"
  ↓
Middleware: Detect Russian, process intent
  ↓
INKA (English): "Hello! Small text tattoo is perfect. How about 'Love' or something personal?"
  ↓
User sees: "Привет! Маленькая текстовая татуировка идеальна. Может быть «Любовь» или что-то личное?"
```

### Пример 2: Англоговорящий клиент

```
User: "I want a realistic portrait tattoo"
  ↓
Middleware: Detect English, pass through
  ↓
INKA: "Great! Portrait tattoos are our specialty. Anna Levi is perfect for this. When are you free?"
  ↓
User sees: (same as INKA generated)
```

### Пример 3: Израильский клиент

```
User: "קעקוע קטן בטלפון? כמה עולה?"
  ↓
Middleware: Detect Hebrew, translate to English
  ↓
INKA (English): "Small phone tattoo costs 150-200. It takes about 30-45 minutes."
  ↓
User sees: "קעקוע קטן בטלפון עולה 150-200. זה לוקח בערך 30-45 דקות"
```

## 🔐 Security & Privacy

- User language preference stored locally (not shared)
- Translations via OpenAI API (secure)
- Database IDs are UUIDs (not exposed)
- No sensitive data in translations

## 📈 Масштабируемость

Добавление нового языка:

1. Добавить enum в `Language`
2. Обновить символьные диапазоны в `detect_language()`
3. Добавить переводы в `glossary` и `responses`
4. Добавить `_lang` колонки в БД
5. Обновить middleware

**Пример добавления французского:**

```python
class Language(Enum):
    FRENCH = "fr"  # Добавить

# В detect_language():
fr_count = sum(1 for c in text if ...(French Unicode range)...)

# В glossary:
"master": {..., "fr": "maître", ...}

# В БД:
"name_fr", "specialization_fr", "bio_fr"
```

## 🚦 Статус Реализации

✅ **Готово:**
- LocalizationService
- InkaLocalizationMiddleware  
- Database schema обновлена
- populate_multilingual.py создан
- Глоссарий с основными терминами

🔄 **В процессе:**
- Тестирование с реальными пользователями
- Оптимизация кэширования переводов

⏳ **Запланировано:**
- Интеграция в Advanced INKA
- Интеграция с Telegram handlers
- Dashboard для управления локализацией

## 🎓 Тренировка Новых Разработчиков

При добавлении многоязычной поддержки новый разработчик должен понимать:

1. **Архитектура:** БД английская → Middleware обрабатывает языки → Пользователь видит на своем языке
2. **Локализация:** name_ru, name_en, name_he в одной строке БД
3. **Автоматизм:** Все работает автоматически, разработчик не думает о языках
4. **Расширяемость:** Легко добавить новый язык (1 час работы)

---

**Последнее обновление:** $(date)
**Автор:** GitHub Copilot
**Версия:** 1.0
