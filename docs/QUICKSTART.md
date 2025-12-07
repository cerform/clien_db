# 🚀 Быстрый Старт

## Локально (разработка)

```bash
# 1. Клонирование репо
git clone https://github.com/cerform/clien_db.git
cd clien_db

# 2. Установка зависимостей
pip install -r requirements.txt

# 3. Создание .env
cp .env.example .env
# Отредактировать .env с вашими ключами

# 4. Инициализация БД
python init_database.py
python populate_real_data.py

# 5. Запуск бота (локально, через polling)
python -u run_production.py
```

## В Cloud Run (production)

```bash
# 1. Развёртывание
gcloud run deploy telegram-bot \
  --source . \
  --region us-central1 \
  --memory 512Mi \
  --quiet

# 2. Проверка статуса
gcloud run describe telegram-bot --region us-central1

# 3. Просмотр логов
gcloud logging read "resource.labels.revision_name=telegram-bot-XXXXX" --limit 100
```

## Основные скрипты

| Скрипт | Описание | Когда использовать |
|--------|---------|-------------------|
| `run_production.py` | Основной bot на webhook | Production (Cloud Run) |
| `init_database.py` | Инициализация БД | При первой настройке |
| `populate_real_data.py` | Заполнение тестовыми данными | После инициализации БД |
| `pre_deploy_check.py` | Проверка перед деплоем | Перед `gcloud run deploy` |
| `test_send_message.py` | Отправка тестовых сообщений | Тестирование webhook |
| `test_unified_sync.py` | Тест синхронизации данных | Тестирование DataSync |

## Структура проекта

```
clien_db/
├── run_production.py          # 🔴 Main entry point (Cloud Run)
├── src/
│   ├── ai/
│   │   ├── advanced_inka.py    # INKA LLM integration
│   │   └── processor.py
│   ├── bot/
│   │   ├── handlers/           # Message handlers
│   │   ├── middlewares/        # Auth middleware
│   │   └── keyboards/
│   ├── services/
│   │   ├── data_sync.py        # 🟢 Unified data sync (Sheets + Calendar + Cache)
│   │   ├── booking_service.py
│   │   └── ...
│   ├── db/
│   │   ├── sheets_client.py    # Google Sheets API
│   │   └── db_initializer.py
│   ├── calendars/
│   │   └── calendar_init.py    # Google Calendar API
│   └── config/
│       └── config.py           # Settings
├── requirements.txt
├── Dockerfile
├── cloudbuild.yaml             # CI/CD
└── README.md
```

## Требования

- Python 3.10+
- Google Cloud Account (для Cloud Run)
- Telegram Bot (от @BotFather)
- OpenAI API Key
- Google Sheets API credentials
- Google Calendar API credentials

## Первые шаги

1. **Прочитать**: [README.md](README.md)
2. **Настроить**: [DEPLOYMENT.md](DEPLOYMENT.md)
3. **Понять архитектуру**: [DATABASE.md](DATABASE.md)
4. **Тестировать**: `python test_send_message.py`
