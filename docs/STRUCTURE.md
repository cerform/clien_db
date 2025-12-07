# 🗺️ Карта Проекта

## 🚀 БЫСТРЫЙ СТАРТ

### 👉 Начните отсюда:
1. **[QUICKSTART.md](QUICKSTART.md)** - 5 минут для локального запуска
2. **[INKA.md](INKA.md)** - понимание AI логики
3. **[DATABASE.md](DATABASE.md)** - структура данных
4. **[DEPLOYMENT.md](DEPLOYMENT.md)** - облачное развёртывание

---

## 📂 СТРУКТУРА ПРОЕКТА

### 🏠 Корень проекта
```
run_production.py       ⭐ ГЛАВНЫЙ ENTRY POINT (Cloud Run)
requirements.txt        Зависимости Python
Dockerfile              Контейнеризация для Cloud Run
cloudbuild.yaml         CI/CD конфигурация
```

### 📚 ДОКУМЕНТАЦИЯ (Читай в этом порядке)
```
QUICKSTART.md           ← НАЧНИ ОТСЮДА
├── Локальная разработка (5 мин)
├── Cloud Run deployment
└── Структура проекта

README.md               Основная информация о проекте
├── Возможности
├── Стек технологий
├── Ключевые компоненты
└── Ссылки на другие документы

INKA.md                 🤖 AI-Ассистент
├── Что такое INKA?
├── Архитектура
├── Методы использования
├── Примеры диалогов
└── Интеграция с другими сервисами

DATABASE.md             📊 База данных
├── Архитектура (Sheets + Calendar)
├── Инициализация БД
├── Синхронизация
├── Валидация данных
└── Текущее состояние

DEPLOYMENT.md           🚀 Cloud Run
├── Быстрый старт
├── Переменные окружения
├── CI/CD Pipeline
├── Мониторинг
├── Откат версий
└── Масштабирование

CLEANUP_REPORT.md       📋 История очистки проекта
```

### 🔧 ИСХОДНЫЙ КОД (src/)
```
src/
├── main.py                     Интерактивное меню (не используется в prod)
├── ai/
│   ├── advanced_inka.py        🤖 INKA AI с OpenAI
│   └── processor.py            (старый код)
├── bot/
│   ├── handlers/
│   │   ├── client_handler.py   ⭐ Маршрутизация сообщений в INKA
│   │   ├── start_handler.py    /start команда
│   │   ├── admin_handler.py    /admin команда
│   │   ├── master_handler.py   (может быть неиспользуемым)
│   │   └── admin_panel.py      Админ-панель
│   ├── loader.py               Инициализация бота
│   ├── keyboards/              (может быть неиспользуемым)
│   └── middlewares/
│       └── auth_middleware.py  Аутентификация
├── services/
│   ├── data_sync.py            🟢 Унифицированная синхронизация (Sheets + Calendar + Cache)
│   ├── booking_service.py      Управление бронированиями
│   ├── client_service.py       Управление клиентами
│   ├── master_service.py       Управление мастерами
│   ├── admin_service.py        Админ функции
│   └── procedure_service.py    Управление услугами
├── db/
│   ├── sheets_client.py        ✅ Google Sheets API client
│   ├── db_initializer.py       Инициализация БД
│   └── sheets_formatter.py     Форматирование Sheets
├── calendars/
│   └── calendar_init.py        ✅ Google Calendar API client
├── config/
│   ├── config.py               ✅ Конфигурация и переменные окружения
│   ├── constants.py            Константы
│   └── logging_config.py       Логирование
└── utils/
    ├── env_loader.py           Загрузка .env
    ├── timezone.py             Работа с временем
    └── validators.py           Валидация данных
```

### 🛠️ УТИЛИТЫ

#### Инициализация БД
```bash
python init_database.py        Создание схемы Sheets
python populate_real_data.py   Добавление мастеров/услуг/расписания
```

#### Операции с БД
```bash
python add_data.py             Добавление новых мастеров/услуг
python add_schedule.py         Добавление расписания
python fix_schedule.py         Исправление расписания
python sync_database.py        Синхронизация Sheets ↔ Calendar
python get_calendar_id.py      Получение Google Calendar ID
```

#### Тестирование
```bash
python pre_deploy_check.py     Проверка перед деплоем (8 проверок)
python test_send_message.py    Отправить тестовое сообщение
python test_unified_sync.py    Тест DataSync (masters, services, search, slots)
python health_check.py         Проверка здоровья сервиса
```

---

## 🎯 КЛЮЧЕВЫЕ КОМПОНЕНТЫ

