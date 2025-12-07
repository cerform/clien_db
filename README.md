# 🎨 Telegram Bot для Тату-Салона

Полностью автоматизированный Telegram-бот на базе **Aiogram v3** с AI-ассистентом **INKA**, синхронизацией с **Google Calendar** и хранением данных в **Google Sheets**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Aiogram](https://img.shields.io/badge/Aiogram-3.4+-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-purple)
![Google APIs](https://img.shields.io/badge/Google%20APIs-Sheets%2C%20Calendar-red)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Production-green)

---

## 🗺️ Навигация

### 🎯 Новая информация (Production Ready!)
- **[🚀 Быстрый Deployment](QUICK_DEPLOYMENT.md)** - Развернуть в 1 минуту
- **[✅ Production Readiness Report](PRODUCTION_READINESS_REPORT.md)** - Статус системы
- **[📋 Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Пошаговая верификация
- **[🔍 QA Resolution Summary](QA_RESOLUTION_SUMMARY.md)** - Все исправления

### 📚 Документация
- **[📖 Полная документация](docs/README.md)** - все документы
- **[🚀 Быстрый старт](docs/QUICKSTART.md)** - 5 минут до рабочего бота
- **[🏗️ Архитектура](ARCHITECTURE.md)** - структура проекта
- **[🤖 INKA AI](docs/INKA.md)** - AI-ассистент
- **[📊 База данных](docs/DATABASE.md)** - структура данных
- **[🔧 Deployment](docs/DEPLOYMENT.md)** - Cloud Run & CI/CD
- **[📝 Deployment Guide](DEPLOYMENT_GUIDE.md)** - Полная архитектура

### 🔧 Папки

| Папка | Назначение | README |
|-------|-----------|--------|
| **📚 docs/** | Полная документация | [docs/README.md](docs/README.md) |
| **🔧 setup/** | Инициализация БД | [setup/README.md](setup/README.md) |
| **🛠️ scripts/** | Утилиты управления | [scripts/README.md](scripts/README.md) |
| **✅ tests/** | Тестирование | [tests/README.md](tests/README.md) |
| **🐳 ci-cd/** | CI/CD конфигурация | [ci-cd/README.md](ci-cd/README.md) |
| **🔐 config/** | Переменные окружения | [config/README.md](config/README.md) |
| **📊 monitoring/** | Мониторинг | [monitoring/README.md](monitoring/README.md) |
| **📦 src/** | Исходный код | [src/](src/) |

---

## 📊 Текущий Статус

### ✅ Production Ready!

| Компонент | Статус | Примечание |
|-----------|--------|-----------|
| **Bot Core** | ✅ Working | Telegram API интеграция |
| **Google Sheets** | ✅ Working | Read/Write operations |
| **Google Calendar** | ✅ Working | Calendar integration |
| **Configuration** | ✅ Working | Environment-based loading |
| **Authentication** | ✅ Working | Local + Cloud Run support |
| **Error Handling** | ✅ Fixed | All exceptions caught |
| **Admin Commands** | ✅ Added | Debug diagnostics |
| **Cloud Run** | ✅ Ready | New entrypoint created |

### 🎯 Все QA Issues Resolved (10/10)
```
✅ Critical (3):   Cloud Run, Validation, Credentials
✅ Major (3):      Client save, Filtering, Syntax
✅ Medium (4):     Admin IDs, Timezone, Debug, Env vars
```

### 🚀 Deployment Status
- **Current Revision**: tattoo-bot-00030 (ready)
- **Previous Revision**: tattoo-bot-00029-s7x (working)

---

## 🔥 Основные возможности

### 👤 Для клиентов
- ✅ Запись на процедуру к мастеру
- ✅ Выбор мастера по специализации (реализм, минимализм, пирсинг)
- ✅ Просмотр свободных слотов (синхронизация с Google Calendar)
- ✅ Естественное общение с AI-ассистентом (INKA)

### 👨‍🎨 Для мастеров
- ✅ Управление расписанием
- ✅ Синхронизация с Google Calendar
- ✅ Просмотр предстоящих записей

### 👨‍💻 Для администратора
- ✅ Управление мастерами и услугами
- ✅ Управление расписанием
- ✅ Просмотр статистики записей
- ✅ Редактирование данных через Google Sheets

---

## 🚀 Быстрый старт

### 1️⃣ Первая настройка (5 минут)
```bash
# Читать детально:
cat docs/QUICKSTART.md

# Или быстро:
cp config/.env.example config/.env  # Отредактировать ключи
python setup/init_database.py       # Создать схему БД
python setup/populate_real_data.py  # Заполнить данные
```

### 2️⃣ Запуск локально
```bash
python -u run_production.py
# Бот слушает на http://0.0.0.0:8080
```

### 3️⃣ Тестирование
```bash
# Все тесты
pytest tests/ -v

# Предпроверка перед деплоем
python tests/pre_deploy_check.py

# Отправить тестовое сообщение (в другом терминале)
python tests/test_send_message.py
```

### 4️⃣ Развёртывание в Cloud Run
```bash
gcloud run deploy telegram-bot --source . --region us-central1 --quiet
```

---

## 📦 Стек технологий

| Компонент | Версия | Назначение |
|-----------|---------|-----------|
| **Python** | 3.10+ | Язык программирования |
| **Aiogram** | 3.4+ | Telegram Bot Framework (webhook) |
| **OpenAI** | GPT-4 | AI Assistant (INKA) |
| **Google Sheets API** | v4 | Database (masters, services, schedule) |
| **Google Calendar API** | v3 | Availability (event synchronization) |
| **Docker** | Latest | Контейнеризация |
| **Google Cloud Run** | - | Production hosting |
| **Google Cloud Build** | - | CI/CD pipeline |

---

## 📁 Структура проекта

```
clien_db/
├── 🚀 run_production.py        Entry point (Cloud Run)
├── 📦 requirements.txt          Python зависимости
├── 🐳 Dockerfile                Контейнеризация
│
├── 📚 docs/                     Полная документация
│   ├── README.md                Overview
│   ├── QUICKSTART.md            5 минут старта
│   ├── INKA.md                  AI-ассистент
│   ├── DATABASE.md              Структура БД
│   ├── DEPLOYMENT.md            Cloud Run & CI/CD
│   ├── STRUCTURE.md             Карта проекта
│   └── DOCS.md                  Индекс документации
│
├── 🔧 setup/                    Инициализация БД
│   ├── init_database.py         Создание схемы
│   ├── populate_database.py     Заполнение данных
│   └── populate_real_data.py    Тестовые данные
│
├── 🛠️ scripts/                  Утилиты управления
│   ├── add_data.py              Добавить мастера/услуги
│   ├── add_schedule.py          Добавить расписание
│   ├── fix_schedule.py          Исправить расписание
│   ├── sync_database.py         Синхронизация Sheets↔Calendar
│   └── get_calendar_id.py       Получить Calendar ID
│
├── ✅ tests/                    Тестирование (pytest)
│   ├── test_send_message.py     Webhook тест
│   ├── test_unified_sync.py     Тест синхронизации
│   ├── pre_deploy_check.py      Предпроверка (8 проверок)
│   └── conftest.py              Pytest fixtures
│
├── 🐳 ci-cd/                    CI/CD конфигурация
│   └── cloudbuild.yaml          Google Cloud Build
│
├── 🔐 config/                   Переменные окружения
│   ├── .env.example             Шаблон (в git)
│   └── .env                     Реальные ключи (не в git)
│
├── 📊 monitoring/               Мониторинг
│   ├── health_check.py          Health endpoint
│   └── metrics.py               Сбор метрик
│
└── 📦 src/                      Исходный код
    ├── ai/                      INKA AI
    ├── bot/                     Telegram handlers
    ├── services/                DataSyncService + бизнес-логика
    ├── db/                      Google Sheets API
    ├── calendars/               Google Calendar API
    ├── config/                  Configuration
    └── utils/                   Utilities
```

---

## ✅ Текущее состояние

**Production Ready ✅**

- ✅ 3 мастера (Анна, Платон, Мойше)
- ✅ 8 услуг (тату, пирсинг, консультации)
- ✅ 21 расписание запись (7 дней × 3 мастера)
- ✅ INKA AI работает корректно
- ✅ Google Calendar синхронизирован
- ✅ Все тесты pass (8/8 pre-deploy checks)
- ✅ Cloud Run deployment готов
- ✅ CI/CD pipeline настроен
- ✅ Мониторинг включен
- ✅ Документация полная и актуальная

---

## 🎯 Начните отсюда

### 👶 Новичок?
1. **[Прочитать docs/QUICKSTART.md](docs/QUICKSTART.md)** - 5 минут
2. **[Запустить локально](docs/QUICKSTART.md#локально-разработка)** - python run_production.py
3. **[Отправить тестовое сообщение](tests/README.md)** - python tests/test_send_message.py

### 👨‍💻 Разработчик?
1. **[Изучить ARCHITECTURE.md](ARCHITECTURE.md)** - структура
2. **[Посмотреть src/](src/)** - исходный код
3. **[Запустить тесты](tests/README.md)** - pytest tests/

### 🚀 Deployment?
1. **[Читать docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Cloud Run
2. **[Посмотреть ci-cd/](ci-cd/)** - CI/CD pipeline
3. **[Запустить pre_deploy_check.py](tests/README.md)** - финальная проверка

### 📊 Мониторинг?
1. **[Читать monitoring/README.md](monitoring/README.md)** - как смотреть логи
2. **[Посмотреть health check](monitoring/health_check.py)** - состояние сервиса
3. **[Настроить алерты](monitoring/README.md#-алерты)** - уведомления об ошибках

---

## 🔗 Полезные ссылки

| Ресурс | Ссылка |
|--------|--------|
| **Google Sheets (БД)** | [Открыть таблицу](https://docs.google.com/spreadsheets/d/17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ) |
| **OpenAI Assistant** | asst_LBGeLxauJ3nYbauR3pilbifN |
| **GitHub Repo** | https://github.com/cerform/clien_db (google-cloud-run branch) |
| **Cloud Run** | [Console](https://console.cloud.google.com/run) |
| **Cloud Build** | [Triggers](https://console.cloud.google.com/cloud-build/triggers) |
| **Cloud Logs** | [Logging](https://console.cloud.google.com/logs) |

---

## 🤝 Контакт

- **Owner**: @cerform
- **Repository**: https://github.com/cerform/clien_db
- **Branch**: google-cloud-run
- **Last Update**: 2025-12-05
- **Version**: v2.0 Professional DevOps

---

**Made with ❤️ for professional tattoo salon automation**
