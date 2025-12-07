# 🌐 Веб-Интерфейс Админ-Панели

## Обзор

Веб-интерфейс админ-панели работает на **одном Cloud Run сервисе** вместе с Telegram ботом:

```
Cloud Run Service (tattoo-bot)
├── /webhook/telegram          ← POST - Telegram webhook
├── /                           ← GET  - Главная страница админ-панели
├── /login                      ← GET  - Страница входа
├── /api/...                    ← REST API для управления БД
└── /docs                       ← Swagger UI документация
```

## 🏗️ Архитектура

### Single Service Architecture

**Преимущества:**
- ✅ Один сервис = одна плата
- ✅ Одна служба аккаунта для всех API
- ✅ Общие переменные окружения
- ✅ Общие логи и мониторинг

**Компоненты:**
- `main.py` - точка входа, запускает FastAPI + Telegram bot webhook
- `src/web/app.py` - создание FastAPI приложения
- `src/web/auth.py` - аутентификация администратора
- `src/web/api/routers.py` - REST API эндпоинты

## 🔒 Аутентификация

### Местная разработка
```bash
# Пароль по умолчанию
ADMIN_WEB_PASSWORD=admin123
```

### Production (Cloud Run)
```bash
# Установить в Cloud Run secrets
gcloud run services update tattoo-bot \
  --set-env-vars="ADMIN_WEB_PASSWORD=your_secure_password_here"
```

## 📡 REST API Эндпоинты

### Аутентификация
```http
POST /api/login
Content-Type: application/json

{
  "password": "admin123"
}

Response:
{
  "success": true,
  "token": "admin_token_123",
  "message": "Успешный вход"
}
```

### Статистика
```http
GET /api/stats

Response:
{
  "clients_count": 45,
  "masters_count": 5,
  "services_count": 12,
  "bookings_count": 78
}
```

### Мастера
```http
# Получить всех мастеров
GET /api/masters

# Создать нового мастера
POST /api/masters
Content-Type: application/json

{
  "name": "Иван Иванов",
  "specialization": "Татуировки",
  "experience_years": 5
}
```

### Услуги
```http
# Получить все услуги
GET /api/services

# Создать новую услугу
POST /api/services
Content-Type: application/json

{
  "name": "Татуировка (1 час)",
  "price": 5000,
  "duration_minutes": 60,
  "category": "tattoo"
}
```

### Клиенты
```http
GET /api/clients

Response:
[
  {
    "id": 1,
    "name": "Александр",
    "phone": "+7900123456",
    "email": "alex@example.com",
    "bookings_count": 3
  }
]
```

### Записи
```http
GET /api/bookings

Response:
[
  {
    "id": 1,
    "client_id": 1,
    "master_id": 2,
    "service_id": 3,
    "start_time": "2025-12-07T14:00:00",
    "end_time": "2025-12-07T15:00:00",
    "status": "confirmed"
  }
]
```

### INKA Обучение
```http
# Получить статистику обучения
GET /api/inka-training-stats

Response:
{
  "total_sessions": 15,
  "successful_trainings": 14,
  "average_score": 0.92
}

# Обучить ИНКУ
POST /api/inka-training
Content-Type: application/json

{
  "text": "Это информация для обучения ассистента"
}

Response:
{
  "success": true,
  "message": "Training started"
}
```

### Здоровье
```http
GET /api/health

Response:
{
  "status": "ok",
  "service": "tattoo-bot-admin"
}
```

## 🌐 Веб-Интерфейс

### Главная страница
```
URL: https://tattoo-bot.com/
```

Содержит:
- 📊 Карточки со статистикой (клиенты, мастера, услуги, записи)
- 📋 Меню управления:
  - 👥 Мастера
  - 💼 Услуги
  - 👤 Клиенты
  - 📅 Записи
  - 🧠 Обучение ИНКИ
  - 📈 Аналитика

### Страница входа
```
URL: https://tattoo-bot.com/login
```

Требует пароль администратора.

### Swagger UI
```
URL: https://tattoo-bot.com/docs
```

