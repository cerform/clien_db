# Installation

1. Ensure Python 3.9+
2. Copy `.env.example` to `.env` and fill:
   - BOT_TOKEN: from @BotFather
   - ADMIN_USER_IDS: your Telegram ID
3. Get OAuth2 credentials from Google Cloud Console (Desktop app JSON)
4. Save as `credentials.json` in project root
5. Run `bash bootstrap.sh`
6. Run `python3 create_google_sheets_structure.py` to create spreadsheet
7. Set SPREADSHEET_ID in `.env`
8. Run `python3 run.py`
