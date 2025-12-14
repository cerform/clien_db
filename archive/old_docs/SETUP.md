# 🎨 Tattoo Appointment Bot - Setup Guide

## ✅ Quick Start (5 minutes)

### 1. Install Dependencies
```bash
cd tattoo_appointment_bot
bash bootstrap.sh
```

### 2. Get Telegram Bot Token
1. Open Telegram, find **@BotFather**
2. Send `/newbot`
3. Follow instructions, get your token
4. Edit `.env` and set `BOT_TOKEN=YOUR_TOKEN_HERE`

### 3. Get Google OAuth2 Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable APIs:
   - Google Sheets API
   - Google Calendar API
4. Create OAuth2 Desktop App credentials
5. Download JSON file → save as `credentials.json` in project root

### 4. Create Google Spreadsheet
```bash
python3 create_google_sheets_structure.py
```
This will open browser for OAuth and create spreadsheet automatically.
Copy the Spreadsheet ID and add to `.env`:
```
SPREADSHEET_ID=your-spreadsheet-id-here
```

### 5. Set Admin Telegram ID
Get your Telegram ID and add to `.env`:
```
ADMIN_USER_IDS=YOUR_ID_HERE
```

### 6. Run Bot
```bash
python3 run.py
```

Bot starts in polling mode (long polling). Ready! 🚀

---

## 📁 Project Structure

```
tattoo_appointment_bot/
├── run.py                          # Bot entrypoint
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .env                            # Your config (create from .env.example)
├── credentials.json                # Google OAuth (create from Google Console)
│
├── src/
│   ├── config/
│   │   ├── env_loader.py          # Load .env variables
│   │   ├── config.py              # Config dataclass
│   │   └── constants.py           # App constants
│   │
│   ├── utils/
│   │   ├── logging_setup.py       # Logging configuration
│   │   ├── time_utils.py          # Date/time helpers
│   │   └── validation.py          # Input validation
│   │
│   ├── db/
│   │   ├── sheets_client.py       # Google Sheets API wrapper
│   │   └── repositories/          # Data access layer
│   │       ├── clients_repo.py
│   │       ├── masters_repo.py
│   │       ├── calendar_repo.py
│   │       └── bookings_repo.py
│   │
│   ├── services/
│   │   ├── booking_service.py     # Booking logic
│   │   ├── client_service.py      # Client logic
│   │   ├── master_service.py      # Master logic
│   │   ├── admin_service.py       # Admin logic
│   │   ├── calendar_service.py    # Google Calendar sync
│   │   └── webhook.py             # FastAPI webhook (optional)
│   │
│   └── bot/
│       ├── entrypoint.py          # Bot startup
│       ├── router.py              # Handler registration
│       ├── handlers/              # Message/callback handlers
│       │   ├── client_handlers.py
│       │   ├── master_handlers.py
│       │   └── admin_handlers.py
│       ├── keyboards/             # Reply markup builders
│       │   ├── common_kb.py
│       │   ├── client_kb.py
│       │   └── admin_kb.py
│       └── middlewares/
│           └── timezone_middleware.py
│
└── docs/
    ├── ARCHITECTURE.md            # Architecture overview
    ├── INSTALLATION_NOTES.md      # Detailed setup
    └── GOOGLE_SHEETS_STRUCTURE.md # Database schema
```

---

## 🤖 Bot Commands

### Client Commands
- `/start` - Welcome & menu
- `/book` - Start booking flow
- `/bookings` - View my bookings
- `/help` - Help

### Master Commands  
- `/agenda` - Today's bookings
- `/calendar` - Google Calendar view (optional)

### Admin Commands
- `/admin` - Admin dashboard
- `/clients` - List clients
- `/masters` - List masters
- `/bookings` - List bookings

---

## 🗄️ Google Sheets Schema

Automatic created with 4 sheets:

### clients
| id | telegram_id | name | phone | email | notes | created_at |
|-------|-------|-------|-------|-------|-------|---------|
| UUID | 12345 | John | +972501234567 | john@example.com | Sleeve tattoo | 2025-12-03T... |

### masters
| id | name | calendar_id | specialties | active | created_at |
|---|---|---|---|---|---|
| UUID | David | calendar_id@google.com | Tribal, Geometric | yes | 2025-12-03T... |

### calendar
| date | master_id | slot_start | slot_end | available | note |
|---|---|---|---|---|---|
| 2025-12-10 | UUID | 10:00 | 11:00 | yes | Regular slot |

### bookings
| id | client_id | master_id | date | slot_start | slot_end | status | created_at | google_event_id |
|---|---|---|---|---|---|---|---|---|
| UUID | UUID | UUID | 2025-12-10 | 10:00 | 11:00 | pending | 2025-12-03T... | event_id@... |

---

## 🔧 Configuration (.env)

```bash
# Telegram Bot
BOT_TOKEN=your-telegram-bot-token-here
USE_WEBHOOK=false
WEBHOOK_URL=https://your-domain.com/bot/webhook
PORT=8080

# Google API
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
SPREADSHEET_ID=your-spreadsheet-id-here

# Timezone (default: Israel)
DEFAULT_TIMEZONE=Asia/Jerusalem

# Admin IDs (comma-separated Telegram user IDs)
ADMIN_USER_IDS=123456789,987654321

# Environment
ENV=development  # or production
```

---

## 🚀 Deployment

### Local Testing
```bash
python3 run.py
```

### Production with Webhook (Optional)
```bash
# Requires valid HTTPS domain
USE_WEBHOOK=true
WEBHOOK_URL=https://your-domain.com/bot/webhook
python3 run.py
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "run.py"]
```

---

## 🐛 Troubleshooting

### "BOT_TOKEN not set"
- Check .env file exists
- Make sure BOT_TOKEN has your actual token from @BotFather

### "SPREADSHEET_ID not set"
- Run: `python3 create_google_sheets_structure.py`
- Copy ID to .env

### "OAuth credentials not found"
- Create `credentials.json` from Google Cloud Console
- Make sure it's in project root

### "Permission denied"
- Add bot to your Telegram (open @YourBotName)
- Check admin ID in .env

### No Masters showing
- Add masters to Google Sheets manually
- Or extend admin handlers with `/add_master` command

---

## 📞 Support

1. Check logs: `grep ERROR` in terminal output
2. Verify .env configuration
3. Ensure Google credentials are valid (may need refresh)
4. Check Telegram bot permissions

---

## ✨ Features

✅ Client booking flow (name → phone → date → master → slot → confirm)
✅ Google Sheets database
✅ Google Calendar sync (per master)
✅ Admin dashboard
✅ Booking status tracking
✅ Timezone support (Israel default)
✅ Input validation
✅ Error handling & logging

---

## 🔄 Next Steps

1. ✅ Setup complete
2. Add test bookings via bot
3. Configure masters' Google Calendar IDs
4. Setup notifications (optional)
5. Deploy to production

**Ready? Start with:** `python3 run.py`
