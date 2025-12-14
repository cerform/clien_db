# 🔑 Google API Setup - Step by Step

## ⚠️ Current Issue
Your `credentials.json` is a placeholder. You need real Google OAuth2 credentials.

---

## ✅ Step 1: Create Google Cloud Project

1. Go to **[Google Cloud Console](https://console.cloud.google.com/)**
2. Click **"Select a Project"** (top left)
3. Click **"NEW PROJECT"**
4. Name: `TattooStudioBot`
5. Click **CREATE**
6. Wait for project to be created

---

## ✅ Step 2: Enable APIs

1. In Google Cloud Console, search for **"Sheets API"**
2. Click **"Google Sheets API"**
3. Click **ENABLE**

4. Go back, search for **"Calendar API"**
5. Click **"Google Calendar API"**
6. Click **ENABLE**

---

## ✅ Step 3: Create OAuth2 Credentials

1. In left menu, click **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** (top)
3. Select **"OAuth client ID"**
4. You'll see: "To create an OAuth client ID, you must first set up the OAuth consent screen"
5. Click **"CONFIGURE CONSENT SCREEN"**

### Configure Consent Screen:
- User Type: **"External"** → Click CREATE
- App name: `TattooStudioBot`
- User support email: Your email
- Developer contact: Your email
- Click **SAVE AND CONTINUE**
- Scopes: Click **ADD OR REMOVE SCOPES**
  - Search and add:
    - `https://www.googleapis.com/auth/spreadsheets`
    - `https://www.googleapis.com/auth/calendar`
  - Click **UPDATE**
- Click **SAVE AND CONTINUE** → **SAVE AND CONTINUE** again
- Click **BACK TO DASHBOARD**

---

## ✅ Step 4: Create Desktop App Credentials

1. Go back to **Credentials** (left menu)
2. Click **"+ CREATE CREDENTIALS"** again
3. Select **"OAuth client ID"**
4. Application type: **"Desktop app"**
5. Name: `tattoo-bot-desktop`
6. Click **CREATE**
7. Click **DOWNLOAD** (or copy JSON)

---

## ✅ Step 5: Save Credentials File

1. Save downloaded file as `credentials.json` in project root:
   ```
   /Users/simanbekov/ttmanager/tattoo_appointment_bot/credentials.json
   ```

2. The file should look like:
   ```json
   {
     "installed": {
       "client_id": "YOUR_ID.apps.googleusercontent.com",
       "project_id": "tattoo-studio-bot-xxx",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
       "client_secret": "YOUR_SECRET",
       "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob","http://localhost"]
     }
   }
   ```

---

## ✅ Step 6: Create Spreadsheet

Now run (it will open browser for auth):
```bash
python3 create_google_sheets_structure.py
```

First time it will:
1. Open browser asking for permissions
2. You authorize
3. Creates `token.json` (auto-refreshing token)
4. Creates new Google Spreadsheet
5. Prints: `Created spreadsheet: 1ABC2DEF3GHI...`

---

## ✅ Step 7: Add to .env

Copy the Spreadsheet ID and add to `.env`:
```
SPREADSHEET_ID=1ABC2DEF3GHI...
```

---

## ✅ Done! 🎉

Now you can run:
```bash
python3 run.py
```

---

## 📝 Notes

- `credentials.json` = OAuth app config (public, safe to commit)
- `token.json` = Your refresh token (PRIVATE, add to `.gitignore`)
- Bot will auto-refresh token when needed
- If token expires, delete `token.json` and re-run any script

---

## 🔗 Google Cloud URLs

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)
- [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)
