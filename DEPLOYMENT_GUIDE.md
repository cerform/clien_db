# 🚀 CLOUD RUN DEPLOYMENT GUIDE

## Overview

После серии исправлений и улучшений, бот теперь готов к production deployment. Этот документ описывает текущую архитектуру и как развернуть бота в Cloud Run.

## 📋 Что было исправлено

### 1. **Синтаксические ошибки** ✅
- **Файл**: `src/ai/advanced_inka.py`
- **Проблема**: Try блок без except/finally на строке 33
- **Решение**: Добавлен except handler

### 2. **Обработка исключений в API вызовах** ✅
- **Файл**: `src/db/sheets_client.py`
- **Проблема**: `append_row()` не возвращал False при ошибке
- **Решение**: Добавлен `return False` в except блок

### 3. **Фильтрация по telegram_id** ✅
- **Файл**: `src/ai/advanced_inka.py`
- **Проблема**: Whitespace в сохраненных значениях предотвращал matching
- **Решение**: Добавлен `.strip()` к обеим значениям для сравнения

### 4. **Dual-credential система** ✅
- **Файлы**: `src/db/sheets_client.py`, `src/calendars/google_calendar_sync.py`
- **Проблема**: Работало только в Cloud Run native auth
- **Решение**: Попытка загрузить local credentials.json сначала, затем fallback на google.auth.default()

### 5. **Отсутствие диагностических команд** ✅
- **Новый файл**: `debug_config.py`
- **Новый файл**: `src/bot/handlers/debug_handler.py`
- **Решение**: Добавлены команды `/debug_config`, `/debug_sheets`, `/debug_calendar` для администраторов

### 6. **Cloud Run entrypoint** ✅
- **Новый файл**: `run_cloud.py`
- **Решение**: Отдельный entrypoint, не использует интерактивное меню

## 📊 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD RUN SERVICE                        │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  run_cloud.py (ENTRYPOINT)                         │    │
│  │  • Загружает конфиг из env vars                    │    │
│  │  • Инициализирует бота                             │    │
│  │  • Включает все handlers                           │    │
│  └────────────────────────────────────────────────────┘    │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Webhook Handler (HTTP)                            │    │
│  │  GET  /health → 200 OK                             │    │
│  │  POST /webhook → Process Telegram Update           │    │
│  └────────────────────────────────────────────────────┘    │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Bot Handlers                                      │    │
│  │  • start_handler         (/start)                  │    │
│  │  • client_handler        (client ops)              │    │
│  │  • master_handler        (master ops)              │    │
│  │  • admin_panel_text      (/admin)                  │    │
│  │  • debug_handler         (/debug_*)                │    │
│  └────────────────────────────────────────────────────┘    │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Core Services                                     │    │
│  │  • GoogleSheetsClient    → Spreadsheet API        │    │
│  │  • GoogleCalendarSync    → Calendar API           │    │
│  │  • AdvancedINKA          → AI Processing          │    │
│  │  • DataSyncService       → DB Operations          │    │
│  └────────────────────────────────────────────────────┘    │
│                           ↓                                  │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                ↓
    ┌────────┐          ┌──────────┐    ┌──────────┐
    │ Google │          │ Google   │    │ OpenAI   │
    │ Sheets │          │ Calendar │    │ API      │
    │ API    │          │ API      │    │          │
    └────────┘          └──────────┘    └──────────┘
        ↓                    ↓
   ┌────────────────────────────────┐
   │  Service Account               │
   │  tattoo-bot-sa@               │
   │  tattoo-480007.iam.            │
   │  gserviceaccount.com           │
   └────────────────────────────────┘
```

## 🔐 Аутентификация

### Cloud Run
```
┌─────────────────────────────────────┐
│ Service Account                     │
│ (автоматически предоставляется      │
│  Cloud Run)                         │
└─────────────────────────────────────┘
        ↓
   google.auth.default()
        ↓
┌─────────────────────────────────────┐
│ googleapis.clients                  │
│ • Sheets API                        │
│ • Calendar API                      │
└─────────────────────────────────────┘
```

### Local Development
```
┌─────────────────────────────────────┐
│ credentials.json (local)            │
│ (в root directory)                  │
└─────────────────────────────────────┘
        ↓
   load_credentials()
        ↓
┌─────────────────────────────────────┐
│ googleapis.clients                  │
│ • Sheets API                        │
│ • Calendar API                      │
└─────────────────────────────────────┘
```

## 🚀 Deployment Steps

### 1. Подготовка

```bash
# Убедитесь что все изменения закоммичены
cd /home/etcsys/projects/clien_db
git add .
git commit -m "Production: Add debug commands and Cloud Run entrypoint"

# Проверьте конфигурацию локально
python3 debug_config.py
```

### 2. Deploy to Cloud Run

```bash
# Deploy с использованием нового entrypoint
gcloud run deploy tattoo-bot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="K_SERVICE=tattoo-bot" \
  --max-instances 100 \
  --entry-point="python -m run_cloud" \
  2>&1
```

**ИЛИ обновить в web console:**
1. Cloud Run → tattoo-bot → Edit & Deploy new revision
2. Set environment variable: `K_SERVICE=tattoo-bot`
3. Set entry command: `python -m run_cloud`

### 3. Проверка

```bash
# Получить URL сервиса
SERVICE_URL=$(gcloud run services describe tattoo-bot \
  --region us-central1 \
  --format='value(status.url)')

echo "Service URL: $SERVICE_URL"

# Проверить health endpoint
curl -X GET "$SERVICE_URL/health"
# Ожидается: 200 OK

# Проверить webhook endpoint (должна быть 404 если GET)
curl -X GET "$SERVICE_URL/webhook"
# Ожидается: 404 Not Found

