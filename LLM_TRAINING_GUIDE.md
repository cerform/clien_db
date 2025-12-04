# 🎓 Тренировка LLM для работы с реальными данными

## 📋 Содержание
1. [Настройка OpenAI Assistant](#настройка-openai-assistant)
2. [Обучение работе с данными](#обучение-работе-с-данными)
3. [Интеграция с Google Calendar](#интеграция-с-google-calendar)
4. [Интернет-поиск](#интернет-поиск)
5. [Человечное общение](#человечное-общение)

---

## 🤖 Настройка OpenAI Assistant

### Шаг 1: Обновление Assistant через API

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

# Обновляем ваш существующий ассистент
assistant = client.beta.assistants.update(
    assistant_id="asst_LBGeLxauJ3nYbauR3pilbifN",
    
    # Системные инструкции (характер и поведение)
    instructions="""Ты — ИНКА, дружелюбный AI-ассистент тату-салона.

ТВОЯ ЛИЧНОСТЬ:
• Общаешься живо и естественно, как настоящий человек
• Проявляешь эмпатию и заботу о клиенте
• Используешь эмодзи уместно
• Запоминаешь детали разговора
• Умеешь поддержать беседу на разные темы

ВАЖНО - ВСЕГДА используй функции для получения РЕАЛЬНЫХ данных:
• get_database_info - для информации о клиентах, записях, услугах
• get_calendar_slots - для проверки свободных слотов
• search_web - для актуальной информации из интернета
• create_booking - для создания записи

НИКОГДА не придумывай данные! Если нужна информация - вызывай соответствующую функцию!

СТИЛЬ:
• Короткие, живые предложения
• Без формальности
• Обращайся по имени
• Будь честной - если не знаешь, так и скажи""",
    
    # Функции (инструменты)
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_database_info",
                "description": "Получить данные из БД (клиенты, записи, мастера, услуги)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "enum": ["Клиенты", "Мастера", "Записи", "Услуги", "Прайс-лист"],
                            "description": "Название таблицы"
                        },
                        "filter_field": {
                            "type": "string",
                            "description": "Поле для фильтрации"
                        },
                        "filter_value": {
                            "type": "string",
                            "description": "Значение фильтра"
                        }
                    },
                    "required": ["table"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_calendar_slots",
                "description": "Получить свободные слоты из календаря",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Дата начала YYYY-MM-DD"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "Дата конца YYYY-MM-DD"
                        },
                        "master_id": {
                            "type": "string",
                            "description": "ID мастера (опционально)"
                        }
                    },
                    "required": ["start_date", "end_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Искать актуальную информацию в интернете",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Поисковый запрос"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_booking",
                "description": "Создать запись для клиента",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "master_id": {"type": "string"},
                        "date": {"type": "string"},
                        "time": {"type": "string"},
                        "service": {"type": "string"}
                    },
                    "required": ["user_id", "master_id", "date", "time", "service"]
                }
            }
        }
    ],
    
    # Модель
    model="gpt-4o",
    
    # Настройки
    temperature=0.7,  # Баланс между креативностью и точностью
)

print("✅ Assistant обновлён!")
print(f"ID: {assistant.id}")
```

### Шаг 2: Сохраните скрипт

```bash
python3 update_assistant.py
```

---

## 📚 Обучение работе с данными

### Метод 1: Fine-tuning (точная настройка)

Fine-tuning позволяет «дообучить» модель на ваших специфических данных.

#### Подготовка датасета

Создайте файл `training_data.jsonl`:

```jsonl
{"messages": [{"role": "system", "content": "Ты ИНКА, ассистент тату-салона. Используй функции для получения реальных данных."}, {"role": "user", "content": "Когда у мастера Аня свободное время?"}, {"role": "assistant", "content": null, "function_call": {"name": "get_calendar_slots", "arguments": "{\"master_id\": \"1\", \"start_date\": \"2025-12-05\", \"end_date\": \"2025-12-12\"}"}}, {"role": "function", "name": "get_calendar_slots", "content": "{\"slots\": [{\"date\": \"2025-12-06\", \"time\": \"14:00\"}, {\"date\": \"2025-12-07\", \"time\": \"10:00\"}]}"}, {"role": "assistant", "content": "У Ани есть свободные окна:\n\n• 6 декабря в 14:00\n• 7 декабря в 10:00\n\nКакой вариант тебе больше подходит?"}]}
{"messages": [{"role": "system", "content": "Ты ИНКА, ассистент тату-салона."}, {"role": "user", "content": "Сколько стоит маленькая тату?"}, {"role": "assistant", "content": null, "function_call": {"name": "get_database_info", "arguments": "{\"table\": \"Прайс-лист\"}"}}, {"role": "function", "name": "get_database_info", "content": "{\"data\": [{\"service\": \"Маленькое тату\", \"price\": \"3000-5000₽\"}]}"}, {"role": "assistant", "content": "Маленькая татушка стоит от 3000 до 5000₽, в зависимости от сложности и детализации 💰\n\nХочешь обсудить идею? Могу показать примеры работ!"}]}
{"messages": [{"role": "system", "content": "Ты ИНКА."}, {"role": "user", "content": "Привет!"}, {"role": "assistant", "content": "Привет! 😊 Как дела? Чем могу помочь сегодня?"}]}
```

#### Запуск Fine-tuning

```python
from openai import OpenAI

