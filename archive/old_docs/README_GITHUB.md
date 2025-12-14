# 🎨 Tattoo Appointment Bot

Telegram bot for tattoo studio appointment booking with multi-language support (Russian, English, Hebrew).

## ✨ Features

- 📅 **Appointment Booking** - Simple booking flow with date, master, and time slot selection
- 🌐 **Multi-language Support** - Russian, English, Hebrew interfaces
- 📊 **Google Sheets Integration** - All data stored in Google Sheets
- 📆 **Google Calendar Sync** - Automatic calendar synchronization
- 👨‍💼 **Admin Panel** - Master management, client list, booking management
- 🤖 **AI Consultation** - Optional AI-powered tattoo consultation (Groq/OpenAI)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Telegram Bot Token (from @BotFather)
- Google Cloud Project with Sheets & Calendar API enabled
- Google OAuth credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cerform/clien_db.git
   cd clien_db
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Setup Google Sheets**
   - Place `credentials.json` from Google Cloud Console in project root
   - Run: `python3 create_google_sheets_structure.py`
   - Copy the Spreadsheet ID to `.env`

6. **Run the bot**
   ```bash
   python3 run.py
   ```

## 📝 Configuration

Edit `.env` file:

```bash
# Telegram
BOT_TOKEN=your_bot_token_here

# Google
SPREADSHEET_ID=your_spreadsheet_id
MASTER_CALENDAR_ID=your_calendar_id

# Admin
ADMIN_USER_IDS=123456789

# AI (Optional)
OPENAI_API_KEY=your_groq_or_openai_key
```

## 🏗️ Project Structure

```
tattoo_appointment_bot/
├── src/
│   ├── bot/
│   │   ├── handlers/          # Message handlers
│   │   ├── keyboards/         # Keyboard layouts
│   │   └── middlewares/       # Bot middlewares
│   ├── config/                # Configuration
│   ├── db/                    # Database layer (Google Sheets)
│   ├── services/              # Business logic
│   └── utils/                 # Utilities
├── .env                       # Configuration (not in git)
├── credentials.json           # Google OAuth (not in git)
├── requirements.txt           # Python dependencies
└── run.py                     # Entry point
```

## 🌍 Languages

The bot supports 3 languages with automatic interface switching:
- 🇷🇺 Russian
- 🇬🇧 English  
- 🇮🇱 Hebrew

Users can change language via "🌐 Language" button.

## 👥 User Flow

1. `/start` - Welcome message
2. "📅 Book Appointment" - Start booking
3. Enter name, phone, tattoo description
4. Select date → master → time slot
5. Confirm booking
6. Done! ✅

## 🔒 Security

- ✅ `.gitignore` protects sensitive files
- ✅ `credentials.json` never committed
- ✅ `.env` never committed
- ✅ Use `.env.example` as template

## 📦 Dependencies

Key packages:
- `aiogram==3.13.1` - Telegram Bot framework
- `google-api-python-client` - Google Sheets/Calendar
- `python-dotenv` - Environment variables
- `groq` - AI API (optional)

## 🛠️ Development

Run tests:
```bash
pytest tests/
```

Check button functionality:
```bash
python3 test_buttons_quick.py
```

## 📄 License

MIT License

## 🤝 Contributing

Pull requests are welcome!

## 📞 Support

For issues and questions, please open a GitHub issue.

---

Made with ❤️ for tattoo artists
