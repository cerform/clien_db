# 🎨 Telegram Bot для Тату-Салона

Полностью автоматизированный Telegram-бот на базе **Aiogram v3** с AI-ассистентом **INKA**, синхронизацией с **Google Calendar** и хранением данных в **Google Sheets**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Aiogram](https://img.shields.io/badge/Aiogram-3.4+-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-purple)
![Google APIs](https://img.shields.io/badge/Google%20APIs-Sheets%2C%20Calendar-red)

**[🚀 Быстрый старт](QUICKSTART.md)** • **[📚 Документация](#-документация)** • **[🤖 INKA AI](INKA.md)** • **[📊 База данных](DATABASE.md)** • **[🔧 Deployment](DEPLOYMENT.md)**

---

## 🔥 Основные возможности

### 👤 Для клиентов:
- ✅ Просмотр доступных временных слотов
- ✅ Выбор мастера по специализации
- ✅ Запись на процедуру
- ✅ Просмотр и управление своими записями
- ✅ Перенос или отмена записи

### 👨‍💼 Для мастеров:
- ✅ Синхронизация с Google Calendar
- ✅ Управление расписанием
- ✅ Подтверждение/отклонение заявок
- ✅ Блокировка времени для перерывов

### 👨‍💻 Для администратора:
- ✅ Полный CRUD клиентов
- ✅ Управление мастерами и их расписанием
- ✅ CRUD записей
- ✅ Просмотр статистики
- ✅ Управление данными через Google Sheets

### 💾 База данных (Google Sheets):
- `clients` - данные клиентов
- `masters` - информация о мастерах
- `calendar` - расписание мастеров
- `bookings` - записи на услуги

---

## 🚀 Стек технологий

| Компонент | Версия |
|-----------|---------|
| Python | 3.10+ |
| Aiogram | 3.4.1 |
| Google Sheets API | v4 |
| Google Calendar API | v3 |
| google-auth-oauthlib | 1.2.0 |
| python-dotenv | 1.0.1 |
| pytz | 2024.1 |

---

## 📦 Структура проекта

```
clien_db/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── init_db.py                 # Инициализация БД
│
├── src/
│   ├── __init__.py
│   ├── main.py                # Главная точка входа с интерактивным меню
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config.py          # Конфигурация приложения
│   │   ├── constants.py       # Константы и переменные
│   │   └── logging_config.py  # Конфигурация логирования
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── env_loader.py      # Загрузка переменных окружения
│   │   ├── timezone.py        # Работа с временными зонами
│   │   └── validators.py      # Валидаторы данных
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── sheets_client.py   # Google Sheets API клиент
│   │
│   ├── calendars/
│   │   ├── __init__.py
│   │   ├── google_calendar_sync.py  # Синхронизация с Google Calendar
│   │   └── slots_finder.py         # Поиск доступных слотов
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── client_service.py   # Сервис клиентов
│   │   ├── master_service.py   # Сервис мастеров
│   │   ├── booking_service.py  # Сервис записей
│   │   └── admin_service.py    # Административный сервис
│   │
│   └── bot/
│       ├── __init__.py
│       ├── loader.py           # Инициализация бота
│       ├── keyboards/
│       │   └── __init__.py     # Клавиатуры и кнопки
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── start_handler.py        # Обработчик /start
│       │   ├── client_handler.py       # Обработчики для клиентов
│       │   ├── master_handler.py       # Обработчики для мастеров
│       │   └── admin_handler.py        # Обработчики для администратора
│       └── middlewares/
│           ├── __init__.py
│           └── auth_middleware.py      # Middleware аутентификации
```

---

## 📋 Требования

- Python 3.10 или выше
- Аккаунт Google с включенным Google Sheets API
- Аккаунт Google с включенным Google Calendar API
- Telegram аккаунт и Bot Token от @BotFather
- Интернет-соединение

---

## ⚙️ Установка и конфигурация

### 1️⃣ Клонирование репозитория

```bash
git clone <repository_url>
cd clien_db
```

### 2️⃣ Создание виртуального окружения

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4️⃣ Получение Telegram Bot Token

1. Откройте Telegram и найдите @BotFather
2. Напишите `/newbot`
3. Укажите имя бота
4. Укажите юзернейм бота
5. Скопируйте полученный токен

### 5️⃣ Настройка Google API

#### Создание Service Account:

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com)
2. Создайте новый проект
3. Включите **Google Sheets API**
4. Включите **Google Calendar API**
5. Создайте **Service Account** (IAM & Admin → Service Accounts)
6. Создайте ключ (JSON) и скачайте его
7. Сохраните файл как `credentials.json` в корне проекта

#### Создание Google Spreadsheet:

1. Откройте [Google Sheets](https://sheets.google.com)
2. Создайте новую таблицу
3. Переименуйте её (например, "Tattoo Salon Database")
4. Скопируйте ID из URL:
   ```
   https://docs.google.com/spreadsheets/d/{ID}/edit
   ```
5. Раздайте доступ Service Account'у (по email из credentials.json)

### 6️⃣ Конфигурация приложения

```bash
# Запустите интерактивное меню конфигурации
python src/main.py
```

Следуйте инструкциям в меню:
1. Введите Telegram Bot Token
2. Введите Google Spreadsheet ID
3. Укажите путь к credentials.json (или используйте по умолчанию)
4. Выберите временную зону
5. Установите Admin IDs

**Файл `.env` будет автоматически создан.**

### 7️⃣ Инициализация базы данных

```bash
python init_db.py
```

Это создаст необходимые листы в Google Sheets с заголовками.

---

## ▶️ Запуск бота

```bash
python src/main.py
```

Выберите пункт "2. ✅ Запустить бота" и бот начнет работу!

---

## 🎮 Использование

### Для клиентов:

1. Найдите бот в Telegram
2. Нажмите `/start`
3. Заполните регистрационную форму
4. Используйте меню для:
   - Просмотра профиля
   - Выбора мастера
   - Записи на услугу
   - Управления записями

### Для администратора:

Используйте команды через интерактивное меню:
- Управление клиентами
- Управление мастерами
- Просмотр статистики

**Примечание:** Установите свой User ID в переменной `ADMIN_IDS` в `.env`

---

## 🔧 Конфигурация через .env

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=<your_bot_token>

# Google API
GOOGLE_SPREADSHEET_ID=<spreadsheet_id>
GOOGLE_CREDENTIALS_JSON=credentials.json

# Timezone
TIMEZONE=Europe/Moscow

# Logging
LOG_LEVEL=INFO

# Admin settings
ADMIN_IDS=123456789,987654321
```

---

## 📚 API Компоненты

### ClientService
Управление данными клиентов:
```python
from src.services.client_service import ClientService

client_service.create_client(user_id, name, phone, email)
client_service.get_client(user_id)
client_service.get_all_clients()
client_service.update_client(user_id, name=..., phone=..., email=...)
```

### MasterService
Управление мастерами:
```python
from src.services.master_service import MasterService

master_service.create_master(name, specialization, phone, calendar_id)
master_service.get_all_masters()
master_service.get_master_by_name(name)
```

### BookingService
Управление записями:
```python
from src.services.booking_service import BookingService

booking_service.create_booking(user_id, master_id, date, time, service)
booking_service.get_user_bookings(user_id)
booking_service.get_master_bookings(master_id)
booking_service.update_booking_status(booking_id, status)
```

### GoogleSheetsClient
Работа с Google Sheets:
```python
from src.db.sheets_client import GoogleSheetsClient

sheets = GoogleSheetsClient(credentials_file, spreadsheet_id)
sheets.get_sheet_values(sheet_name)
sheets.append_row(sheet_name, values)
sheets.update_range(sheet_name, range_spec, values)
sheets.find_row(sheet_name, column_index, value)
```

---

## 🚨 Логирование

Логи сохраняются в `logs/bot.log`

Уровни логирования:
- `DEBUG` - детальная информация
- `INFO` - информационные сообщения
- `WARNING` - предупреждения
- `ERROR` - ошибки
- `CRITICAL` - критические ошибки

Измените `LOG_LEVEL` в `.env` для настройки уровня логирования.

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте файл логов: `logs/bot.log`
2. Убедитесь, что все переменные окружения установлены
3. Проверьте доступ к Google API
4. Проверьте наличие интернета

---

## 📄 Лицензия

Этот проект свободен для использования.

---

## 👨‍💻 Автор

Создано для управления записями в тату-салон через Telegram.

---

## 🔄 История версий

### v1.0.0 (текущая версия)
- ✅ Базовая функциональность бота
- ✅ Интеграция с Google Sheets
- ✅ Поддержка Google Calendar
- ✅ Интерактивное меню конфигурации
- ✅ Система логирования

---

## 📝 TODO

- [ ] Улучшение интерфейса (InlineKeyboard для слотов)
- [ ] SMS уведомления
- [ ] Email напоминания
- [ ] Платежи через Telegram
- [ ] Аналитика и статистика
- [ ] Мобильное приложение
- [ ] Веб-интерфейс для администратора
│   │   │   └── auth_middleware.py
│   │   ├── keyboards/
│   │   │   ├── __init__.py
│   │   │   ├── client_kb.py
│   │   │   ├── admin_kb.py
│   │   │   └── master_kb.py
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── start.py
│   │   │   ├── client_handlers.py
│   │   │   ├── admin_handlers.py
│   │   │   └── master_handlers.py
│   │   └── router.py
│   │
│   ├── google/
│   │   ├── __init__.py
│   │   ├── credentials.json         # placeholder
│   │   └── token.json               # placeholder
│   │
│   └── scripts/
│       ├── __init__.py
│       ├── init_google_sheets.py
│       └── register_webhook.py
│
└── tests/
    ├── __init__.py
    ├── test_slots.py
    ├── test_sheets_client.py
    └── test_handlers.py

---

## 📚 Документация

### 📖 Основные документы

| Документ | Описание |
|----------|---------|
| **[🚀 QUICKSTART.md](QUICKSTART.md)** | Начните отсюда! Быстрый старт за 5 минут |
| **[🤖 INKA.md](INKA.md)** | AI-ассистент, архитектура, примеры использования |
| **[📊 DATABASE.md](DATABASE.md)** | Структура БД, синхронизация, Google Sheets, Calendar |
| **[🔧 DEPLOYMENT.md](DEPLOYMENT.md)** | Cloud Run, CI/CD, мониторинг, масштабирование |

### 🎯 Быстрые ссылки

- **Локальная разработка**: `python -u run_production.py`
- **Cloud Run deployment**: `gcloud run deploy telegram-bot --source . --region us-central1`
- **Тестирование**: `python test_send_message.py`
- **Проверка перед деплоем**: `python pre_deploy_check.py`

---

## 🔑 Ключевые компоненты

### INKA AI (`src/ai/advanced_inka.py`)
- LLM интеграция через OpenAI Assistant API (GPT-4o)
- Поиск мастеров по специализации через keyword matching в bio
- Получение доступных слотов из Calendar + Sheets + Cache
- Ведение естественного диалога на русском языке

### DataSyncService (`src/services/data_sync.py`)
- Унифицированный доступ к данным из Sheets + Calendar
- Двусторонняя синхронизация (Sheets ↔ Calendar)
- Кэширование с TTL (1 час для masters/services/schedule, 15 мин для bookings)
- Автоматическая валидация данных

### Интеграции
- **Google Sheets**: masters, services, schedule, bookings, clients таблицы
- **Google Calendar**: синхронизация событий и слотов
- **OpenAI**: GPT-4o assistant для INKA AI

---

## 📊 Текущее состояние

✅ **Production Ready**

- ✅ 3 мастера, 8 услуг, 21 расписание запись
- ✅ INKA AI работает корректно
- ✅ Calendar синхронизирован
- ✅ Cloud Run deployment настроен
- ✅ CI/CD pipeline готов

---

**Made with ❤️ for tattoo salon automation**