client = OpenAI()

# Загружаем файл
with open("training_data.jsonl", "rb") as file:
    training_file = client.files.create(
        file=file,
        purpose="fine-tune"
    )

# Создаём задачу fine-tuning
fine_tune = client.fine_tuning.jobs.create(
    training_file=training_file.id,
    model="gpt-4o-2024-08-06",  # или gpt-3.5-turbo
    suffix="inka-trained"
)

print(f"Fine-tuning job created: {fine_tune.id}")
print("Check status: client.fine_tuning.jobs.retrieve(fine_tune.id)")
```

### Метод 2: Few-shot learning (примеры в промпте)

Добавьте примеры прямо в системный промпт:

```python
examples = """
ПРИМЕРЫ ПРАВИЛЬНОЙ РАБОТЫ:

Пример 1: Запрос информации
Пользователь: "У вас есть мастер Анна?"
Ты: [вызываешь get_database_info(table="Мастера", filter_field="name", filter_value="Анна")]
[получаешь данные]
Ты: "Да, у нас есть мастер Анна Иванова! Она специализируется на минимализме и акварельных работах ✨"

Пример 2: Проверка расписания
Пользователь: "Когда можно записаться на следующей неделе?"
Ты: [вызываешь get_calendar_slots(start_date="2025-12-09", end_date="2025-12-15")]
[получаешь свободные слоты]
Ты: "На следующей неделе есть такие варианты:\n\n• Понедельник, 9 дек в 14:00\n• Среда, 11 дек в 10:00\n• Пятница, 13 дек в 16:00\n\nКакое время удобно?"

Пример 3: Поиск в интернете
Пользователь: "Как ухаживать за свежей тату?"
Ты: [вызываешь search_web(query="уход за свежей татуировкой 2025")]
[получаешь информацию]
Ты: "После сеанса важно:\n• Первые 2-3 часа держать пленку\n• Мыть только чистыми руками\n• Наносить заживляющую мазь\n\nЯ пришлю подробную инструкцию после твоей записи! 📝"
"""
```

---

## 📅 Интеграция с Google Calendar

### Настройка доступа к Calendar

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_calendar_service():
    """Получить сервис Google Calendar"""
    creds = Credentials.from_authorized_user_file('token.json', 
        ['https://www.googleapis.com/auth/calendar.readonly'])
    
    service = build('calendar', 'v3', credentials=creds)
    return service

# Использование
calendar_service = get_calendar_service()

# Получить события
events = calendar_service.events().list(
    calendarId='primary',
    timeMin='2025-12-05T00:00:00Z',
    timeMax='2025-12-12T23:59:59Z',
    singleEvents=True,
    orderBy='startTime'
).execute()

print(f"Найдено событий: {len(events.get('items', []))}")
```

### Добавление Calendar в INKA

Обновите `src/bot/handlers/client_handler.py`:

```python
from src.ai.advanced_inka import get_advanced_inka
from src.calendars.google_calendar_sync import GoogleCalendarService

# В обработчике
calendar_service = GoogleCalendarService(config.google_credentials_json)

inka = get_advanced_inka(
    api_key=config.openai_api_key,
    assistant_id=config.openai_assistant_id,
    sheets_client=sheets,
    calendar_service=calendar_service
)

response = await inka.chat(user_text, user_id, conversation_history)
```

---

## 🌐 Интернет-поиск

### Вариант 1: Google Custom Search API

```python
import requests

def search_google(query: str, api_key: str, cx: str) -> list:
    """Поиск через Google Custom Search API"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": 3
    }
    
    response = requests.get(url, params=params)
    results = response.json().get("items", [])
    
    return [{
        "title": item["title"],
        "snippet": item["snippet"],
        "link": item["link"]
    } for item in results]
```

### Вариант 2: Bing Search API

```python
def search_bing(query: str, api_key: str) -> list:
    """Поиск через Bing Search API"""
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "count": 3}
    
    response = requests.get(url, headers=headers, params=params)
    results = response.json().get("webPages", {}).get("value", [])
    
    return [{
        "title": item["name"],
        "snippet": item["snippet"],
        "url": item["url"]
    } for item in results]
```

### Вариант 3: Использование GPT-4 (без реального поиска)

```python
def ai_knowledge_search(query: str, client: OpenAI) -> str:
    """Использование знаний GPT"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты эксперт по татуировкам. Дай точный, актуальный ответ."},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content
```

---

## 💬 Человечное общение

### Техники для естественного диалога

#### 1. Контекст и память

