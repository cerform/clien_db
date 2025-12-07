# INKA Multilingual Integration Examples

## 📋 Содержание

1. [Базовое использование](#базовое-использование)
2. [Интеграция в Advanced INKA](#интеграция-в-advanced-inka)
3. [Интеграция в Telegram Handlers](#интеграция-в-telegram-handlers)
4. [Полный workflow](#полный-workflow)
5. [Обработка ошибок](#обработка-ошибок)

---

## Базовое использование

### Пример 1: Определение языка

```python
from src.services.localization_service import LocalizationService, Language

# Инициализировать сервис
loc = LocalizationService(openai_api_key="sk-...")

# Определить язык текста
def handle_user_message(text: str):
    language = loc.detect_language(text)
    
    if language == Language.RUSSIAN:
        print("Пользователь говорит по-русски 🇷🇺")
    elif language == Language.ENGLISH:
        print("User speaks English 🇬🇧")
    elif language == Language.HEBREW:
        print("המשתמש מדבר עברית 🇮🇱")

# Примеры
handle_user_message("Привет, как дела?")        # → Russian
handle_user_message("Hello, how are you?")      # → English
handle_user_message("שלום, איך אתה?")           # → Hebrew
```

### Пример 2: Перевод текста

```python
from src.services.localization_service import LocalizationService, Language

loc = LocalizationService(openai_api_key="sk-...")

# Перевести на русский
russian = loc.translate_text("I want a tattoo", Language.RUSSIAN)
print(russian)  # "Я хочу тату"

# Перевести на иврит
hebrew = loc.translate_text("Book an appointment", Language.HEBREW)
print(hebrew)  # "הזמן ייעוץ"

# Быстрые переводы из глоссария
master_he = loc.glossary["master"]["he"]  # "מהיר"
service_ru = loc.glossary["service"]["ru"]  # "услуга"
```

### Пример 3: Готовые ответы

```python
from src.services.localization_service import LocalizationService, Language

loc = LocalizationService(openai_api_key="sk-...")

# Получить приветствие на русском
greeting_ru = loc.get_response("greeting", Language.RUSSIAN)
print(greeting_ru)
# → "Привет! 😊 Хочешь сделать тату или пирсинг?"

# Получить подтверждение бронирования на иврите
confirmation_he = loc.get_response("confirm_booking", Language.HEBREW, 
                                    date="יום ב' 15:00", 
                                    master="אנה לוי")
print(confirmation_he)
# → "מעולה! הזמנתי אותך ב-יום ב' 15:00 עם אנה לוי."
```

### Пример 4: Локализация БД запросов

```python
from src.services.localization_service import LocalizationService, Language

loc = LocalizationService(openai_api_key="sk-...")

# Данные из Google Sheets (с локализационными полями)
master_from_db = {
    "id": "master-123",
    "name": "Anna Levi",  # English base
    "name_ru": "Анна Леви",
    "name_en": "Anna Levi",
    "name_he": "אנה לוי",
    "specialization": "Realistic Tattoos",
    "specialization_ru": "Реалистичные татуировки",
    "specialization_en": "Realistic Tattoos",
    "specialization_he": "קעקועים אמיתיים"
}

# Перевести информацию мастера
translated = loc.translate_master_info(master_from_db, Language.HEBREW)
print(translated["name"])               # → "אנה לוי"
print(translated["specialization"])     # → "קעקועים אמיתיים"
```

---

## Интеграция в Advanced INKA

### Полная интеграция в Advanced INKA

```python
# в src/ai/advanced_inka.py

from src.ai.inka_localization import create_inka_localization_middleware
from src.services.localization_service import Language

class AdvancedINKA:
    def __init__(self, api_key: str, assistant_id: str, 
                 sheets_client=None, calendar_service=None, 
                 data_sync=None, openai_api_key: str = None):
        """
        Инициализация INKA с поддержкой локализации
        """
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self.sheets_client = sheets_client
        self.calendar_service = calendar_service
        self._data_sync = data_sync
        
        # Инициализировать локализацию
        self.localization = create_inka_localization_middleware(
            openai_api_key or api_key
        )
        
        # Существующие кэши...
        self._schedule_cache = None
        self._masters_cache = None
        self._services_cache = None
    
    def process_message(self, user_id: str, message: str, 
                       telegram_language_code: str = None) -> str:
        """
        Обработать сообщение пользователя с поддержкой локализации
        
        Args:
            user_id: Telegram ID пользователя
            message: Текст сообщения
            telegram_language_code: Код языка от Telegram (опционально)
        
        Returns:
            Ответ на языке пользователя
        """
        # 1. Обработать входящее сообщение
        msg_info = self.localization.process_incoming_message(user_id, message)
        processed_msg = msg_info['processed_message']
        user_lang = msg_info['detected_language']
        
        # Если есть информация от Telegram, использовать ее
        if telegram_language_code:
            if telegram_language_code.startswith('ru'):
                user_lang = Language.RUSSIAN
            elif telegram_language_code.startswith('he'):
                user_lang = Language.HEBREW
            elif telegram_language_code.startswith('en'):
                user_lang = Language.ENGLISH
            self.localization.set_user_language(user_id, user_lang)
        
        # 2. Извлечь намерение бронирования
        booking_intent = self.localization.extract_booking_intent(
            message, user_lang
        )
        
        # 3. Получить системный промпт с учетом языка
        system_prompt = self.localization.create_system_prompt_with_localization(user_lang)
        
        # 4. Отправить в OpenAI Assistant
        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=processed_msg
        )
        
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
            system_prompt=system_prompt
        )
        
        # Ждем завершения
        while run.status != "completed":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            time.sleep(0.5)
        
        # 5. Получить ответ от INKA
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        inka_response = messages.data[0].content[0].text
        
        # 6. Локализовать ответ
        final_response = self.localization.format_outgoing_message(
            inka_response, user_lang
        )
        
        return final_response
    
    def get_available_slots_multilingual(self, master_id: str, 
                                         user_lang: Language) -> str:
        """
        Получить доступные слоты на языке пользователя
        """
        slots = self._get_available_slots(master_id)  # существующий метод
        
        # Форматировать на нужном языке
        return self.localization.get_schedule_display(slots, user_lang)
```

---

## Интеграция в Telegram Handlers

### Обработчик сообщений с локализацией

```python
# в src/bot/handlers/client_handler.py

from telegram import types
from telegram.ext import ContextTypes, MessageHandler, filters
from src.ai.advanced_inka import AdvancedINKA
from src.config.config import get_config

class ClientHandler:
    def __init__(self):
        config = get_config()
        self.inka = AdvancedINKA(
            api_key=config.openai_api_key,
            assistant_id=config.openai_assistant_id,
            openai_api_key=config.openai_api_key
        )
    
    async def handle_message(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработать сообщение пользователя с полной локализацией
        """
        message = update.message
        user = message.from_user
        
        # Получить информацию о пользователе
        user_id = str(user.id)
        user_text = message.text
        user_language_code = user.language_code  # 'ru', 'en', 'he' и т.д.
        
        try:
            # Отправить статус "пишет ответ"
            await message.chat.send_action("typing")
            
            # Обработать сообщение через INKA с локализацией
            response = self.inka.process_message(
                user_id=user_id,
                message=user_text,
                telegram_language_code=user_language_code
            )
            
            # Отправить ответ пользователю
            await message.reply(response)
            
        except Exception as e:
            logger.error(f"Error processing message from {user_id}: {e}")
            await message.reply("Произошла ошибка. Попробуй еще раз 😊")


# Регистрация обработчика
def register_handlers(dp):
    handler = ClientHandler()
    dp.add_handler(MessageHandler(filters.text, handler.handle_message))
```

### Обработчик команды /start с локализацией

```python
# в src/bot/handlers/start_handler.py

from telegram import types
from src.services.localization_service import LocalizationService, Language

class StartHandler:
    def __init__(self):
        self.localization = LocalizationService(openai_api_key="sk-...")
    
    async def handle_start(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /start с приветствием на языке пользователя
        """
        user = update.message.from_user
        language_code = user.language_code or "ru"
        
        # Определить язык пользователя
        if language_code.startswith('he'):
            user_lang = Language.HEBREW
            greeting = self.localization.get_response("greeting", Language.HEBREW)
        elif language_code.startswith('en'):
            user_lang = Language.ENGLISH
            greeting = self.localization.get_response("greeting", Language.ENGLISH)
        else:  # Russian default
            user_lang = Language.RUSSIAN
            greeting = self.localization.get_response("greeting", Language.RUSSIAN)
        
        await update.message.reply(greeting)
```

---

## Полный workflow

### End-to-End пример

```python
import logging
from telegram import types
from src.ai.advanced_inka import AdvancedINKA
from src.services.localization_service import Language
from src.config.config import get_config

logger = logging.getLogger(__name__)

class CompleteWorkflow:
    def __init__(self):
        config = get_config()
        self.inka = AdvancedINKA(
            api_key=config.openai_api_key,
            assistant_id=config.openai_assistant_id,
            sheets_client=None,  # initialize if needed
            calendar_service=None,  # initialize if needed
            openai_api_key=config.openai_api_key
        )
    
    async def handle_user_interaction(self, message: types.Message):
        """
        Полный workflow обработки сообщения пользователя
        """
        user_id = str(message.from_user.id)
        user_text = message.text
        language_code = message.from_user.language_code
        
        logger.info(f"📨 User {user_id} ({language_code}): {user_text}")
        
        # Шаг 1: Показать что пишем ответ
        await message.chat.send_action("typing")
        
        # Шаг 2: Обработать через INKA с локализацией
        try:
            response = self.inka.process_message(
                user_id=user_id,
                message=user_text,
                telegram_language_code=language_code
            )
            
            logger.info(f"✅ Response sent to {user_id}")
            
            # Шаг 3: Отправить ответ
            await message.reply(response)
            
            # Шаг 4: Если нужны предложения слотов
            msg_info = self.inka.localization.process_incoming_message(user_id, user_text)
            booking_intent = self.inka.localization.extract_booking_intent(
                user_text, msg_info['detected_language']
            )
            
            if booking_intent['has_booking_intent']:
                logger.info(f"🎯 Booking intent detected for {user_id}")
                
                # Получить доступные слоты
                slots = self.inka._get_available_slots("master-123")
                slots_text = self.inka.localization.get_schedule_display(
                    slots, msg_info['detected_language']
                )
                
                await message.reply(slots_text)
        
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)
            
            # Отправить сообщение об ошибке на языке пользователя
            if language_code and language_code.startswith('he'):
                error_msg = "סליחה, הייתה שגיאה. נסה שוב מאוחר יותר 😊"
            elif language_code and language_code.startswith('en'):
                error_msg = "Sorry, there was an error. Please try again later 😊"
            else:
                error_msg = "Извини, произошла ошибка. Попробуй позже 😊"
            
            await message.reply(error_msg)
```

---

## Обработка ошибок

### Примеры обработки типичных ошибок

```python
from src.services.localization_service import LocalizationService, Language

class ErrorHandling:
    def __init__(self):
        self.loc = LocalizationService(openai_api_key="sk-...")
    
    async def handle_language_detection_error(self, user_id: str, message: str):
        """
        Если определение языка не сработало
        """
        try:
            lang = self.loc.detect_language(message)
            if lang == Language.AUTO:
                # Спросить пользователя
                return "Which language do you prefer? (English/Русский/עברית)"
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "Couldn't detect language. Please tell us your preferred language."
    
    async def handle_translation_error(self, user_id: str, text: str, target_lang: Language):
        """
        Если перевод не сработал
        """
        try:
            translated = self.loc.translate_text(text, target_lang)
            if not translated or translated == text:
                # Fallback на оригинальный текст
                logger.warning(f"Translation might be incomplete: {text}")
                return text
            return translated
        except Exception as e:
            logger.error(f"Translation failed for {target_lang.value}: {e}")
            # Вернуть оригинальный текст
            return text
    
    async def handle_database_localization_error(self, data: dict, user_lang: Language):
        """
        Если локализация БД не сработала
        """
        try:
            localized = self.loc.translate_master_info(data, user_lang)
            return localized
        except Exception as e:
            logger.error(f"Database localization failed: {e}")
            # Fallback на английский базовый язык
            return data
```

---

## Тестирование

### Unit тесты для локализации

```python
import pytest
from src.services.localization_service import LocalizationService, Language
from src.ai.inka_localization import InkaLocalizationMiddleware

def test_russian_detection():
    loc = LocalizationService()
    assert loc.detect_language("Привет") == Language.RUSSIAN

def test_english_detection():
    loc = LocalizationService()
    assert loc.detect_language("Hello") == Language.ENGLISH

def test_hebrew_detection():
    loc = LocalizationService()
    assert loc.detect_language("שלום") == Language.HEBREW

def test_glossary_lookup():
    loc = LocalizationService()
    assert loc.glossary["master"]["ru"] == "мастер"
    assert loc.glossary["master"]["en"] == "master"
    assert loc.glossary["master"]["he"] == "מהיר"

def test_middleware_language_persistence():
    middleware = InkaLocalizationMiddleware(LocalizationService())
    
    # Первое сообщение
    middleware.get_user_language("user1", "Привет")
    lang1 = middleware.get_user_language("user1", "")
    
    # Второе сообщение - должен вспомнить
    assert lang1 == Language.RUSSIAN
```

---

## 🎯 Checklist Интеграции

- [ ] Установить LocalizationService в services
- [ ] Установить InkaLocalizationMiddleware в ai
- [ ] Обновить __init__.py в services и ai
- [ ] Добавить локализацию в Advanced INKA
- [ ] Добавить локализацию в Telegram handlers
- [ ] Обновить database schema с _ru, _en, _he полями
- [ ] Заполнить БД многоязычными данными
- [ ] Запустить тесты: `python3 tests/test_multilingual.py`
- [ ] Протестировать с реальными пользователями
- [ ] Обновить документацию

---

**Версия:** 1.0
**Статус:** Ready for Production
**Последнее обновление:** 2024