### 1. **INKA AI** (`src/ai/advanced_inka.py`)
Главный интеллект бота. Использует:
- ✅ **OpenAI GPT-4o Assistant API**
- ✅ **DataSyncService** для доступа к данным
- ✅ **Keyword matching** в bio мастеров
- ✅ **Асинхронный чат** через Telegram

**Методы**:
- `async chat(user_text, user_id, conversation_history)` - основной
- `get_masters_unified()` - получить всех мастеров
- `search_masters_unified(keyword)` - поиск по ключевому слову
- `get_available_slots_unified(master_id, date)` - свободные слоты

### 2. **DataSyncService** (`src/services/data_sync.py`)
Унифицированный доступ к данным. Делает:
- ✅ Синхронизацию Sheets ↔ Calendar
- ✅ Кэширование с TTL (1 час)
- ✅ Валидацию данных (referential integrity)
- ✅ Оптимизацию производительности (7x faster)

**Методы**:
- `get_masters()` - с кэшем
- `get_services()` - с кэшем
- `search_masters(keyword)` - поиск в bio
- `get_available_slots(master_id, date, duration)` - слоты
- `sync_all()` - принудительная синхронизация

### 3. **Client Handler** (`src/bot/handlers/client_handler.py`)
Маршрутизирует сообщения в INKA. Кэширует:
- ✅ Google Sheets client
- ✅ Google Calendar service
- ✅ INKA instance

### 4. **Google APIs Integration**
- **sheets_client.py** - чтение/запись в таблицы
- **calendar_init.py** - работа с событиями календаря

---

## 📊 ДАННЫЕ В GOOGLE SHEETS

| Таблица | Строк | Колонки | Описание |
|---------|-------|---------|---------|
| **masters** | 3 | id, name, specialization, bio, phone | Мастера студии |
| **services** | 8 | id, name, duration_min, price_min | Услуги (тату, пирсинг) |
| **schedule** | 21 | id, master_id, day_of_week, start, end | Расписание (7 дней × 3 мастера) |
| **bookings** | N | id, client_id, master_id, service_id, date, time | Записи клиентов |
| **clients** | N | id, chat_id, name, phone, booking_date | Клиенты |

### Текущие мастера:
1. **Анна Леви** (m_anna_levi) - Реализм, черно-белая графика, 8+ лет
2. **Платон Сосницкий** (m_platon) - Реализм, минимализм
3. **Мойше** (m_moshe) - Пирсинг, консультации

---

## 🚀 РАЗВЁРТЫВАНИЕ

### Локально (разработка)
```bash
python -u run_production.py
# Бот слушает на http://0.0.0.0:8080
```

### Cloud Run (production)
```bash
gcloud run deploy telegram-bot --source . --region us-central1 --quiet
# URL: https://telegram-bot-408800151466.us-central1.run.app
```

### CI/CD (GitHub Actions + Cloud Build)
```yaml
# cloudbuild.yaml триггер:
# При push на main ветку → автоматический deploy
```

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

✅ **Production Ready**

- ✅ Бот работает в Cloud Run (текущая версия: 00074+)
- ✅ INKA AI правильно работает с мастерами
- ✅ Calendar синхронизирован
- ✅ DataSyncService оптимизирован
- ✅ Все тесты проходят (pre_deploy_check 8/8)
- ✅ Документация консолидирована
- ✅ Проект чист от дубликатов

---

## ⚡ БЫСТРЫЕ КОМАНДЫ

```bash
# Локальный запуск
python -u run_production.py

# Тестирование
python test_send_message.py
python test_unified_sync.py
python pre_deploy_check.py

# Cloud Run
gcloud run deploy telegram-bot --source . --region us-central1 --quiet

# Логи
gcloud logging read "resource.service.name=telegram-bot" --limit 100

# Откат версии
gcloud run revisions list --service=telegram-bot
gcloud run services update-traffic telegram-bot --to-revisions REVISION_NAME=100
```

---

## 🔗 ССЫЛКИ

- **GitHub**: https://github.com/cerform/clien_db (google-cloud-run branch)
- **Google Sheets**: https://docs.google.com/spreadsheets/d/17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ
- **OpenAI Assistant**: asst_LBGeLxauJ3nYbauR3pilbifN
- **Cloud Console**: https://console.cloud.google.com/run
- **Cloud Build**: https://console.cloud.google.com/cloud-build

---

**Последнее обновление**: 2025-12-05  
**Версия**: v1.0 (Cleaned & Optimized)  
**Статус**: ✅ Production Ready
