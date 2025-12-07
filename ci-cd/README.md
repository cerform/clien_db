# 🐳 CI/CD - Непрерывная интеграция и развёртывание

Автоматизация тестирования и развёртывания.

## 📋 Файлы

### `cloudbuild.yaml`
**Google Cloud Build конфигурация** для автоматического deploy

## 🚀 Как это работает

### 1️⃣ Локально
```bash
# Вы пишете код
git add .
git commit -m "fix: something"
git push origin google-cloud-run
```

### 2️⃣ На GitHub
```
Push → Trigger Cloud Build
```

### 3️⃣ Cloud Build выполняет:
```yaml
# cloudbuild.yaml

steps:
  1. Собрать Docker образ
  2. Запустить тесты
  3. Push в Container Registry
  4. Deploy на Cloud Run
  5. Проверить здоровье
```

### 4️⃣ Результат:
```
✅ Новая версия live в production
```

## 📊 Pipeline

```
Code Push
    ↓
GitHub Webhook
    ↓
Google Cloud Build Trigger
    ↓
Запустить cloudbuild.yaml
    ├─ 1. Docker build
    ├─ 2. Run tests (pytest)
    ├─ 3. Push to Registry
    ├─ 4. Deploy to Cloud Run
    └─ 5. Health check
    ↓
Email Notification
    ↓
✅ Live in production
  или
❌ Failed - notification
```

## 🔧 Настройка CI/CD

### Первая настройка (одна раз)

```bash
# 1. Создать Cloud Build Trigger
# На https://console.cloud.google.com/cloud-build/triggers

# 2. Подключить GitHub repo
# Выбрать: owner/clien_db

# 3. Настроить trigger
# Ветка: google-cloud-run
# Конфигурация: Cloud Build (cloudbuild.yaml)

# 4. Сохранить
```

## 📝 Команды вручную

Если нужно запустить вручную:

```bash
# 1. Локальная сборка Docker образа
docker build -t telegram-bot:latest .

# 2. Запустить локально
docker run -p 8080:8080 \
  -e TELEGRAM_BOT_TOKEN=... \
  -e GOOGLE_SPREADSHEET_ID=... \
  telegram-bot:latest

# 3. Развернуть вручную
gcloud run deploy telegram-bot \
  --source . \
  --region us-central1 \
  --quiet
```

## 🔄 Workflow

### ✅ Успешный deploy
```
✅ Push на main
✅ Все тесты pass
✅ Docker build успешен
✅ Deploy на Cloud Run
✅ Health check pass
✅ Email: "Deployment successful"
✅ Новая версия live
```

### ❌ Неудачный deploy
```
❌ Push на main
❌ Тесты не pass (например, syntax error)
❌ Build отменен
❌ Email: "Build failed: Tests failed"
❌ Production не изменилась (safe!)
```

## 📊 Мониторинг deployments

```bash
# Смотреть все deployments
gcloud run revisions list --service=telegram-bot

# Смотреть логи последнего deploy
gcloud builds log --recent-first --limit=10

# Смотреть детали определённой версии
gcloud run describe telegram-bot --region us-central1
```

## 🔙 Откат версии

Если что-то пошло не так:

```bash
# 1. Список версий
gcloud run revisions list --service=telegram-bot

# 2. Откат на предыдущую версию
gcloud run services update-traffic telegram-bot \
  --to-revisions REVISION_NAME=100

# 3. Проверить
gcloud run describe telegram-bot

# 4. Посмотреть логи
gcloud logging read "resource.service.name=telegram-bot" --limit 50
```

---

## 🔐 Secrets

Для безопасного хранения API ключей используются **Google Secret Manager**:

```bash
# Создать secret
gcloud secrets create TELEGRAM_BOT_TOKEN \
  --replication-policy="automatic"

# Добавить значение
echo "123456:ABC..." | gcloud secrets versions add TELEGRAM_BOT_TOKEN --data-file=-

# Использовать в Cloud Run
gcloud run deploy telegram-bot \
  --update-secrets TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest

# Проверить в cloudbuild.yaml
# - name: 'gcr.io/cloud-builders/gke-deploy'
#   secretEnv: ['TELEGRAM_BOT_TOKEN']
```

---

## 📈 Метрики

```bash
# Просмотреть метрики deploy
gcloud monitoring read "metric.type=run.googleapis.com/request_count" \
  --filter 'resource.service_name=telegram-bot' \
  --format=json

# CPU usage
gcloud monitoring read "metric.type=run.googleapis.com/container/cpu/allocations" \
  --filter 'resource.service_name=telegram-bot'

# Memory usage
gcloud monitoring read "metric.type=run.googleapis.com/container/memory/allocations" \
  --filter 'resource.service_name=telegram-bot'
```

---

## 🐛 Решение проблем

### "Build failed: Tests failed"
```bash
# 1. Скачать логи
gcloud builds log $(gcloud builds list --limit=1 --format='value(ID)')

# 2. Исправить тесты локально
python -m pytest tests/ -v

# 3. Коммитить исправления
git commit -am "fix: test failures"
git push
```

### "Deployment stuck"
```bash
# 1. Проверить статус
gcloud builds list --limit=10

# 2. Отменить зависший build
gcloud builds cancel BUILD_ID

# 3. Запустить заново
git push -f  # или просто новый push
```

### "Health check failed"
```bash
# 1. Проверить endpoint
curl https://telegram-bot-XXXXX.us-central1.run.app/health

# 2. Посмотреть логи
gcloud logging read "resource.service.name=telegram-bot" --limit 50 | grep -i error

# 3. Откатиться на предыдущую версию (см. выше)
```

---

## 📚 Документация

- [Google Cloud Build Docs](https://cloud.google.com/build/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [GitHub Actions Integration](https://github.com/google-github-actions/deploy-cloud-run)

---

**Статус**: ✅ Production Ready
