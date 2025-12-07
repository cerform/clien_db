# 🔐 Config - Конфигурация

Управление переменными окружения и конфигурацией приложения.

## 📋 Файлы

### `.env.example`
**Шаблон** переменных окружения.

✅ **В git** - все видят что требуется  
❌ **Не содержит** реальные ключи

### `.env`
**Реальные** переменные окружения для вашего окружения.

❌ **НЕ в git** - содержит секреты  
✅ **Локально** на компьютере и в Cloud Run

## 🚀 Первая настройка

### 1️⃣ Создать `.env` из шаблона
```bash
cp config/.env.example config/.env
```

### 2️⃣ Отредактировать значения
```bash
nano config/.env
# или
code config/.env
```

## 📝 Переменные окружения

### Telegram
```
TELEGRAM_BOT_TOKEN=123456:ABC...
```
- Получить у @BotFather в Telegram
- Формат: `123456:ABCdefGHIjklmnoPQRstuvwxyz`

### Google APIs
```
GOOGLE_SPREADSHEET_ID=17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ
GOOGLE_CREDENTIALS_JSON=credentials.json
GOOGLE_CALENDAR_ID=calendar_id@group.calendar.google.com
```

- **GOOGLE_SPREADSHEET_ID**: ID из URL таблицы
  ```
  https://docs.google.com/spreadsheets/d/{ID}/edit
                                        ↑
  ```
- **GOOGLE_CREDENTIALS_JSON**: Путь к файлу credentials.json
- **GOOGLE_CALENDAR_ID**: Получить командой:
  ```bash
  python scripts/get_calendar_id.py
  ```

### OpenAI
```
OPENAI_API_KEY=sk-proj-...
OPENAI_ASSISTANT_ID=asst_...
```

- **OPENAI_API_KEY**: Получить на https://platform.openai.com
- **OPENAI_ASSISTANT_ID**: ID ассистента в OpenAI

### Администраторы
```
ADMIN_IDS=123456789,987654321
```
- Telegram ID администраторов (через запятую)
- Получить свой ID: отправить /id боту

### Система
```
TIMEZONE=Asia/Jerusalem
LOG_LEVEL=INFO
```

- **TIMEZONE**: Часовой пояс (Europe/Moscow, Asia/Jerusalem, etc)
- **LOG_LEVEL**: INFO, DEBUG, WARNING, ERROR

## 🔐 Где получить ключи

### 🤖 Telegram Bot Token
1. Открыть Telegram
2. Написать @BotFather
3. Выполнить /newbot
4. Следовать инструкциям
5. Скопировать token

### 🔑 OpenAI API Key
1. Открыть https://platform.openai.com
2. Меню → API keys
3. Нажать "Create new secret key"
4. Скопировать ключ

### 📊 Google Sheets API
1. Google Cloud Console: https://console.cloud.google.com
2. Create Project → Tattoo Bot
3. Enable APIs:
   - Google Sheets API
   - Google Calendar API
4. Create Service Account
5. Create JSON key
6. Скачать credentials.json
7. Скопировать в проект

### 📅 Google Calendar ID
```bash
python scripts/get_calendar_id.py
```

---

## 📍 Расположение `.env`

### Локально (разработка)
```bash
config/.env
```

### Cloud Run (production)
Переменные задаются через:
1. **Dockerfile** (видит все)
2. **gcloud run deploy --update-env-vars** (переопределяет)
3. **Service secrets** (безопаснее для ключей)

---

## 🔄 Синхронизация между окружениями

### Локальное окружение → Cloud Run
```bash
# 1. Убедиться что .env полный
nano config/.env

# 2. Развернуть (автоматически используется .env)
gcloud run deploy telegram-bot --source .

# 3. Проверить что переменные установлены
gcloud run services describe telegram-bot
```

### Cloud Run → Локально (для тестирования)
```bash
# 1. Получить переменные из Cloud Run
gcloud run services describe telegram-bot --format json | jq '.spec.template.spec.containers[0].env'

# 2. Обновить локальный .env
```

---

## ✅ Проверка конфигурации

### Проверить что все переменные установлены
```bash
python -c "from src.config import get_config; c = get_config(); print(f'✅ Config loaded: {c}')"
```

### Проверить что .env загружается
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv('config/.env'); print(f'TELEGRAM_BOT_TOKEN: {os.getenv(\"TELEGRAM_BOT_TOKEN\", \"NOT SET\")}')"
```

### Полная предпроверка
```bash
python tests/pre_deploy_check.py
```

---

## 🐛 Решение проблем

### Проблема: "Config not found"
**Решение**: Убедиться что:
1. `.env` файл существует в `config/`
2. Запускаете из корня проекта

### Проблема: "Invalid API key"
**Решение**: Проверить:
1. OPENAI_API_KEY правильный
2. Нет пробелов в начале/конце
3. Ключ не истёк на OpenAI

### Проблема: "Google Sheets not found"
**Решение**: Проверить:
1. GOOGLE_SPREADSHEET_ID правильный
2. Service Account имеет доступ к таблице
3. Таблица не удалена

### Проблема: "Telegram webhook failed"
**Решение**: Проверить:
1. TELEGRAM_BOT_TOKEN правильный
2. Webhook URL правильный
3. HTTPS (не HTTP)

---

## 🔒 Безопасность

### ✅ DO's
- ✅ Сохраняйте `.env` в `config/`
- ✅ Добавьте `config/.env` в `.gitignore`
- ✅ Используйте `config/.env.example` в git
- ✅ Никогда не коммитьте реальные ключи
- ✅ Ротируйте ключи регулярно

### ❌ DON'Ts
- ❌ Не постите `.env` в Slack/Email
- ❌ Не коммитьте реальные ключи
- ❌ Не используйте одинаковые ключи везде
- ❌ Не сохраняйте ключи в истории shell
- ❌ Не передавайте credentials.json по сети

---

## 🔄 Ротация ключей

### Ежемесячно обновляйте:
```bash
# 1. OpenAI API Key
# На https://platform.openai.com - создать новый, удалить старый

# 2. Google Service Account Key
# На https://console.cloud.google.com - удалить старый JSON, создать новый

# 3. Telegram Bot Token
# В @BotFather - /revoke если компрометирован
```

---

**Статус**: ✅ Production Ready