```python
# Сохраняйте контекст разговора
conversation_memory = {
    "client_name": "Петя",
    "last_topic": "цены на тату",
    "preferences": ["минимализм", "чёрно-белое"],
    "mentioned_dates": ["2025-12-10"]
}

# Используйте в ответах
f"Привет, {conversation_memory['client_name']}! Помню, ты интересовался {conversation_memory['last_topic']}"
```

#### 2. Эмоциональность и эмпатия

```python
emotional_responses = {
    "excitement": ["Вау! 🤩", "Это круто! ✨", "Обожаю такие идеи! 💫"],
    "sympathy": ["Понимаю тебя 🙏", "Да, бывает 😔", "Держись! 💪"],
    "encouragement": ["Давай попробуем! 🚀", "У тебя получится! ⭐", "Вперёд! 🎯"]
}
```

#### 3. Вариативность ответов

```python
# Вместо одного шаблона - несколько вариантов
greetings = [
    "Привет! 😊 Как дела?",
    "Хей! Рада тебя видеть! 👋",
    "Здарова! Что нового? 🌟",
    "О, привет! Как настроение? ☀️"
]

import random
response = random.choice(greetings)
```

#### 4. Персонализация

```python
async def personalize_response(response: str, client_data: dict) -> str:
    """Персонализировать ответ под клиента"""
    
    # Добавить имя
    if client_data.get("name"):
        response = response.replace("ты", client_data["name"])
    
    # Учесть историю
    if client_data.get("visit_count", 0) > 3:
        response += "\n\nКстати, ты уже наш постоянный клиент! 💜"
    
    # Учесть предпочтения
    if "минимализм" in client_data.get("preferences", []):
        response += "\n\nКстати, у нас новые минималистичные эскизы! Хочешь глянуть?"
    
    return response
```

---

## 🎯 Полная интеграция

### Обновление обработчика сообщений

Замените в `src/bot/handlers/client_handler.py`:

```python
from src.ai.advanced_inka import get_advanced_inka

@router.message(F.text)
async def handle_text_message(message: Message, state: FSMContext):
    """Обработка с продвинутой INKA"""
    
    user_id = message.from_user.id
    user_text = message.text
    
    # Игнорируем команды меню
    if user_text in ["👤 Личный кабинет", "📅 Записать на прием", ...]:
        return
    
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    
    # Создаём продвинутую INKA с доступом к данным
    inka = get_advanced_inka(
        api_key=config.openai_api_key,
        assistant_id=config.openai_assistant_id,
        sheets_client=sheets,
        calendar_service=None  # Добавьте если нужен календарь
    )
    
    # Получаем историю
    state_data = await state.get_data()
    history = state_data.get("conversation_history", [])
    
    # Typing indicator
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Получаем ответ от INKA
    response = await inka.chat(user_text, str(user_id), history)
    
    # Сохраняем в историю
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": response})
    history = history[-10:]  # Последние 10 сообщений
    
    await state.update_data(conversation_history=history)
    
    # Отправляем ответ
    await message.answer(response)
```

---

## 🚀 Деплой обновлений

```bash
# 1. Задеплоить обновлённый код
gcloud run deploy telegram-bot \
  --source . \
  --region us-central1 \
  --project tattoo-480007 \
  --set-secrets=TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,OPENAI_API_KEY=openai-api-key:latest \
  --set-env-vars=OPENAI_ASSISTANT_ID=asst_LBGeLxauJ3nYbauR3pilbifN

# 2. Проверить логи
gcloud logging read "resource.type=cloud_run_revision" --limit=50 --project=tattoo-480007
```

---

## 📊 Мониторинг и улучшение

### Логирование взаимодействий

```python
# Логируйте все взаимодействия для анализа
import logging

logger.info(f"User {user_id}: {user_message}")
logger.info(f"INKA response: {response}")
logger.info(f"Functions called: {functions_used}")
```

### Сбор feedback

```python
# Добавьте кнопки оценки
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

feedback_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="👍 Полезно", callback_data="feedback_good"),
        InlineKeyboardButton(text="👎 Не то", callback_data="feedback_bad")
    ]
])

await message.answer(response, reply_markup=feedback_kb)
```

### Анализ и дообучение

Периодически:
1. Собирайте логи неудачных взаимодействий
2. Анализируйте, где модель ошибается
3. Добавляйте эти кейсы в training dataset
4. Переобучайте модель

---

## 🎓 Итоговый чеклист

- [ ] Обновить Assistant с функциями
- [ ] Создать training dataset
- [ ] Запустить fine-tuning (опционально)
- [ ] Интегрировать с Google Sheets
- [ ] Интегрировать с Google Calendar
- [ ] Добавить интернет-поиск
- [ ] Обновить обработчики бота
- [ ] Задеплоить на Cloud Run
- [ ] Протестировать все функции
- [ ] Настроить мониторинг
- [ ] Собирать feedback

---

**Теперь ваша INKA будет:**
✅ Работать с реальными данными из Google Sheets
✅ Проверять календарь и предлагать свободные слоты
✅ Искать актуальную информацию
✅ Общаться естественно, как человек
✅ Запоминать контекст разговора
✅ Персонализировать ответы
