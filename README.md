# 🎨 Tattoo Appointment Bot

Complete Telegram bot for tattoo studio appointment booking with Google Sheets database and Google Calendar sync.

**Status:** ✅ Ready to deploy (need Google OAuth credentials)

---

## 🚀 Quick Start (10 minutes)

### Prerequisites
- Python 3.10+
- Telegram account
- Google account (for Sheets & Calendar)

### 1. Setup
```bash
cd tattoo_appointment_bot
bash bootstrap.sh
```

### 2. Get Tokens
- **Telegram:** [@BotFather](https://t.me/BotFather) → `/newbot` → copy token
- **Google:** [Follow GOOGLE_SETUP.md](./GOOGLE_SETUP.md)

### 3. Configure
```bash
cp .env.example .env
# Edit .env with:
# - BOT_TOKEN from @BotFather
# - ADMIN_USER_IDS (your Telegram ID)
# - Place credentials.json in project root
```

### 4. Initialize Database
```bash
python3 create_google_sheets_structure.py
# Copy SPREADSHEET_ID to .env
```

### 5. Run Bot
```bash
python3 run.py
```

## 🧩 Microservices local development

If you'd like to develop and debug the system in a microservices layout, we've added a scaffolding with a backend service, a Telegram bot service (webhook), an AI worker service and a small static frontend.

1) Copy the env example and update values:

```bash
cp .env.example .env
# Fill BOT_TOKEN, SPREADSHEET_ID, OPENAI_API_KEY as needed
```

2) Start the full stack locally using Docker Compose:

```bash
docker compose up --build
```

Services started:
- Backend API: http://localhost:8081
- Bot webhook: http://localhost:8082
- Frontend docs: http://localhost:8083

This setup is intended for local debugging: code is mounted to the containers so you can edit and test quickly. To test the webhook flow locally, you can use a tunneling service (like ngrok) to expose the bot URL and set webhook via `scripts/setup_webhook.sh` (or call `/api/setup-webhook` on the backend if needed).


---

## 🧩 Windows installer (experimental)

This repository includes a small Tkinter-based installer GUI that can be bundled into a Windows EXE using PyInstaller.
- Files are in `tools/win_installer/`.
- To build on Windows, use `python tools/win_installer/build_installer.py` or run the provided GitHub Actions workflow `build-windows-exe.yml`.

See `tools/win_installer/README.md` for details.

---

## ⚙️ Full setup (local development)

To quickly get a full development environment running (including a local Postgres used by admin messages), use the `setup` scripts:

1. Run the setup script:
```bash
bash setup/setup.sh
```
2. Follow the prompts to create a virtualenv, install requirements, start local PostgreSQL (optional), fill `.env` and optionally create Google Sheets structure.
3. Start the bot locally using polling:
```bash
python3 run.py
```

CLI env generator and Docker Dev/Prod
-----------------------------------
You can automate `.env` creation using `setup/configure_env.py` so you do not need manual editing:
```bash
python3 setup/configure_env.py --bot-token <token> --openai-key <key> --spreadsheet-id <id> --out .env --force
```

For development with Docker compose (includes web + Postgres):
```bash
docker compose -f setup/docker-compose.dev.yml up --build
```

For a simple production compose (web + postgres + nginx):
```bash
docker compose -f setup/docker-compose.prod.yml up --build -d
```

See `setup/README.md` for full details and optional Windows instructions.

⚠️ If this repository contains a `.env` file with real credentials, remove it from the repo and add your own `.env` values. Do not commit secrets to Git.

**✅ Bot is live!** Open Telegram and find your bot.

---

## 📋 Features

### 👥 Clients
- ✅ Browse available appointment slots
- ✅ Select master (tattoo artist)
- ✅ View today's appointments
- ✅ Google Calendar sync
- ✅ Full CRUD for clients, masters, bookings
- ✅ Dashboard with statistics
- ✅ Google Sheets (single spreadsheet, 4 tabs)
- ✅ Cloud SQL for admin messages storage
- ✅ Auto-schema creation
- ✅ Timezone support (Israel default)
- **Database:** Google Sheets API v4
- **Calendar:** Google Calendar API
- **Auth:** OAuth2 (auto-refresh)
- **Timezone:** Pytz (Israel/other locales)

---

## 📁 Structure

