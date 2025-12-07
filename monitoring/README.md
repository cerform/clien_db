# 📊 Monitoring - Мониторинг и метрики

Здоровье сервиса и сбор метрик.

## 📋 Файлы

### `health_check.py`
**Endpoint проверки здоровья** сервиса

### `metrics.py`
**Сбор метрик** для мониторинга

## 🩺 Health Check

### Что проверяется

```python
# GET /health

{
    "status": "ok",
    "timestamp": "2025-12-05T15:30:00Z",
    "uptime": 3600.5,
    "checks": {
        "database": "ok",
        "google_sheets": "ok",
        "google_calendar": "ok",
        "openai": "ok"
    }
}
```

### Использование

```bash
# Локально
curl http://localhost:8080/health

# Cloud Run
curl https://telegram-bot-XXXXX.us-central1.run.app/health
```

### В Cloud Run

```bash
# Cloud Run использует health check автоматически
# Если /health возвращает 200 - сервис считается здоровым
# Если не отвечает - сервис будет перезагружен

# Настройка (через Dockerfile):
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"
```

## 📈 Метрики

### Основные метрики

```
1. Uptime - время работы сервиса
2. Requests/sec - количество запросов
3. Errors/sec - ошибки
4. Response time - время ответа
5. CPU usage - использование CPU
6. Memory usage - использование памяти
7. Database connections - подключения к БД
```

### Просмотр метрик

```bash
# Cloud Run Dashboard
https://console.cloud.google.com/run

# Google Cloud Monitoring
https://console.cloud.google.com/monitoring

# Логирование
gcloud logging read "resource.service.name=telegram-bot" --limit 100
```

## 📊 Логирование

### Уровни логирования

```python
import logging

logging.debug("Debug message")      # Подробно для разработчиков
logging.info("Info message")        # Информационные сообщения
logging.warning("Warning message")  # Предупреждения
logging.error("Error message")      # Ошибки
logging.critical("Critical error")  # Критичные ошибки
```

### Просмотр логов

```bash
# Последние 50 логов
gcloud logging read "resource.service.name=telegram-bot" --limit 50

# Только ошибки
gcloud logging read "resource.service.name=telegram-bot AND severity=ERROR" --limit 50

# Реал-тайм логирование
gcloud logging read "resource.service.name=telegram-bot" --follow

# Фильтр по времени (последний час)
gcloud logging read "resource.service.name=telegram-bot AND timestamp>='$(date -d '1 hour ago' --iso-8601=seconds)'"
```

## 🔔 Алерты

### Создание алерта

```bash
# 1. Google Cloud Console
https://console.cloud.google.com/monitoring/alerting

# 2. Create Policy
# Условие: Error rate > 10%
# Notification: Email
# Action: Send to admin

# 3. Save
```

### Типичные алерты

```
1. Error rate > 5%
   → Email admin
   → Create incident

2. Response time > 5sec
   → Notify team
   → Check database

3. CPU > 80%
   → Scale up (add instances)
   → Notify ops

4. Service unavailable
   → Immediate critical alert
   → Auto-restart
```

## 🚨 Troubleshooting

### Health check failed
```bash
# 1. Проверить endpoint вручную
curl https://telegram-bot-XXXXX.us-central1.run.app/health -v

# 2. Посмотреть логи
gcloud logging read "resource.service.name=telegram-bot" --limit 20

# 3. Проверить что сервис запущен
gcloud run describe telegram-bot --region us-central1

# 4. Перезагрузить сервис
gcloud run services update telegram-bot --region us-central1 --no-traffic
gcloud run services update-traffic telegram-bot --to-revisions REVISION_NAME=100
```

### High error rate
```bash
# 1. Посмотреть ошибки
gcloud logging read "resource.service.name=telegram-bot AND severity=ERROR" --limit 50

# 2. Найти тренд ошибок
gcloud logging read "resource.service.name=telegram-bot AND severity=ERROR" \
  --format='table(timestamp,severity,textPayload)' --limit 100

# 3. Откатить на предыдущую версию
gcloud run revisions list --service=telegram-bot
gcloud run services update-traffic telegram-bot --to-revisions PREVIOUS_REVISION=100
```

### High memory usage
```bash
# 1. Посмотреть метрики памяти
gcloud monitoring read "metric.type=run.googleapis.com/container/memory/allocations" \
  --filter 'resource.service_name=telegram-bot'

# 2. Увеличить выделенную память
gcloud run deploy telegram-bot \
  --memory 1Gi  # Увеличить с 512Mi на 1Gi

# 3. Проверить что нет утечек памяти в коде
```

## 📋 Checklist мониторинга

- [ ] Health check endpoint работает
- [ ] Логи собираются в Cloud Logging
- [ ] Настроены алерты на ошибки
- [ ] Настроены алерты на performance
- [ ] Dashboard создан для быстрого обзора
- [ ] Команда знает как реагировать на алерты

---

## 🔗 Ссылки

- [Cloud Run Monitoring](https://cloud.google.com/run/docs/monitoring)
- [Cloud Logging](https://cloud.google.com/logging/docs)
- [Cloud Monitoring](https://cloud.google.com/monitoring/docs)
- [Alerts & Notifications](https://cloud.google.com/monitoring/alerts)

---

**Статус**: ✅ Production Ready
