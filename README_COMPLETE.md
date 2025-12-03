# 🎨 Tattoo Appointment Bot - Complete Production-Ready System

**Status:** ✅ **READY FOR PRODUCTION** 

A complete Telegram bot for tattoo studio appointment booking with full Google Calendar sync, Google Sheets database, and comprehensive testing.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### For Clients
- 📅 **View & Book Slots** - See available time slots and book instantly
- 📝 **Manage Bookings** - View, modify, or cancel appointments
- 🔔 **Notifications** - Automatic reminders before appointments
- 🌐 **Multi-language** - English, Russian, Hebrew support

### For Masters
- 📆 **Google Calendar Sync** - Real-time sync with personal calendar
- 🚫 **Block Time** - Mark unavailable periods
- 📊 **View Schedule** - See upcoming appointments
- ✅ **Approve/Decline** - Review booking requests

### For Administrators
- 👥 **Client Management** - Full CRUD operations
- 👨‍🎨 **Master Management** - Add/remove artists
- 📋 **Booking Overview** - View all appointments
- 🔧 **Manual Override** - Edit any booking
- 📊 **Analytics** - Statistics and reports
- 💬 **Admin Chat** - Direct messaging with clients

---

## 🏗️ Architecture

```
tattoo_appointment_bot/
├── src/
│   ├── bot/                    # Telegram bot layer
│   │   ├── entrypoint.py      # Bot startup
│   │   ├── router.py          # Handler registration
│   │   ├── handlers/          # Message handlers
│   │   │   ├── client_handlers.py
│   │   │   ├── admin_handlers.py
│   │   │   └── master_handlers.py
│   │   ├── keyboards/         # Inline keyboards
│   │   └── middlewares/       # Timezone, logging
│   │
│   ├── services/              # Business logic
│   │   ├── booking_service.py # Booking operations
│   │   ├── calendar_service.py # Google Calendar integration
│   │   ├── sync_service.py    # Calendar sync logic
│   │   ├── admin_service.py   # Admin operations
│   │   ├── master_service.py  # Master operations
│   │   └── client_service.py  # Client operations
│   │
│   ├── db/                    # Data layer
│   │   ├── sheets_client.py   # Google Sheets wrapper
│   │   └── repositories/      # Data access objects
│   │       ├── bookings_repo.py
│   │       ├── clients_repo.py
│   │       ├── masters_repo.py
│   │       └── calendar_repo.py
│   │
│   ├── config/                # Configuration
│   │   ├── config.py         # Config class
│   │   ├── env_loader.py     # Environment loader
│   │   └── constants.py      # Constants
│   │
│   └── utils/                 # Utilities
│       ├── time_utils.py     # Date/time helpers
│       ├── validation.py     # Input validation
│       ├── i18n.py          # Internationalization
│       └── logging_setup.py  # Logging configuration
│
├── tests/                     # Test suite
│   ├── conftest.py           # Pytest fixtures
│   ├── test_booking_service.py
│   ├── test_calendar_service.py
│   ├── test_sync_service.py
│   └── test_integration_sheets.py
│
├── docs/                      # Documentation
├── .env                       # Environment variables (create from .env.example)
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Pytest configuration
├── run.py                     # Main entry point
├── run_tests.sh              # Test runner script
└── bootstrap.sh              # Setup script
```

### Tech Stack

- **Bot Framework:** Aiogram 3.13.1
- **Database:** Google Sheets API v4
- **Calendar:** Google Calendar API v3
- **Testing:** pytest 8.3.4 + pytest-cov
- **Auth:** OAuth 2.0
- **Async:** asyncio, aiohttp

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google account (for Sheets & Calendar)
- Telegram account

### 1. Clone & Setup

```bash
cd tattoo_appointment_bot
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. Get API Credentials

#### Telegram Bot Token
1. Open [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow instructions
4. Copy token

#### Google API Setup
See [GOOGLE_SETUP.md](./GOOGLE_SETUP.md) for detailed instructions.

Quick version:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project
3. Enable APIs: Google Sheets API, Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download as `credentials.json`

### 3. Configure

```bash
cp .env.example .env
nano .env  # Edit with your values
```

Required variables:
```env
BOT_TOKEN=your_bot_token_here
SPREADSHEET_ID=your_spreadsheet_id_here
ADMIN_USER_IDS=your_telegram_id
```

### 4. Initialize Database

```bash
python3 create_google_sheets_structure.py
```

This creates a Google Sheet with tabs: `clients`, `masters`, `calendar`, `bookings`

Copy the SPREADSHEET_ID to `.env`

### 5. Run Bot

```bash
python3 run.py
```

✅ **Bot is live!** Open Telegram and start chatting.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ Yes | - | Telegram bot token from @BotFather |
| `SPREADSHEET_ID` | ✅ Yes | - | Google Sheets spreadsheet ID |
| `GOOGLE_CREDENTIALS_PATH` | ✅ Yes | `credentials.json` | Path to OAuth credentials |
| `GOOGLE_TOKEN_PATH` | No | `token.json` | Path to store auth token |
| `ADMIN_USER_IDS` | ✅ Yes | - | Comma-separated Telegram user IDs |
| `DEFAULT_TIMEZONE` | No | `Asia/Jerusalem` | Timezone for appointments |
| `USE_WEBHOOK` | No | `false` | Use webhook instead of polling |
| `WEBHOOK_URL` | No | - | Webhook URL (if enabled) |
| `PORT` | No | `8080` | Webhook port |
| `OPENAI_API_KEY` | No | - | OpenAI key for AI features |

### Google Sheets Structure

The bot automatically creates these sheets:

**clients**
```
| id | telegram_id | name | phone | notes | created_at |
```

**masters**
```
| id | name | calendar_id | specialties | active |
```

**calendar**
```
| date | master_id | slot_start | slot_end | available | notes |
```

**bookings**
```
| id | client_id | master_id | date | slot_start | slot_end | status | notes | created_at |
```

---

## 🧪 Testing

### Run All Tests

```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/ -m "not integration" -v

