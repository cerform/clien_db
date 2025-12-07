# 🎯 PRODUCTION DEPLOYMENT CHECKLIST

## Pre-Deployment Verification

### 1. Local Testing ✅
```bash
# Test configuration
python3 debug_config.py
# Expected: 16 passed, 0 failed
```

### 2. Code Compilation ✅
```bash
python3 -m py_compile run_cloud.py debug_config.py src/bot/handlers/debug_handler.py
# Expected: No errors
```

### 3. All Files Modified
- ✅ run_cloud.py (NEW)
- ✅ debug_config.py (NEW)
- ✅ src/bot/handlers/debug_handler.py (NEW)
- ✅ src/bot/handlers/__init__.py (UPDATED)
- ✅ src/main.py (UPDATED)
- ✅ src/db/sheets_client.py (FIXED)
- ✅ src/calendars/google_calendar_sync.py (ENHANCED)
- ✅ src/ai/advanced_inka.py (FIXED)
- ✅ DEPLOYMENT_GUIDE.md (NEW)
- ✅ QA_RESOLUTION_SUMMARY.md (NEW)

### 4. Git Status
```bash
git status
# Expected: Nothing to commit, working tree clean
```

---

## Cloud Run Deployment

### Step 1: Deploy New Revision
```bash
cd /home/etcsys/projects/clien_db

gcloud run deploy tattoo-bot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="K_SERVICE=tattoo-bot" \
  --max-instances 100 \
  --entry-point="python -m run_cloud" \
  --memory 512Mi \
  --timeout 300 \
  --project tattoo-480007 \
  2>&1
```

**Expected Output**:
```
✓ Deploying...
✓ Creating Revision... tattoo-bot-00030-xxxx
✓ Routing traffic...
Service [tattoo-bot] deployed successfully.
URL: https://tattoo-bot-xxxxx.run.app
```

### Step 2: Verify Deployment

#### 2a. Check Service is Running
```bash
gcloud run services describe tattoo-bot --region us-central1 --format='value(status.url)'
# Expected: https://tattoo-bot-xxxxx.run.app
```

#### 2b. Check Health Endpoint
```bash
SERVICE_URL=$(gcloud run services describe tattoo-bot --region us-central1 --format='value(status.url)')
curl -X GET "$SERVICE_URL/health"
# Expected: 200 OK or similar response
```

#### 2c. Check Recent Logs
```bash
gcloud run services logs read tattoo-bot --region us-central1 --limit 30
# Expected: Should see startup messages, no ERROR entries
```

#### 2d. Check Deployed Revision
```bash
gcloud run services describe tattoo-bot --region us-central1 --format='value(status.latestCreatedRevisionName)'
# Expected: tattoo-bot-00030-xxxx (or next version number)
```

### Step 3: Test Bot Functionality

#### 3a. Test as Admin (from Telegram)
```
/debug_config
```

Expected Response:
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

#### 3b. Test Client Creation (as regular user)
1. Send: "Привет, хочу записаться на тату"
2. Bot should:
   - ✅ Ask for name
   - ✅ Ask for phone
   - ✅ Ask for email
   - ✅ Save to Google Sheets
   - ✅ Show confirmation

#### 3c. Test Webhook (technical)
```bash
SERVICE_URL=$(gcloud run services describe tattoo-bot --region us-central1 --format='value(status.url)')
curl -X POST "$SERVICE_URL/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 1,
    "message": {
      "message_id": 1,
      "chat": {"id": 123},
      "text": "test"
    }
  }'
# Expected: 200 OK
```

### Step 4: Monitor Logs (First 5 Minutes)

```bash
# Watch logs in real-time
gcloud run services logs read tattoo-bot --region us-central1 --limit 100 --follow

# OR check for errors
gcloud run services logs read tattoo-bot --region us-central1 --limit 100 | grep -i error
# Expected: No ERROR entries (warnings OK)
```

---

## Post-Deployment Verification

