# 🚀 Инструкции по деплою на Cloud Run

## Текущий статус

✅ **Все изменения готовы к коммиту и деплою**

## Шаг 1: Коммит изменений

```bash
# Добавить все новые файлы
git add Dockerfile .dockerignore cloudbuild.yaml deploy_cloudrun.sh
git add .env.cloudrun.example PII_POLICY.md MIGRATION_COMPLETE.md
git add src/db/cloudsql_client.py
git add src/db/repositories/admin_messages_repo.py
git add scripts/setup_database.py scripts/migrate_sheets_to_cloudsql.py scripts/cloudsql_migrate.sh
git add tests/test_admin_messages_repo.py

# Добавить измененные файлы
git add README.md requirements.txt
git add run_production.py
git add src/bot/entrypoint.py
git add src/bot/handlers/admin_handlers.py
git add src/config/constants.py
git add src/db/repositories/__init__.py
git add src/services/admin_chat_service.py

# Создать коммит
git commit -F COMMIT_MESSAGE.txt

# Запушить изменения
git push origin fix-e2e-no-venv
```

## Шаг 2: Настройка окружения

### 2.1. Установка gcloud CLI (если еще не установлен)

```bash
# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# macOS
brew install --cask google-cloud-sdk

# Инициализация
gcloud init
```

### 2.2. Настройка проекта

```bash
# Установить проект
gcloud config set project tattoo-480007

# Аутентификация
gcloud auth login
gcloud auth application-default login
```

### 2.3. Включение необходимых API

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com
```

## Шаг 3: Подготовка .env файла

Убедитесь, что `.env` содержит все необходимые переменные:

```bash
# Telegram Bot
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ

# OpenAI API
OPENAI_API_KEY=sk-...

# Google Sheets
SPREADSHEET_ID=your_spreadsheet_id_here

# Cloud SQL
CLOUDSQL_PASSWORD=secure_password_here

# Admin Configuration
ADMIN_IDS=your_telegram_id_here
```

**⚠️ ВАЖНО:** Эти данные будут автоматически загружены в Secret Manager при деплое.

## Шаг 4: Деплой на Cloud Run

### Автоматический деплой (рекомендуется)

```bash
# Сделать скрипт исполняемым
chmod +x deploy_cloudrun.sh

# Запустить деплой
./deploy_cloudrun.sh
```

Скрипт автоматически:
1. ✅ Создаст Cloud SQL instance (если не существует)
2. ✅ Создаст базу данных `admin_messages`
3. ✅ Загрузит secrets в Secret Manager
4. ✅ Соберет Docker образ через Cloud Build
5. ✅ Задеплоит на Cloud Run с правильными настройками
6. ✅ Подключит Cloud SQL через Unix socket

### Note
- Скрипт автоматически включит AI mode (BOT_MODE=advanced) and add more memory (1Gi) if `OPENAI_API_KEY` is present in `.env` or in Secret Manager. Otherwise it will deploy in INKA-only mode (BOT_MODE=inka).

### Важная проверка: FORCE_SHEET_MODE и pre-deploy checks

Если вы хотите, чтобы проект работал только с Google Sheets (без локальных mock-данных), включите режим FORCE_SHEET_MODE.

```bash
# Включить принудительный sheet-only режим
export FORCE_SHEET_MODE=1
```

Скрипт деплоя будет запускать `scripts/predeploy_check.py` перед сборкой, чтобы убедиться, что все обязательные переменные окружения и доступ к Google API настроены. Если проверка не пройдёт — деплой будет остановлен.


### Ручной деплой (опционально)

Если нужен больший контроль:

```bash
# 1. Создать Cloud SQL instance
gcloud sql instances create tattoo-bot-db \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=us-central1

# 2. Создать базу данных
gcloud sql databases create admin_messages --instance=tattoo-bot-db

# 3. Установить пароль root
gcloud sql users set-password root \
  --instance=tattoo-bot-db \
  --password=YOUR_PASSWORD

