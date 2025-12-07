# 📁 Структура Проекта

```
clien_db/
├── 🚀 PRODUCTION
│   ├── run_production.py          ⭐ Главный entry point для Cloud Run
│   ├── requirements.txt           Зависимости Python
│   ├── Dockerfile                 Контейнеризация
│   ├── .gitignore
│   └── .env.example               Шаблон переменных окружения
│
├── 📚 docs/                       Полная документация
│   ├── README.md                  Обзор проекта
│   ├── QUICKSTART.md              Быстрый старт (5 мин)
│   ├── INKA.md                    AI-ассистент
│   ├── DATABASE.md                База данных
│   ├── DEPLOYMENT.md              Cloud Run & CI/CD
│   ├── STRUCTURE.md               Карта проекта
│   ├── DOCS.md                    Индекс документации
│   └── CLEANUP_REPORT.md          История оптимизации
│
├── 🔧 setup/                      Инициализация и заполнение БД
│   ├── __init__.py
│   ├── init_database.py           Создание схемы Sheets
│   ├── populate_database.py       Заполнение данными
│   └── populate_real_data.py      Тестовые данные (мастера, услуги)
│
├── 🛠️ scripts/                     Утилиты для управления БД
│   ├── __init__.py
│   ├── add_data.py                Добавить мастера/услуги
│   ├── add_schedule.py            Добавить расписание
│   ├── fix_schedule.py            Исправить расписание
│   ├── sync_database.py           Синхронизировать Sheets ↔ Calendar
│   └── get_calendar_id.py         Получить Google Calendar ID
│
├── ✅ tests/                       Unit & Integration тесты
│   ├── __init__.py
│   ├── conftest.py                Fixtures для pytest
│   ├── test_send_message.py       Webhook тест
│   ├── test_unified_sync.py       Тест DataSync
│   └── pre_deploy_check.py        Проверка перед деплоем (8 проверок)
│
├── 🐳 ci-cd/                      CI/CD конфигурация
│   ├── cloudbuild.yaml            Google Cloud Build
│   ├── .github/
│   │   └── workflows/             GitHub Actions (будущее)
│   └── README.md                  Инструкции CI/CD
│
├── 🔐 config/                     Конфигурация и переменные окружения
│   ├── .env                       Переменные окружения (НЕ в git)
│   ├── .env.example               Шаблон .env
│   └── README.md                  Инструкции конфигурации
│
├── 📊 monitoring/                 Мониторинг и health checks
│   ├── __init__.py
│   ├── health_check.py            Health check endpoint
│   ├── metrics.py                 Сбор метрик
│   └── README.md                  Инструкции мониторинга
│
├── 📦 src/                        Исходный код приложения
│   ├── __init__.py
│   ├── main.py
│   ├── ai/                        🤖 INKA AI
│   │   ├── advanced_inka.py
│   │   └── processor.py
│   ├── bot/                       Telegram handlers
│   │   ├── handlers/
│   │   ├── middlewares/
│   │   ├── keyboards/
│   │   └── loader.py
│   ├── services/                  Бизнес-логика
│   │   ├── data_sync.py           🟢 DataSync (Sheets + Calendar + Cache)
│   │   ├── booking_service.py
│   │   ├── client_service.py
│   │   ├── master_service.py
│   │   ├── admin_service.py
│   │   └── procedure_service.py
│   ├── db/                        Database layer
│   │   ├── sheets_client.py       Google Sheets API
│   │   ├── db_initializer.py
│   │   └── sheets_formatter.py
│   ├── calendars/                 Calendar integration
│   │   └── calendar_init.py       Google Calendar API
│   ├── config/                    Configuration
│   │   ├── config.py
│   │   ├── constants.py
│   │   └── logging_config.py
│   └── utils/                     Utilities
│       ├── env_loader.py
│       ├── timezone.py
│       └── validators.py
│
├── .gitignore                     Git ignore rules
├── .dockerignore                  Docker ignore rules
└── Dockerfile                     Docker контейнер

```

## 📂 Назначение папок

### 📚 `docs/` - Документация
Полная документация проекта:
- Начните с `README.md`
- Для быстрого старта: `QUICKSTART.md`
- По темам: `INKA.md`, `DATABASE.md`, `DEPLOYMENT.md`
- Навигация: `DOCS.md`, `STRUCTURE.md`

**Команда для просмотра:**
```bash
cd docs && cat README.md
```

### 🔧 `setup/` - Инициализация БД
Скрипты для первоначальной настройки:
- `init_database.py` - создание схемы
- `populate_database.py` - заполнение данными
- `populate_real_data.py` - тестовые данные

