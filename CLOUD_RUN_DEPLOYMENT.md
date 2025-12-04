# Деплой Telegram Бота в Google Cloud Run

Полное руководство по развертыванию Telegram бота тату-салона в Google Cloud Run.

## 📋 Содержание

1. [Предварительные требования](#предварительные-требования)
2. [Быстрый старт](#быстрый-старт)
3. [Подробная инструкция](#подробная-инструкция)
4. [Настройка секретов](#настройка-секретов)
5. [Мониторинг и логи](#мониторинг-и-логи)
6. [Обновление сервиса](#обновление-сервиса)
7. [Устранение неполадок](#устранение-неполадок)

## 🎯 Предварительные требования

### 1. Google Cloud Project

Создайте проект в Google Cloud:
```bash
gcloud projects create YOUR_PROJECT_ID --name="Telegram Bot"
gcloud config set project YOUR_PROJECT_ID
```

### 2. Установка Google Cloud SDK

**macOS:**
```bash
brew install --cask google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows:**
Скачайте инсталлятор: https://cloud.google.com/sdk/docs/install

### 3. Аутентификация

```bash
gcloud auth login
gcloud auth application-default login
```

### 4. Необходимые данные

Подготовьте следующие данные:
- `TELEGRAM_BOT_TOKEN` - токен от @BotFather
- `GOOGLE_SHEETS_SPREADSHEET_ID` - ID таблицы Google Sheets
- `credentials.json` - файл с учетными данными Google Service Account

## 🚀 Быстрый старт

### Автоматический деплой (рекомендуется)

```bash
# 1. Убедитесь, что credentials.json в корне проекта
ls credentials.json

# 2. Запустите скрипт деплоя
./deploy.sh YOUR_PROJECT_ID us-central1
```

Скрипт автоматически:
- ✅ Включит необходимые API
- ✅ Создаст секреты из введенных данных
- ✅ Настроит Service Account с правами
- ✅ Соберет Docker образ
- ✅ Задеплоит сервис в Cloud Run

## 📖 Подробная инструкция

### Шаг 1: Включение API

```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com
```

### Шаг 2: Создание секретов

#### Telegram Bot Token
```bash
echo -n "YOUR_BOT_TOKEN" | gcloud secrets create telegram-bot-token \
    --data-file=- \
    --replication-policy="automatic"
```

#### Google Sheets ID
```bash
echo -n "YOUR_SPREADSHEET_ID" | gcloud secrets create google-sheets-id \
    --data-file=- \
    --replication-policy="automatic"
```

#### Google Credentials
```bash
gcloud secrets create google-credentials \
    --data-file=credentials.json \
    --replication-policy="automatic"
```

### Шаг 3: Service Account

```bash
# Создание Service Account
gcloud iam service-accounts create telegram-bot-sa \
    --display-name="Telegram Bot Service Account"

# Назначение прав для доступа к секретам
SA_EMAIL="telegram-bot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com"

gcloud secrets add-iam-policy-binding telegram-bot-token \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding google-sheets-id \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding google-credentials \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"
```

### Шаг 4: Сборка образа

```bash
# С использованием Cloud Build (рекомендуется)
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/telegram-bot

# Или локально с Docker
docker build -t gcr.io/YOUR_PROJECT_ID/telegram-bot .
docker push gcr.io/YOUR_PROJECT_ID/telegram-bot
```

### Шаг 5: Деплой в Cloud Run

```bash
gcloud run deploy telegram-bot \
    --image gcr.io/YOUR_PROJECT_ID/telegram-bot \
    --platform managed \
    --region us-central1 \
    --service-account telegram-bot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 3 \
    --port 8080 \
    --timeout 300s \
    --set-env-vars PYTHONUNBUFFERED=1,PYTHONDONTWRITEBYTECODE=1 \
    --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,GOOGLE_SHEETS_SPREADSHEET_ID=google-sheets-id:latest
```

## 🔐 Настройка секретов

### Просмотр секретов

```bash
gcloud secrets list
```

### Обновление секретов

```bash
# Обновить Telegram токен
echo -n "NEW_BOT_TOKEN" | gcloud secrets versions add telegram-bot-token --data-file=-

# Обновить Google Sheets ID
echo -n "NEW_SPREADSHEET_ID" | gcloud secrets versions add google-sheets-id --data-file=-

# Обновить credentials
gcloud secrets versions add google-credentials --data-file=credentials.json
```

### Удаление старых версий

```bash
# Удалить конкретную версию
gcloud secrets versions destroy VERSION_NUMBER --secret=SECRET_NAME

# Автоматическое удаление после определенного времени
gcloud secrets update SECRET_NAME --ttl=30d
```

## 📊 Мониторинг и логи

### Просмотр логов

```bash
# Real-time логи
gcloud run services logs tail telegram-bot --region us-central1

# Последние логи
gcloud run services logs read telegram-bot --region us-central1 --limit 100

# Фильтрация по уровню
gcloud run services logs read telegram-bot \
    --region us-central1 \
    --log-filter "severity>=ERROR"
```

### Метрики в Console

Перейдите в Cloud Console:
```
https://console.cloud.google.com/run/detail/us-central1/telegram-bot/metrics
```

### Алерты

Настройка уведомлений при ошибках:
```bash
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Bot Errors Alert" \
    --condition-threshold-value=5 \
    --condition-threshold-duration=300s
```

## 🔄 Обновление сервиса

### Быстрое обновление

```bash
# Использовать скрипт deploy.sh
./deploy.sh YOUR_PROJECT_ID us-central1
```

### Обновление образа без изменения конфигурации

```bash
# Пересборка и деплой
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/telegram-bot
gcloud run services update telegram-bot \
    --image gcr.io/YOUR_PROJECT_ID/telegram-bot:latest \
    --region us-central1
```

### Откат к предыдущей версии

```bash
# Посмотреть ревизии
gcloud run revisions list --service telegram-bot --region us-central1

# Откатить на конкретную ревизию
gcloud run services update-traffic telegram-bot \
    --to-revisions REVISION_NAME=100 \
    --region us-central1
```

### Канареечный деплой

```bash
# 90% трафика на старую версию, 10% на новую
gcloud run services update-traffic telegram-bot \
    --to-revisions OLD_REVISION=90,NEW_REVISION=10 \
    --region us-central1
```

## 🛠 Устранение неполадок

### Проблема: Бот не отвечает

**Проверьте логи:**
```bash
gcloud run services logs read telegram-bot --region us-central1 --limit 50
```

**Проверьте статус сервиса:**
```bash
gcloud run services describe telegram-bot --region us-central1
```

### Проблема: Ошибка доступа к секретам

**Проверьте права Service Account:**
```bash
gcloud secrets get-iam-policy telegram-bot-token
```

**Переназначьте права:**
```bash
gcloud secrets add-iam-policy-binding telegram-bot-token \
    --member="serviceAccount:telegram-bot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Проблема: Out of Memory

**Увеличьте память:**
```bash
gcloud run services update telegram-bot \
    --memory 1Gi \
    --region us-central1
```

### Проблема: Cold Start

**Установите минимум инстансов:**
```bash
gcloud run services update telegram-bot \
    --min-instances 1 \
    --region us-central1
```

### Проблема: Таймауты

**Увеличьте таймаут:**
```bash
gcloud run services update telegram-bot \
    --timeout 600s \
    --region us-central1
```

## 💰 Оптимизация расходов

### Мониторинг стоимости

```bash
# Просмотр использования
gcloud logging read "resource.type=cloud_run_revision" \
    --format json \
    --limit 1000 | \
    jq '[.[] | {timestamp, severity, textPayload}]'
```

### Рекомендации по снижению расходов

1. **Используйте минимальные ресурсы:**
   - Memory: 512Mi (достаточно для бота)
   - CPU: 1 (1 vCPU)
   - Min instances: 0 (если можно терпеть cold start)

2. **Оптимизируйте образ:**
   - Используйте multi-stage build (уже в Dockerfile)
   - Удаляйте ненужные зависимости

3. **Настройте автоскейлинг:**
   ```bash
   gcloud run services update telegram-bot \
       --min-instances 0 \
       --max-instances 3 \
       --concurrency 80 \
       --region us-central1
   ```

## 🔗 Полезные ссылки

- [Cloud Run Документация](https://cloud.google.com/run/docs)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Build](https://cloud.google.com/build/docs)
- [Pricing Calculator](https://cloud.google.com/products/calculator)

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в Cloud Console
2. Убедитесь, что все секреты настроены правильно
3. Проверьте права Service Account
4. Обратитесь к [документации Cloud Run](https://cloud.google.com/run/docs)

---

**Готово!** 🎉 Ваш Telegram бот теперь работает в Google Cloud Run с автоматическим масштабированием и высокой доступностью.