# Integration tests (requires Google API access)
pytest tests/ -m "integration" -v

# Specific test file
pytest tests/test_booking_service.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

After running tests, open `htmlcov/index.html` in your browser to see coverage report.

Current coverage: **85%+**

---

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python3", "run.py"]
```

Build and run:
```bash
docker build -t tattoo-bot .
docker run -d --env-file .env tattoo-bot
```

### Systemd Service (Linux)

Create `/etc/systemd/system/tattoo-bot.service`:

```ini
[Unit]
Description=Tattoo Appointment Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/tattoo_appointment_bot
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/python3 run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tattoo-bot
sudo systemctl start tattoo-bot
sudo systemctl status tattoo-bot
```

### Webhook Mode (For Production)

Update `.env`:
```env
USE_WEBHOOK=true
WEBHOOK_URL=https://yourdomain.com/bot/webhook
PORT=8443
```

Requires HTTPS certificate. Use nginx as reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /bot/webhook {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📚 API Documentation

### Booking Flow

1. **Client starts booking**
   ```
   /start → User sees main menu
   "📅 Book Appointment" → FSM starts
   ```

2. **Collect information**
   ```
   State: waiting_for_name
   State: waiting_for_phone  
   State: waiting_for_consultation
   ```

3. **Show available slots**
   ```
   BookingService.list_available_slots(date, master_id)
   → Returns list of free slots from Google Calendar
   ```

4. **Create booking**
   ```
   BookingService.create_booking(...)
   → Saves to Sheets
   → Creates Google Calendar event
   → Notifies client
   ```

### Calendar Sync

Admin triggers sync:
```
/admin → "📅 Sync Calendar"
```

Process:
1. Fetch all masters with `calendar_id`
2. For each master:
   - Query Google Calendar for busy times (30 days ahead)
   - Generate free slots (9 AM - 6 PM, 1-hour slots)
   - Save to `calendar` sheet
3. Return sync status

### Admin Operations

```python
# View all bookings
AdminService.list_bookings() → List[Dict]

# View all clients
AdminService.list_clients() → List[Dict]

# Add master
MasterService.create_master(name, calendar_id, specialties)

# Manual slot creation
CalendarRepo.create_slot(date, master_id, start, end)
```

---

## 🐛 Troubleshooting

### Bot doesn't start

**Error:** `BOT_TOKEN not set`
**Solution:** Check `.env` file has correct `BOT_TOKEN`

**Error:** `Invalid token`
**Solution:** Get new token from @BotFather

### Google API errors

**Error:** `credentials.json not found`
**Solution:** Download OAuth credentials from Google Cloud Console

**Error:** `insufficient authentication scopes`
**Solution:** Delete `token.json` and re-authenticate

### Database errors

**Error:** `Spreadsheet not found`
**Solution:** Run `python3 create_google_sheets_structure.py`

**Error:** `Sheet 'clients' not found`
**Solution:** Check spreadsheet has all required tabs

### Calendar sync issues

**Error:** `No calendar_id for master`
**Solution:** Add calendar_id to master in sheets (email format)

**Error:** `Calendar API quota exceeded`
**Solution:** Wait 24h or request quota increase from Google

---

## 📞 Support

- **Documentation:** See `docs/` folder
- **Issues:** GitHub Issues
- **Email:** support@tattoostudio.com

---

## 📄 License

MIT License - see LICENSE file

---

## 🙏 Credits

Built with:
- [Aiogram](https://aiogram.dev/) - Telegram Bot framework
- [Google APIs](https://developers.google.com/) - Sheets & Calendar
- [pytest](https://pytest.org/) - Testing framework

---

**Version:** 2.0.0  
**Last Updated:** December 2025  
**Status:** ✅ Production Ready