# 4. Создать secrets
echo -n "YOUR_BOT_TOKEN" | gcloud secrets create BOT_TOKEN --data-file=-
echo -n "YOUR_OPENAI_KEY" | gcloud secrets create OPENAI_API_KEY --data-file=-
echo -n "YOUR_CLOUDSQL_PASSWORD" | gcloud secrets create CLOUDSQL_PASSWORD --data-file=-
echo -n "YOUR_SPREADSHEET_ID" | gcloud secrets create SPREADSHEET_ID --data-file=-

# 5. Собрать образ
gcloud builds submit --tag gcr.io/tattoo-480007/tattoo-bot

# 6. Деплой на Cloud Run
gcloud run deploy tattoo-bot \
  --image gcr.io/tattoo-480007/tattoo-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --add-cloudsql-instances tattoo-480007:us-central1:tattoo-bot-db \
  --set-env-vars "CLOUD_RUN_ENV=true,DB_SOCKET_DIR=/cloudsql" \
  --set-secrets "BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest"
```

## Шаг 5: Настройка Telegram Webhook

После успешного деплоя:

```bash
# Получить URL сервиса
SERVICE_URL=$(gcloud run services describe tattoo-bot \
  --region=us-central1 \
  --format='value(status.url)')

echo "Service URL: $SERVICE_URL"

# Установить webhook
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=${SERVICE_URL}/webhook/telegram"

# Проверить webhook
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

## Шаг 6: Верификация

### 6.1. Проверка логов

```bash
# Просмотр последних логов
gcloud run logs read --service=tattoo-bot --region=us-central1 --limit=50

# Следить за логами в реальном времени
gcloud run logs tail --service=tattoo-bot --region=us-central1
```

### 6.2. Проверка Cloud SQL

```bash
# Подключиться к Cloud SQL
gcloud sql connect tattoo-bot-db --user=root

# В MySQL консоли:
USE admin_messages;
SHOW TABLES;
SELECT COUNT(*) FROM admin_messages;
```

### 6.3. Тестирование бота

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте `/start`
4. Проверьте, что бот отвечает

### 6.4. Проверка админ-функций

1. Отправьте сообщение боту от имени администратора
2. Проверьте, что сообщение сохранилось в Cloud SQL:

```bash
gcloud sql connect tattoo-bot-db --user=root
USE admin_messages;
SELECT * FROM admin_messages ORDER BY created_at DESC LIMIT 5;
```

## Шаг 7: Мониторинг

### Cloud Run Metrics

```bash
# Открыть в браузере
gcloud run services describe tattoo-bot --region=us-central1
```

Или в Cloud Console:
https://console.cloud.google.com/run?project=tattoo-480007

### Cloud SQL Metrics

https://console.cloud.google.com/sql/instances?project=tattoo-480007

## Устранение неполадок

### Проблема: Бот не отвечает

```bash
# Проверить логи
gcloud run logs read --service=tattoo-bot --region=us-central1 --limit=50

# Проверить webhook
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

### Проблема: Cloud SQL не подключается

```bash
# Проверить статус instance
gcloud sql instances describe tattoo-bot-db

# Проверить логи Cloud Run
gcloud run logs read --service=tattoo-bot --region=us-central1 | grep -i "cloud.*sql\|mysql"
```

### Проблема: Secrets не загружаются

```bash
# Список secrets
gcloud secrets list

# Проверить версии
gcloud secrets versions list BOT_TOKEN
gcloud secrets versions list OPENAI_API_KEY
```

## Откат изменений

Если что-то пошло не так:

```bash
# Откатить на предыдущую версию
gcloud run services update-traffic tattoo-bot \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=us-central1

# Список ревизий
gcloud run revisions list --service=tattoo-bot --region=us-central1
```

## 🎉 Готово!

После успешного деплоя:
- ✅ Бот работает на Cloud Run
- ✅ Использует Cloud SQL для admin_messages
- ✅ Автоматически масштабируется (0-10 инстансов)
- ✅ Webhook настроен корректно
- ✅ Все secrets защищены в Secret Manager

**Service URL:** Проверьте в логах или в Cloud Console

**Админ панель:** `https://SERVICE_URL`

**API Health Check:** `https://SERVICE_URL/api/health`