Интерактивная документация всех API эндпоинтов.

## 🚀 Развертывание на Cloud Run

### Создание сервиса
```bash
# 1. Собрать образ
docker build -t gcr.io/tattoo-480007/tattoo-bot:latest .

# 2. Загрузить на Google Container Registry
docker push gcr.io/tattoo-480007/tattoo-bot:latest

# 3. Развернуть на Cloud Run
gcloud run deploy tattoo-bot \
  --image gcr.io/tattoo-480007/tattoo-bot:latest \
  --region us-central1 \
  --service-account tattoo-bot-sa@tattoo-480007.iam.gserviceaccount.com \
  --set-env-vars=\
"PORT=8080,\
HOST=0.0.0.0,\
WEBHOOK_URL=https://tattoo-bot-xxxxx.run.app,\
ADMIN_WEB_PASSWORD=your_password,\
TELEGRAM_BOT_TOKEN=your_token,\
GOOGLE_SPREADSHEET_ID=xxx,\
GOOGLE_CALENDAR_ID=google@tattoo.me,\
ADMIN_IDS=438407739,\
OPENAI_API_KEY=sk-xxx,\
TIMEZONE=Europe/Moscow" \
  --timeout 3600 \
  --memory 512Mi \
  --cpu 1
```

### Обновить webhook URL в Telegram
```bash
# Сначала узнайте URL сервиса
gcloud run services describe tattoo-bot --region us-central1

# Затем установите webhook через Telegram API
curl -X POST https://api.telegram.org/botYOUR_TOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://tattoo-bot-xxxxx.run.app/webhook/telegram",
    "drop_pending_updates": false
  }'
```

## 🔧 Локальная разработка

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск локально
```bash
# Установить переменные окружения
export ADMIN_WEB_PASSWORD=admin123
export TELEGRAM_BOT_TOKEN=your_token
export GOOGLE_SPREADSHEET_ID=your_id
# ... и другие переменные

# Запустить сервер
python3 -m src.main
```

Откроется веб-интерфейс на http://localhost:8080

### Тестирование API
```bash
# Получить список мастеров
curl http://localhost:8080/api/masters

# Получить статистику
curl http://localhost:8080/api/stats

# Вход
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"password": "admin123"}'
```

## 📊 Мониторинг

### Просмотр логов
```bash
# Все логи
gcloud run services logs read tattoo-bot

# Логи за последние 5 минут
gcloud run services logs read tattoo-bot --limit 100

# Логи в реальном времени
gcloud run services logs read tattoo-bot --tail
```

### Метрики
```bash
# Память
gcloud run services describe tattoo-bot --region us-central1

# Список ревизий
gcloud run revisions list --service tattoo-bot --region us-central1
```

## 🔐 Безопасность

### Best Practices
1. ✅ Использовать `HTTPS` в production
2. ✅ Менять пароль администратора
3. ✅ Включить CORS только для известных доменов
4. ✅ Логировать все действия администратора
5. ✅ Использовать JWT токены для API (не реализовано в базовой версии)

### Добавить JWT аутентификацию (опционально)
```python
# Установить пакет
pip install python-jose[cryptography] passlib[bcrypt]

# Использовать в api/routers.py для защиты эндпоинтов
```

## 🐛 Troubleshooting

### Проблема: "Connection refused" на localhost
```bash
# Проверить, запущен ли сервер
ps aux | grep uvicorn

# Проверить порт
lsof -i :8080
```

### Проблема: "Database manager not initialized"
```bash
# Убедиться, что переменные окружения установлены
echo $GOOGLE_SPREADSHEET_ID
echo $TELEGRAM_BOT_TOKEN
```

### Проблема: Webhook не работает
```bash
# Проверить URL вебхука
curl https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo

# Пересоздать вебхук
curl -X POST https://api.telegram.org/botYOUR_TOKEN/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.run.app/webhook/telegram"}'
```

## 📚 Дополнительные ресурсы

- [FastAPI документация](https://fastapi.tiangolo.com/)
- [Uvicorn документация](https://www.uvicorn.org/)
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
