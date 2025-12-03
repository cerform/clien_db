# 🚀 Quick Start Guide - Tattoo Appointment Bot

**Last Updated:** December 3, 2025  
**Status:** ✅ Production Ready  
**Time to Launch:** ~15 minutes

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.10 or higher installed
- [ ] Google account
- [ ] Telegram account
- [ ] Terminal/command line access

---

## 🎯 Step-by-Step Setup

### Step 1: Environment Setup (2 minutes)

```bash
# Navigate to project directory
cd tattoo_appointment_bot

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

✅ **Verify:** Run `python --version` - should show Python 3.10+

---

### Step 2: Get Telegram Bot Token (3 minutes)

1. Open Telegram and search for **@BotFather**
2. Send command: `/newbot`
3. Follow prompts:
   - Bot name: `My Tattoo Studio Bot`
   - Username: `mytattoo_appt_bot` (must end with 'bot')
4. **Copy the token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

✅ **Save token** - you'll need it in Step 4

---

### Step 3: Setup Google APIs (5 minutes)

#### 3.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a project" → "New Project"
3. Name: `Tattoo Bot`, click "Create"

#### 3.2 Enable APIs

1. In Cloud Console, go to "APIs & Services" → "Library"
2. Search and enable:
   - **Google Sheets API** (click Enable)
   - **Google Calendar API** (click Enable)

#### 3.3 Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure consent screen:
   - User Type: **External**
   - App name: `Tattoo Bot`
   - Support email: your email
   - Save and continue (skip optional fields)
4. Back to Credentials:
   - Application type: **Desktop app**
   - Name: `Tattoo Bot Desktop`
   - Click "Create"
5. **Download JSON** → save as `credentials.json` in project root

✅ **Verify:** File `credentials.json` exists in project folder

---

### Step 4: Configure Environment (2 minutes)

```bash
# Copy example config
cp .env.example .env

# Edit config file
nano .env  # or use your favorite editor
```

Update these values:

```env
# Required: Your bot token from Step 2
BOT_TOKEN=YOUR_TOKEN_HERE

# Required: Your Telegram user ID (get from @userinfobot)
ADMIN_USER_IDS=YOUR_USER_ID

# Leave these as default for now
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
DEFAULT_TIMEZONE=Asia/Jerusalem
```

✅ **Save and close** the file

---

### Step 5: Initialize Database (2 minutes)

```bash
# Run database creation script
python3 create_google_sheets_structure.py
```

This will:
1. Open browser for Google authentication
2. Ask for permissions (click "Allow")
3. Create a new Google Sheet with tabs: clients, masters, calendar, bookings
4. Show you the **SPREADSHEET_ID**

**Example output:**
```
✅ Spreadsheet created!
📋 SPREADSHEET_ID: 1abc...xyz
📝 Copy this ID to your .env file
```

**Copy the SPREADSHEET_ID** and add to `.env`:

```env
SPREADSHEET_ID=1abc...xyz
```

✅ **Verify:** Check Google Drive - you should see new spreadsheet

---

### Step 6: Run Tests (Optional but Recommended) (1 minute)

```bash
# Run test suite
chmod +x run_tests.sh
./run_tests.sh
```

Expected output:
```
🧪 Running Unit Tests...
tests/test_booking_service.py ✅ PASSED
tests/test_calendar_service.py ✅ PASSED
... (more tests)
✅ Tests complete!
```

✅ If all tests pass, you're good to go!

---

### Step 7: Launch Bot (1 minute)

```bash
# Start the bot
python3 run.py
```

Expected output:
```
============================================================
🎨 Tattoo Appointment Bot
============================================================
📋 Spreadsheet ID: 1abc...xyz
👤 Admin Users: [123456789]
🌍 Timezone: Asia/Jerusalem
🚀 Mode: Polling
============================================================
✅ Bot started successfully!
INFO:aiogram:Start polling
INFO:aiogram:Run polling for bot
```

✅ **Bot is live!**

---

## 🎉 Test Your Bot

### 1. Find Your Bot

Open Telegram and search for your bot username (e.g., `@mytattoo_appt_bot`)

### 2. Start Conversation

Send: `/start`

Expected response:
```
🎨 Welcome to Tattoo Studio!

Book your perfect tattoo appointment 🔥
```

### 3. Test Booking Flow

1. Click **"📅 Book Appointment"**
2. Enter name: `John Doe`
3. Enter phone: `+972501234567`
4. Describe tattoo: `Small dragon on arm`
5. Select date from calendar buttons
6. Select master
7. Select time slot
8. Confirm booking

✅ **Success!** Booking should be created in Google Sheets

### 4. Test Admin Functions

Send: `/admin`

You should see admin dashboard with options:
- 📊 Dashboard
- 👨‍🎨 Add Master
- ⏰ Add Slot
- 📅 Sync Calendar
- 👥 View Clients
- 📋 View Bookings

---

## 🔧 Troubleshooting

### Issue: "BOT_TOKEN not set"

**Solution:** Check `.env` file has `BOT_TOKEN=your_token_here` (no quotes)

### Issue: "credentials.json not found"

**Solution:** Download OAuth credentials from Google Cloud Console to project root

### Issue: "Insufficient authentication scopes"

**Solution:** 
1. Delete `token.json`
2. Run `python3 create_google_sheets_structure.py` again
3. Re-authenticate with all permissions

### Issue: Bot doesn't respond

**Solutions:**
1. Check bot is running (no errors in terminal)
2. Verify BOT_TOKEN is correct
3. Make sure virtual environment is activated
4. Check internet connection

### Issue: "Sheet 'clients' not found"

**Solution:** Run `python3 create_google_sheets_structure.py` again

---

## 📚 Next Steps

### Add Your First Master

1. Open the Google Sheet (check Google Drive)
2. Go to **"masters"** tab
3. Add a row:
   ```
   master_001 | Jane Artist | jane@example.com | traditional,watercolor | yes
   ```
4. Save

### Sync Calendar Slots

1. In bot, send `/admin`
2. Click **"📅 Sync Calendar"**
3. Wait for confirmation (creates 30 days of slots)

### Test Complete Flow

1. As client: Book appointment
2. Check Google Sheets → new entry in "bookings"
3. Check master's Google Calendar → event created
4. As admin: View booking in `/admin` → "📋 View Bookings"

---

## 🚀 Production Deployment

When ready for production:

1. **Get a domain and SSL certificate**
2. **Switch to webhook mode** (edit `.env`):
   ```env
   USE_WEBHOOK=true
   WEBHOOK_URL=https://yourdomain.com/bot/webhook
   ```
3. **Deploy** to server (Docker/Systemd - see README_COMPLETE.md)
4. **Monitor logs** for any issues

---

## 📞 Support

- **Documentation:** See `README_COMPLETE.md` for full details
- **Project Status:** See `PROJECT_STATUS.md` for completion checklist
- **Architecture:** See `docs/ARCHITECTURE.md` for technical details

---

## ✅ Launch Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Telegram bot token obtained
- [ ] Google credentials downloaded
- [ ] `.env` file configured
- [ ] Database initialized (Google Sheets created)
- [ ] Tests passing (optional)
- [ ] Bot running without errors
- [ ] Test booking completed successfully
- [ ] Admin functions tested

**All checked?** 🎉 **You're ready for production!**

---

**Time Taken:** ~15 minutes  
**Status:** ✅ Ready to Launch  
**Next:** Add masters, sync calendar, start taking bookings! 🚀