```
src/
├── config/          Config loader, constants
├── utils/           Logging, timezone, validation
├── db/              Google Sheets wrapper + repositories
├── services/        Business logic (booking, calendar, admin)
└── bot/             Aiogram handlers, keyboards, middlewares
```

---

## 🎯 Commands

### Client: `/start`, `/book`, `/bookings`
### Master: `/agenda`
### Admin: `/admin`

---

## 📖 Docs

- [SETUP.md](./SETUP.md) - Detailed setup guide
- [GOOGLE_SETUP.md](./GOOGLE_SETUP.md) - Google OAuth configuration
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) - System design
- [docs/GOOGLE_SHEETS_STRUCTURE.md](./docs/GOOGLE_SHEETS_STRUCTURE.md) - DB schema

---

## ⚙️ Configuration

### .env
```bash
BOT_TOKEN=your-token           # @BotFather
SPREADSHEET_ID=your-id         # create_google_sheets_structure.py
ADMIN_USER_IDS=12345,67890     # Your Telegram ID
DEFAULT_TIMEZONE=Asia/Jerusalem # Locale
ENV=development                 # or production
```

### credentials.json
- Download from [Google Cloud Console](https://console.cloud.google.com/)
- OAuth2 Desktop app
- See [GOOGLE_SETUP.md](./GOOGLE_SETUP.md)

---

## 🔄 Workflow

```
Client                  Bot                     Admin/Master
  |                      |                            |
  └─→ /book ────────────→ FSM flow ──────────────────→ Google Sheets
       (name/phone)       (date/master/slot)        (bookings tab)
                          |
                          └──→ Google Calendar (if master has calendar_id)
                          |
                    Send confirmation msg
                          ↓
         Booking created (status: pending)
```

---

## 📊 Database (Google Sheets)

Auto-created with 4 tabs:

| Tab | Purpose | Columns |
|-----|---------|---------|
| **clients** | User profiles | id, telegram_id, name, phone, email, notes, created_at |
| **masters** | Tattoo artists | id, name, calendar_id, specialties, active, created_at |
| **calendar** | Available slots | date, master_id, slot_start, slot_end, available, note |
| **bookings** | Appointments | id, client_id, master_id, date, slot_start, slot_end, status, created_at, google_event_id |

---

## 🚀 Deployment

### Local Development (Polling)
```bash
python3 run.py
```

### Google Cloud Run (Production)

**Автоматический деплой с Cloud SQL:**

```bash
./deploy_cloudrun.sh
```

Этот скрипт автоматически:
- ✅ Создаст Cloud SQL instance для admin_messages
- ✅ Соберет Docker образ и задеплоит на Cloud Run
- ✅ Настроит webhook для Telegram
- ✅ Подключит Cloud SQL через Unix socket

**После деплоя установите webhook:**
```bash
SERVICE_URL=$(gcloud run services describe tattoo-bot --region=us-central1 --format='value(status.url)')
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=${SERVICE_URL}/webhook/telegram"
```

**Просмотр логов:**
```bash
gcloud run logs read --service=tattoo-bot --region=us-central1 --limit=50
```

### Docker (Local)
```bash
docker build -t tattoo-bot .
docker run -e BOT_TOKEN=... -e SPREADSHEET_ID=... tattoo-bot
```

---

## 🐛 Troubleshooting

| Error | Fix |
|-------|-----|
| `BOT_TOKEN not set` | Add to .env from @BotFather |
| `SPREADSHEET_ID not set` | Run `create_google_sheets_structure.py` |
| `Credentials error` | Download fresh `credentials.json` from Google Cloud |
| `Permission denied` | Add bot to Telegram, check ADMIN_USER_IDS |

See [SETUP.md](./SETUP.md) for more.

---

## 📝 Code Examples

### Add a Client (in code)
```python
from src.services.client_service import ClientService
from src.db.sheets_client import SheetsClient
from src.config.env_loader import load_env
from src.config.config import Config

load_env()
cfg = Config.from_env()
sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
cs = ClientService(sc, cfg.SPREADSHEET_ID)
client = cs.register_client(telegram_id=12345, name="John", phone="+972501234567")
```

### Get Available Slots
```python
from src.services.booking_service import BookingService

bs = BookingService(sc, cfg.SPREADSHEET_ID)
slots = bs.list_available_slots(date="2025-12-10", master_id="master-uuid")
# Returns list of dicts: {date, master_id, slot_start, slot_end, available, note}
```

---

## 🔐 Security

- ✅ OAuth2 (no passwords)
- ✅ Input validation (phone, name, dates)
- ✅ Admin-only commands
- ✅ Error logging (no sensitive data)
- ✅ Token auto-refresh

---

## 📞 Support

1. **Setup issues?** → Read [SETUP.md](./SETUP.md)
2. **Google auth?** → Read [GOOGLE_SETUP.md](./GOOGLE_SETUP.md)
3. **Code questions?** → Check [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
4. **Errors?** → Check terminal output, look for `ERROR` or `Exception`

---

## 📜 License

Open source • Use freely • No warranty

---

## ✨ What's Next?

- [ ] Complete Google OAuth setup (see GOOGLE_SETUP.md)
- [ ] Add BOT_TOKEN to .env
- [ ] Run `python3 create_google_sheets_structure.py`

---

## 🗄️ Cloud SQL Integration

### Архитектура

Бот использует гибридную архитектуру хранения:
- **Google Sheets** - для основных данных (clients, masters, bookings, calendar)
- **Cloud SQL (MySQL)** - для admin_messages с AI классификацией

### Зачем Cloud SQL?

1. **Производительность** - быстрые запросы для больших объемов сообщений
2. **Индексы** - эффективный поиск по категориям, пользователям, датам
3. **Политика хранения** - автоматическое удаление старых сообщений (12 месяцев)
4. **PII Compliance** - возможность редактирования персональных данных
5. **Статистика** - агрегация данных без загрузки всего датасета

### Локальная разработка с Cloud SQL

```bash
# 1. Скачать Cloud SQL Proxy
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# 2. Запустить proxy
./cloud_sql_proxy -instances=tattoo-480007:us-central1:tattoo-bot-db=tcp:3306 &

# 3. Настроить переменные окружения
export CLOUDSQL_HOST=127.0.0.1
export CLOUDSQL_PORT=3306
export CLOUDSQL_USER=root
export CLOUDSQL_PASSWORD=your_password
export CLOUDSQL_DB=admin_messages

# 4. Инициализировать базу
python scripts/setup_database.py

# 5. (Опционально) Мигрировать данные из Google Sheets
python scripts/migrate_sheets_to_cloudsql.py
```

### Миграция на Cloud SQL

Для полной автоматической миграции используйте:

```bash
./scripts/cloudsql_migrate.sh
```

Этот скрипт:
1. Запускает Cloud SQL Proxy
2. Создает базу данных и таблицы
3. Мигрирует данные из Google Sheets
4. Останавливает proxy

### Структура таблицы admin_messages

```sql
CREATE TABLE admin_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp VARCHAR(32),
    user_id VARCHAR(32),
    username VARCHAR(64),
    message TEXT,
    category VARCHAR(64),
    data JSON,
    inka_category VARCHAR(64),
    sheet_row INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id),
    INDEX idx_category (category)
);
```

### Управление данными

```python
from src.db.cloudsql_client import get_cloudsql_client
from src.db.repositories.admin_messages_repo import AdminMessagesRepo

# Получить репозиторий
client = get_cloudsql_client()
repo = AdminMessagesRepo(client.get_engine())

# Получить сообщения пользователя
messages = repo.get_messages_by_user(user_id="12345", limit=50)

# Получить статистику по категориям
stats = repo.get_categories_stats()

# Удалить старые сообщения (старше 12 месяцев)
deleted = repo.delete_old_messages(months=12)

# Редактировать PII для пользователя
redacted = repo.redact_pii_by_user(user_id="12345")
```

### PII Политика

См. [PII_POLICY.md](PII_POLICY.md) для подробностей о:
- Сроках хранения данных (12 месяцев)
- Автоматическом редактировании персональных данных
- GDPR compliance
- Процедурах удаления данных

### Мониторинг Cloud SQL

```bash
# Подключиться к БД
gcloud sql connect tattoo-bot-db --user=root

# В MySQL консоли:
USE admin_messages;

# Статистика по категориям
SELECT category, COUNT(*) as count
FROM admin_messages
GROUP BY category
ORDER BY count DESC;

# Сообщения за последний месяц
SELECT COUNT(*)
FROM admin_messages
WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 MONTH);

# Размер таблицы
SELECT
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'admin_messages';
```
- [ ] Run `python3 run.py`
- [ ] Test `/start` in Telegram

**🎉 Ready? Start with:** `python3 run.py`