### Test Case 1: New User Registration
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Send message to bot | Bot responds with /start menu |
| 2 | Tap "Запись на процедуру" | Bot asks for name |
| 3 | Enter name | Bot asks for phone |
| 4 | Enter phone | Bot asks for email |
| 5 | Enter email | ✅ Bot saves and shows "Запись сохранена" |
| 6 | Check Google Sheets | ✅ New row in 'clients' sheet |

### Test Case 2: Returning User Detection
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | User who already exists sends message | Bot recognizes user |
| 2 | Check `/debug_sheets` | ✅ Shows all sheets correctly |
| 3 | Check `/debug_calendar` | ✅ Calendar access OK |

### Test Case 3: Admin Commands
| Command | Expected Result |
|---------|-----------------|
| /debug_config | ✅ Shows full config status |
| /debug_sheets | ✅ Shows spreadsheet structure |
| /debug_calendar | ✅ Shows calendar info |
| /debug_help | ✅ Shows help text |

### Test Case 4: Error Handling
| Scenario | Expected Behavior |
|----------|-------------------|
| Invalid email entered | ✅ Bot shows error, asks again |
| Google Sheets temporarily unavailable | ✅ Error message shown to user |
| User not in admin list tries /debug_config | ✅ "Access denied" message |

---

## Rollback Plan (If Needed)

### If Something Goes Wrong

#### Option 1: Revert to Previous Revision
```bash
# List revisions
gcloud run services describe tattoo-bot --region us-central1 \
  --format='value(status.traffic[].[revisionName,percent])'

# Route 100% to previous revision
gcloud run services update-traffic tattoo-bot \
  --to-revisions tattoo-bot-00029-s7x=100 \
  --region us-central1
```

#### Option 2: Quick Git Rollback
```bash
# See recent commits
git log --oneline -10

# If needed: revert last commit
git revert HEAD
git push

# Deploy previous version
gcloud run deploy tattoo-bot --source . --region us-central1
```

---

## Success Criteria

✅ **Deployment Successful When:**
1. Service URL is accessible
2. Health endpoint responds (200 or 404 for GET /webhook)
3. `/debug_config` command works for admins
4. No ERROR entries in recent logs
5. User can register new client (saves to Sheets)
6. Returning users are recognized

❌ **Issues If:**
1. Service shows errors in logs
2. Admin debug commands fail
3. Client creation doesn't save to Sheets
4. Calendar access fails
5. Webhook doesn't accept POST requests

---

## Monitoring (First Day)

```bash
# Check every 30 minutes
watch -n 30 'echo "=== Deployment Status ===" && \
  gcloud run services describe tattoo-bot --region us-central1 --format="value(status.url)" && \
  echo "=== Recent Logs ===" && \
  gcloud run services logs read tattoo-bot --region us-central1 --limit 20 | head -20'
```

---

## After Deployment Confirmed

### 1. Update Documentation
- [ ] Update DEPLOYMENT_GUIDE.md with actual revision number
- [ ] Add deployment date to changelog
- [ ] Notify team of successful deployment

### 2. Monitor for 24 Hours
- [ ] Check logs periodically
- [ ] Monitor error rates
- [ ] Verify client creation works
- [ ] Test admin commands

### 3. Performance Baseline
Record these metrics:
- [ ] Response time: _____ ms
- [ ] Error rate: _____ %
- [ ] Successful registrations: _____ per hour
- [ ] Failed registrations: _____ per hour

---

## Key Contacts

If issues arise:
- **Service Account**: tattoo-bot-sa@tattoo-480007.iam.gserviceaccount.com
- **Service URL**: https://tattoo-bot-[ID].run.app
- **Region**: us-central1
- **Project**: tattoo-480007

---

## Final Notes

✅ **Bot is production-ready with:**
- Dual-credential authentication (local + Cloud Run)
- Comprehensive error handling
- Debug commands for troubleshooting
- Automatic configuration from environment variables
- Proper logging and monitoring

✅ **All 10 QA issues have been resolved**

✅ **Ready to deploy to production**
