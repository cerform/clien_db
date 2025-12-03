# 🚀 Deployment Guide

## Quick Deploy on New Server

### 1. Clone Repository
```bash
git clone https://github.com/cerform/clien_db.git
cd clien_db
```

### 2. Setup Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Bot

Create `.env` file (use `.env.example` as template):
```bash
cp .env.example .env
nano .env
```

Fill in:
- `BOT_TOKEN` - from @BotFather
- `SPREADSHEET_ID` - from Google Sheets
- `MASTER_CALENDAR_ID` - from Google Calendar
- `ADMIN_USER_IDS` - your Telegram user ID
- `OPENAI_API_KEY` - Groq or OpenAI API key (optional)

### 4. Setup Google Credentials

1. Download `credentials.json` from Google Cloud Console
2. Place it in project root
3. Run initial setup:
   ```bash
   python3 create_google_sheets_structure.py
   ```
4. Follow OAuth flow in browser
5. `token.json` will be created automatically

### 5. Run Bot

**Development:**
```bash
python3 run.py
```

**Production (with systemd):**

Create `/etc/systemd/system/tattoo-bot.service`:
```ini
[Unit]
Description=Tattoo Appointment Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/clien_db
Environment="PATH=/path/to/clien_db/.venv/bin"
ExecStart=/path/to/clien_db/.venv/bin/python3 run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tattoo-bot
sudo systemctl start tattoo-bot
sudo systemctl status tattoo-bot
```

View logs:
```bash
sudo journalctl -u tattoo-bot -f
```

## 🔄 Update Deployed Bot

```bash
cd /path/to/clien_db
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart tattoo-bot
```

## 🐳 Docker Deployment (Optional)

Create `Dockerfile`:
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
docker run -d --name tattoo-bot \
  --env-file .env \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  tattoo-bot
```

## 🔐 Security Checklist

- ✅ Never commit `.env`
- ✅ Never commit `credentials.json`
- ✅ Never commit `token.json`
- ✅ Use environment variables for secrets
- ✅ Keep dependencies updated
- ✅ Use HTTPS for webhooks (if used)
- ✅ Restrict admin access via `ADMIN_USER_IDS`

## 📊 Monitoring

Check bot health:
```bash
# Process status
ps aux | grep run.py

# Bot logs
tail -f bot.log

# System logs (if using systemd)
sudo journalctl -u tattoo-bot -f
```

## 🆘 Troubleshooting

**Bot not responding:**
```bash
# Check if running
ps aux | grep run.py

# Check logs
tail -100 bot.log

# Restart
sudo systemctl restart tattoo-bot
```

**Google API errors:**
```bash
# Delete token and re-authenticate
rm token.json
python3 run.py
# Follow OAuth flow
```

**Database errors:**
```bash
# Verify spreadsheet access
python3 test_sheets.py
```

## 📱 Testing After Deploy

1. Open bot in Telegram
2. Send `/start`
3. Try "🌐 Language" - switch to different languages
4. Try "📅 Book Appointment" - complete full booking flow
5. As admin: check "📊 Dashboard"

## 🔄 Backup

**Important data to backup:**
- `.env` - configuration
- `credentials.json` - Google OAuth
- `token.json` - Google refresh token
- Google Sheets (automatic backup via Google)

**Backup command:**
```bash
tar -czf tattoo-bot-backup-$(date +%Y%m%d).tar.gz \
  .env credentials.json token.json
```

---

Good luck! 🎉