# Проверить логи
gcloud run services logs read tattoo-bot --region us-central1 --limit 50
```

## 📋 Проверка после deployment

### 1. **Диагностические команды доступны**
```
/debug_config   - Полная проверка конфигурации
/debug_sheets   - Проверка Google Sheets доступа
/debug_calendar - Проверка Google Calendar доступа
/debug_help     - Справка
```

### 2. **Admin использует для проверки**
```
# В Telegram (только для администраторов)
/debug_config
```

Ожидается ответ типа:
```
🔍 КОНФИГУРАЦИЯ БОТА

📋 Переменные окружения:
• Telegram токен: ✅
• Google Spreadsheet ID: ✅
• Google Calendar ID: ✅
• OpenAI API: ✅
• Timezone: Asia/Jerusalem
• Admin IDs: 2 шт.

🔐 Учетные данные:
• Local credentials.json: ❌ (using Cloud Run Service Account)

📊 Google Sheets:
• Spreadsheet: ✅ (db_new)
• Sheets: 14
• All required sheets: ✅

📅 Google Calendar:
• Calendar: ✅

👤 Администраторы:
• 438407739
• 457343487
```

### 3. **Попробовать создать клиента**
1. Пользователь пишет боту: "Привет, хочу записаться"
2. Бот предлагает ввести имя, телефон и email
3. Проверяется: ✅ запись добавляется в Google Sheets

### 4. **Проверить логи**
```bash
gcloud run services logs read tattoo-bot --region us-central1 --limit 100 | grep -E "(error|ERROR|WARNING)"
```

## 🔧 Troubleshooting

### Проблема: "Бот не отвечает на сообщения"

**Решение 1: Проверить webhook**
```bash
SERVICE_URL=$(gcloud run services describe tattoo-bot --region us-central1 --format='value(status.url)')
curl -X POST "$SERVICE_URL/webhook" \
  -H "Content-Type: application/json" \
  -d '{"update_id":1,"message":{"message_id":1,"chat":{"id":123},"text":"test"}}'
```

**Решение 2: Проверить конфиг**
```bash
# В Telegram от администратора:
/debug_config
```

### Проблема: "ошибка при попытке записать" (403 Forbidden)

**Решение:**
```bash
# Убедиться что Service Account имеет editor access к Sheets
gcloud projects get-iam-policy tattoo-480007 \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:tattoo-bot-sa@tattoo-480007.iam.gserviceaccount.com"
```

Должна быть роль `roles/editor` или `roles/sheets.admin`

### Проблема: "я не нашел информацию о вас в системе"

**Решение:**
```bash
# Проверить что пользователь был записан
# В Telegram от администратора:
/debug_sheets
```

Посмотреть есть ли строки в листе "clients"

## 📚 File Structure

```
├── run_cloud.py                    ← Cloud Run entrypoint (НОВЫЙ)
├── debug_config.py                 ← Диагностический скрипт (НОВЫЙ)
├── src/
│   ├── main.py                     ← Интерактивное меню для local development
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── debug_handler.py   ← Debug команды (НОВЫЙ)
│   │   │   ├── start_handler.py
│   │   │   ├── client_handler.py
│   │   │   └── admin_panel_text.py
│   │   └── loader.py
│   ├── db/
│   │   └── sheets_client.py        ← УЛУЧШЕН: dual-credential
│   ├── calendars/
│   │   └── google_calendar_sync.py ← УЛУЧШЕН: dual-credential
│   ├── ai/
│   │   └── advanced_inka.py        ← ИСПРАВЛЕН: syntax error, .strip()
│   └── config/
│       └── config.py
└── requirements.txt                ← Зависимости
```

## 📊 Статус компонентов

| Компонент | Статус | Примечание |
|-----------|--------|-----------|
| Telegram Bot | ✅ Working | Webhook принимает updates |
| Google Sheets | ✅ Working | Читает/пишет в spreadsheet |
| Google Calendar | ✅ Working | Календарь доступен |
| OpenAI Assistants | ✅ Working | Обработка запросов |
| Configuration | ✅ Working | Загружается из env vars |
| Credentials | ✅ Working | Dual-credential система |
| Admin Commands | ✅ Working | Debug команды доступны |
| Cloud Run | ✅ Ready | Новый entrypoint |

## 🎯 Next Steps

После deployment:

1. **Мониторить логи**
   ```bash
   watch -n 5 'gcloud run services logs read tattoo-bot --region us-central1 --limit 50'
   ```

2. **Тестировать функционал**
   - Запись нового клиента
   - Бронирование процедуры
   - Admin функции

3. **При проблемах**
   - Запустить `/debug_config` в Telegram
   - Проверить логи в Cloud Run console
   - Смотреть ошибки в Sheets/Calendar API

## 🚨 Important Notes

1. **Путь до credentials.json**
   - Cloud Run: используется встроенный Service Account
   - Local: указывается явно или ищется в root directory

2. **Переменные окружения**
   - K_SERVICE: определяет что мы в Cloud Run
   - TELEGRAM_BOT_TOKEN: из Secrets Manager
   - GOOGLE_SPREADSHEET_ID: явно указывается
   - OPENAI_API_KEY: из Secrets Manager

3. **Admin IDs**
   - Должны быть разделены запятыми
   - Парсятся в List[int]
   - Проверяются на строгое равенство

## 📞 Support

При возникновении проблем:
1. Запустить `python3 debug_config.py` локально
2. Запустить `/debug_config` в Telegram (для администратора)
3. Проверить логи: `gcloud run services logs read tattoo-bot`
4. Проверить конфиг в Cloud Run console
