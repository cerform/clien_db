# 🚀 Развёртывание в Cloud Run

## Быстрый старт

```bash
# 1. Выполнить проверки перед деплоем
python pre_deploy_check.py

# 2. Развернуть в Cloud Run
gcloud run deploy telegram-bot \
  --source . \
  --region us-central1 \
  --memory 512Mi \
  --quiet

# 3. Проверить статус
gcloud run describe telegram-bot --region us-central1
```

## Требования

### Локально

- `gcloud` CLI
- Авторизация: `gcloud auth login`
- Docker (для локального тестирования)

### Google Cloud Project

- ✅ Cloud Run API включена
- ✅ Artifact Registry API включена
- ✅ Sheets API включена
- ✅ Calendar API включена
- ✅ Service Account с ролями:
  - `roles/editor` (для Sheets)
  - `roles/calendar.admin` (для Calendar)

### Telegram

- Bot Token от @BotFather
- Webhook URL должен быть HTTPS

### OpenAI

- API Key

## Настройка переменных окружения

### Локальная разработка (.env файл)

```bash
TELEGRAM_BOT_TOKEN=123456:ABC...
GOOGLE_SPREADSHEET_ID=17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ
GOOGLE_CREDENTIALS_JSON=credentials.json
GOOGLE_CALENDAR_ID=calendar_id@group.calendar.google.com
OPENAI_API_KEY=sk-proj-...
OPENAI_ASSISTANT_ID=asst_...
ADMIN_IDS=123456789,987654321
TIMEZONE=Asia/Jerusalem
LOG_LEVEL=INFO
```

### Cloud Run (в Dockerfile)

```dockerfile
ENV TELEGRAM_BOT_TOKEN="..."
ENV GOOGLE_SPREADSHEET_ID="..."
ENV GOOGLE_CALENDAR_ID="..."
ENV OPENAI_API_KEY="..."
ENV OPENAI_ASSISTANT_ID="..."
ENV ADMIN_IDS="..."
```

Или через `gcloud`:

```bash
gcloud run deploy telegram-bot \
  --update-env-vars \
  TELEGRAM_BOT_TOKEN=value,\
  GOOGLE_SPREADSHEET_ID=value,\
  ...
```

## Архитектура

```
                    ┌─────────────────────────────────┐
                    │      Telegram Bot API           │
                    │   (sends webhooks to our app)   │
                    └──────────────┬──────────────────┘
                                   │ POST /webhook
                    ┌──────────────▼──────────────────┐
                    │   Google Cloud Run (512Mi)      │
                    │   ├─ run_production.py          │
                    │   ├─ Aiogram 3.x (webhook)      │
                    │   ├─ INKA AI (OpenAI)           │
                    │   └─ Handlers                   │
                    └──────────────┬──────────────────┘
                    ┌──────────────┴──────────────────┐
        ┌───────────▼────────────┐   ┌──────────────▼────────┐
        │  Google Sheets API     │   │ Google Calendar API   │
        │  (Data: masters,       │   │ (Events & slots)      │
        │   services, schedule)  │   │                       │
        └────────────────────────┘   └───────────────────────┘
```

## Pipeline CI/CD

### GitHub Actions

Файл: `cloudbuild.yaml` (Google Cloud Build)

```yaml
steps:
  # 1. Сборка образа
  - name: gcr.io/cloud-builders/docker
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/telegram-bot:latest', '.']

  # 2. Push в registry
  - name: gcr.io/cloud-builders/docker
    args: ['push', 'gcr.io/$PROJECT_ID/telegram-bot:latest']

  # 3. Deploy в Cloud Run
  - name: gcr.io/cloud-builders/gke-deploy
    args:
      - run
      - --filename=.
      - --image=gcr.io/$PROJECT_ID/telegram-bot:latest
      - --location=us-central1
```

### Триггер

Автоматический deploy при push:
- На ветку `main`
- Путь: `cloudbuild.yaml`

## Мониторинг

### Логи

```bash
# Последние 100 логов
gcloud logging read "resource.service.name=telegram-bot" --limit 100

# Фильтр по ошибкам
gcloud logging read "resource.service.name=telegram-bot AND severity=ERROR" --limit 50

# Реал-тайм логирование
gcloud logging read "resource.service.name=telegram-bot" --limit 50 --follow
```

### Health Check

```bash
# Прямой запрос
curl https://telegram-bot-XXXXX.us-central1.run.app/health

# Ответ
{"status": "ok"}
```

### Метрики

```bash
# CPU usage, memory, requests
gcloud monitoring read "metric.type=run.googleapis.com/request_count" \
  --filter "resource.service_name=telegram-bot"
```

## Откат версии

```bash
# Список всех версий
gcloud run revisions list --service=telegram-bot

# Откат на предыдущую версию
gcloud run deploy telegram-bot --revision REVISION_NAME --no-traffic
gcloud run services update-traffic telegram-bot --to-revisions REVISION_NAME=100
```

## Масштабирование

### Текущие параметры

```bash
# Память: 512Mi
# Минимум экземпляров: 0
# Максимум экземпляров: 100 (по умолчанию)
# Timeout: 300 сек
```

### Увеличение памяти

```bash
gcloud run deploy telegram-bot --memory 1Gi --region us-central1
```

## Тестирование перед деплоем

```bash
# 1. Проверка конфигурации
python pre_deploy_check.py

# 2. Локальный тест
python -u run_production.py

# 3. Отправка тестового сообщения (в другом терминале)
python test_send_message.py
```

## Проблемы и решения

### Проблема: Webhook не получает сообщения
**Решение**: 
1. Проверить URL правильный: `gcloud run describe telegram-bot`
2. Проверить IAM политику: `roles/run.invoker` для `allUsers`

### Проблема: Бот отвечает медленно
**Решение**:
1. Увеличить память: `--memory 1Gi`
2. Проверить кэширование в DataSyncService

### Проблема: Google API ошибка 403
**Решение**:
1. Проверить Service Account права
2. Проверить API включены в Cloud Console
3. Обновить credentials.json в Dockerfile

### Проблема: OpenAI ошибка
**Решение**:
1. Проверить API ключ валидный
2. Проверить Assistant ID правильный
3. Проверить квота на аккаунте

## Откат на локальный polling (для разработки)

Изменить `run_production.py`:

```python
# Заменить webhook на polling
await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
```

## Ссылки

- 🔧 [Cloud Console](https://console.cloud.google.com)
- 📊 [Cloud Run Services](https://console.cloud.google.com/run)
- 📝 [Docker Documentation](https://docs.docker.com)
- 🤖 [Aiogram Documentation](https://docs.aiogram.dev)
