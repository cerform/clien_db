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

**✅ Bot is live!** Open Telegram and find your bot.

---

## 📋 Features

### 👥 Clients
- ✅ Browse available appointment slots
- ✅ Select master (tattoo artist)
- ✅ Choose date & time
- ✅ View/cancel bookings
- ✅ Phone validation

### 👨‍🎨 Masters
- ✅ View today's appointments
- ✅ Google Calendar sync
- ✅ Block unavailable times
- ✅ Real-time availability

### 🔧 Admin
- ✅ Full CRUD for clients, masters, bookings
- ✅ Dashboard with statistics
- ✅ Manual booking override
- ✅ Status management (pending/confirmed/cancelled)

### 🗄️ Database
- ✅ Google Sheets (single spreadsheet, 4 tabs)
- ✅ Auto-schema creation
- ✅ Timezone support (Israel default)
- ✅ Structured data (no messy spreadsheets)

### 📱 Tech Stack
- **Bot:** Aiogram 3.13 (async Telegram)
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

### Local (Polling)
```bash
python3 run.py
```

### Production (Webhook)
```bash
USE_WEBHOOK=true
WEBHOOK_URL=https://your-domain.com/bot/webhook
python3 run.py
```

### Docker
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
- [ ] Run `python3 run.py`
- [ ] Test `/start` in Telegram

**🎉 Ready? Start with:** `python3 run.py`
