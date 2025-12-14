# 🔗 Постоянная настройка Telegram Webhook

## Что такое Webhook?

Webhook - это способ получения обновлений от Telegram в реальном времени. Вместо того, чтобы бот постоянно опрашивал сервера Telegram (polling), Telegram сам отправляет обновления на ваш сервер.

**Преимущества webhook:**
- ⚡ Мгновенная доставка сообщений
- 💰 Меньше нагрузки и затрат
- 🚀 Лучше для production

## 🚀 Быстрая настройка

После успешного деплоя на Cloud Run:

```bash
./scripts/setup_persistent_webhook.sh
```

Этот скрипт автоматически:
1. Получает URL вашего Cloud Run сервиса
2. Достаёт токен бота из Secret Manager
3. Устанавливает webhook в Telegram
4. Проверяет статус webhook
5. Сохраняет URL в .env
6. Тестирует доступность endpoint

## 📋 Ручная настройка

### 1. Получить URL сервиса

```bash
SERVICE_URL=$(gcloud run services describe telegram-bot \
  --region=us-central1 \
  --format="value(status.url)")

echo "Service URL: $SERVICE_URL"
```

### 2. Получить Bot Token

```bash
BOT_TOKEN=$(gcloud secrets versions access latest \
  --secret=telegram-bot-token \
  --project=tattoo-480007)
```

### 3. Установить webhook

```bash
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"${SERVICE_URL}/webhook\",
    \"drop_pending_updates\": true,
    \"allowed_updates\": [\"message\", \"callback_query\", \"my_chat_member\"]
  }"
```

### 4. Проверить webhook

```bash
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool
```

Ожидаемый ответ:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-service-url.run.app/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40,
    "ip_address": "xxx.xxx.xxx.xxx"
  }
}
```

## 🔍 Проверка работы webhook

### Тест 1: Проверить endpoint
```bash
curl -I https://your-service-url.run.app/webhook
```

Ожидается HTTP 200 или 405 (метод не разрешен, но endpoint существует)

### Тест 2: Отправить /start боту
Откройте бота в Telegram и отправьте `/start`

Бот должен ответить мгновенно.

### Тест 3: Проверить логи
```bash
gcloud run services logs read telegram-bot \
  --region=us-central1 \
  --limit=50
```

Должны появиться записи о полученных обновлениях.

## 🔄 Обновление webhook

После каждого деплоя webhook остаётся активным и указывает на тот же URL.

Но если URL сервиса изменился (например, после пересоздания сервиса):

```bash
./scripts/setup_persistent_webhook.sh
```

## ❌ Удаление webhook

Для локальной разработки с polling:

```bash
BOT_TOKEN=$(gcloud secrets versions access latest \
  --secret=telegram-bot-token \
  --project=tattoo-480007)

curl "https://api.telegram.org/bot${BOT_TOKEN}/deleteWebhook"
```

Затем запустите бота локально:
```bash
python run.py  # Uses polling mode
```

## 🐛 Troubleshooting

### Webhook не работает

1. **Проверить статус webhook:**
   ```bash
   curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
   ```

2. **Проверить логи Cloud Run:**
   ```bash
   gcloud run services logs read telegram-bot --region=us-central1 --limit=100
   ```

3. **Проверить, что сервис запущен:**
   ```bash
   gcloud run services describe telegram-bot --region=us-central1
   ```

4. **Проверить secrets:**
   ```bash
   gcloud run services describe telegram-bot --region=us-central1 --format="value(spec.template.spec.containers[0].env)"
   ```

### Ошибка "Connection refused"

Webhook URL должен быть HTTPS и публично доступен. Cloud Run автоматически предоставляет HTTPS.

### Ошибка "Certificate verify failed"

Cloud Run использует валидные SSL сертификаты. Если ошибка возникает:
1. Проверьте, что URL начинается с `https://`
2. Убедитесь, что сервис публично доступен (`--allow-unauthenticated`)

### Бот не отвечает

1. Проверьте endpoint:
   ```bash
   curl https://your-service.run.app/webhook
   ```

2. Проверьте, что webhook зарегистрирован:
   ```bash
   curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
   ```

3. Отправьте тестовое сообщение и проверьте логи:
   ```bash
   gcloud run services logs read telegram-bot --region=us-central1 --limit=20
   ```

## 📊 Мониторинг webhook

### Команды для мониторинга:

```bash
# Статус webhook
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | \
  python3 -m json.tool | \
  grep -E "(url|pending_update_count|last_error)"

# Логи за последние 5 минут
gcloud run services logs read telegram-bot \
  --region=us-central1 \
  --limit=50 \
  --format="value(textPayload)"

# Метрики Cloud Run
gcloud run services describe telegram-bot \
  --region=us-central1 \
  --format="value(status.traffic[0].percent,status.conditions)"
```

## 🔐 Безопасность

### Проверка подлинности обновлений

run_production.py автоматически проверяет подлинность входящих обновлений от Telegram.

Telegram отправляет специальный заголовок `X-Telegram-Bot-Api-Secret-Token`, который можно проверить.

### Ограничение доступа

По умолчанию Cloud Run endpoint публичный (`--allow-unauthenticated`), но только Telegram может отправлять валидные обновления.

Для дополнительной безопасности можно:
1. Добавить secret token в webhook
2. Проверять IP адреса Telegram
3. Использовать Cloud Armor для защиты

## 📝 Конфигурация в коде

Webhook настраивается в `run_production.py`:

```python
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates via webhook"""
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}
```

URL webhook определяется автоматически из Cloud Run:
```python
webhook_url = os.getenv('WEBHOOK_URL', f"{service_url}/webhook")
```

## ✅ Checklist после настройки

- [ ] Webhook установлен (`getWebhookInfo` показывает URL)
- [ ] Нет pending updates (или они обрабатываются)
- [ ] Endpoint доступен (curl возвращает 200/405)
- [ ] Бот отвечает на /start мгновенно
- [ ] Логи Cloud Run показывают входящие обновления
- [ ] URL сохранён в .env для reference

## 🎯 Следующие шаги

После успешной настройки webhook:

1. **Обновить Telegram ID суперадмина:**
   ```bash
   # Получите ваш ID у @userinfobot
   python3 scripts/create_user.py list
   # Обновите ID в базе
   ```

2. **Протестировать бота:**
   - Отправьте /start
   - Проверьте роутинг (SuperAdmin/Admin/Master/Client)
   - Проверьте /master команду (для мастеров)
   - Проверьте /admin команду (для админов)

3. **Создать других пользователей:**
   ```bash
   python3 scripts/create_user.py admin --name "..." --phone "..." --telegram-id "..."
   python3 scripts/create_user.py master --name "..." --phone "..." --telegram-id "..."
   ```

**✅ Webhook настроен и готов к работе!**