**Когда использовать:**
```bash
# Первая настройка
python setup/init_database.py
python setup/populate_real_data.py
```

### 🛠️ `scripts/` - Утилиты управления
Вспомогательные скрипты для управления БД:
- `add_data.py` - добавить записи
- `add_schedule.py` - добавить расписание
- `fix_schedule.py` - исправить расписание
- `sync_database.py` - синхронизация
- `get_calendar_id.py` - получить ID календаря

**Когда использовать:**
```bash
# Добавить нового мастера
python scripts/add_data.py

# Исправить расписание
python scripts/fix_schedule.py
```

### ✅ `tests/` - Тестирование
Unit & Integration тесты:
- `test_send_message.py` - webhook тест
- `test_unified_sync.py` - тест синхронизации
- `pre_deploy_check.py` - предпроверка (8 проверок)
- `conftest.py` - pytest fixtures

**Когда использовать:**
```bash
# Все тесты
pytest tests/

# Конкретный тест
pytest tests/test_unified_sync.py

# Предпроверка перед деплоем
python tests/pre_deploy_check.py
```

### 🐳 `ci-cd/` - CI/CD
Конфигурация непрерывной интеграции и развёртывания:
- `cloudbuild.yaml` - Google Cloud Build
- `.github/workflows/` - GitHub Actions (будущее)

**Как это работает:**
```yaml
# При push на main ветку:
1. Запустить тесты (tests/)
2. Собрать Docker образ
3. Push в registry
4. Deploy на Cloud Run
```

### 🔐 `config/` - Конфигурация
Переменные окружения и конфигурация:
- `.env.example` - шаблон (В git)
- `.env` - реальные значения (НЕ в git)

**Когда использовать:**
```bash
# Копировать шаблон
cp config/.env.example config/.env

# Отредактировать переменные
nano config/.env
```

### 📊 `monitoring/` - Мониторинг
Health checks и метрики:
- `health_check.py` - endpoint проверки здоровья
- `metrics.py` - сбор метрик

**Когда использовать:**
```bash
# Проверить здоровье сервиса
curl https://telegram-bot.../health

# Смотреть метрики в Cloud Console
```

### 📦 `src/` - Исходный код
Основной исходный код приложения:
- `ai/` - INKA AI логика
- `bot/` - Telegram handlers
- `services/` - Бизнес-логика
- `db/` - Слой работы с БД
- `calendars/` - Google Calendar
- `config/` - Конфигурация
- `utils/` - Утилиты

**Структура:**
```
src/
├── Main entry point
└── Модули организованы по функциям
    ├── AI layer (ai/)
    ├── Bot layer (bot/)
    ├── Service layer (services/)
    └── Data layer (db/)
```

---

## 🚀 Быстрый старт с новой структурой

### 1️⃣ Инициализация БД
```bash
python setup/init_database.py
python setup/populate_real_data.py
```

### 2️⃣ Запуск локально
```bash
python -u run_production.py
```

### 3️⃣ Тестирование
```bash
# Все тесты
pytest tests/

# Предпроверка
python tests/pre_deploy_check.py

# Webhook тест
python tests/test_send_message.py
```

### 4️⃣ Развёртывание
```bash
gcloud run deploy telegram-bot --source . --region us-central1 --quiet
```

---

## 📋 Файлы в корне (только критические)

| Файл | Назначение |
|------|-----------|
| `run_production.py` | ⭐ Entry point |
| `requirements.txt` | Зависимости |
| `Dockerfile` | Docker образ |
| `.gitignore` | Git ignore |
| `.dockerignore` | Docker ignore |
| `README.md` | Ссылка на docs/ |

---

## 📊 Преимущества новой структуры

✅ **Профессиональная организация**
- Каждая папка имеет чёткое назначение
- Разделение ответственности
- Легко масштабировать

✅ **Удобство разработки**
- `tests/` - вся тестирование в одном месте
- `scripts/` - вспомогательные скрипты отдельно
- `setup/` - инициализация отдельно от основного кода

✅ **DevOps готовность**
- `ci-cd/` - CI/CD конфиги
- `monitoring/` - мониторинг
- `config/` - управление конфигурацией

✅ **Масштабируемость**
- Легко добавить новые папки
- Легко добавить новые тесты
- Легко добавить новые утилиты

---

**Последнее обновление**: 2025-12-05  
**Версия**: v2.0 Professional DevOps Architecture
**Статус**: ✅ Production Ready
