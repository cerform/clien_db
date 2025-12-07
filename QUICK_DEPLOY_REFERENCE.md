# ⚡ QUICK DEPLOYMENT REFERENCE (Copy & Paste Ready)

## Pre-Flight Check (30 seconds)
```bash
# Verify all tests passed
cd /home/etcsys/projects/clien_db && \
source venv/bin/activate && \
python3 -m pytest tests/ -q && \
python3 test_admin_functions.py 2>&1 | grep -E "(PASS|FAIL)"
```

Expected: All tests show PASS ✅

---

## STEP 1: Build Docker Image (~5 min)
```bash
cd /home/etcsys/projects/clien_db && \
docker build -t gcr.io/tattoo-480007/tattoo-bot:latest . && \
docker images | grep tattoo-bot
```

Expected: Image listed with latest tag ✅

---

## STEP 2: Push to GCR (~3 min)
```bash
gcloud auth configure-docker && \
docker push gcr.io/tattoo-480007/tattoo-bot:latest && \
gcloud container images list --repository=gcr.io/tattoo-480007
```

Expected: Image URL appears in output ✅

---

## STEP 3: Deploy to Cloud Run (~3-5 min)

**First, set your values:**
```bash
export TELEGRAM_BOT_TOKEN="YOUR_TOKEN_HERE"
export OPENAI_API_KEY="YOUR_KEY_HERE"
```

**Then deploy:**
```bash
gcloud run deploy tattoo-bot \
  --image gcr.io/tattoo-480007/tattoo-bot:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 3600 \
  --allow-unauthenticated \
  --set-env-vars \
    TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}",\
    GOOGLE_SPREADSHEET_ID="17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ",\
    GOOGLE_CALENDAR_ID="google@tattoo.me",\
    OPENAI_API_KEY="${OPENAI_API_KEY}",\
    OPENAI_ASSISTANT_ID="asst_NPqHLNqQeTi7rgyaZR0iL5kE",\
    ADMIN_IDS="438407739,457343487",\
    ADMIN_WEB_PASSWORD="admin123" \
  --service-account tattoo-bot-sa@tattoo-480007.iam.gserviceaccount.com \
  --project tattoo-480007
```

Expected: "Service [tattoo-bot] deployed successfully" ✅

---

## STEP 4: Get Service URL
```bash
SERVICE_URL=$(gcloud run services describe tattoo-bot \
  --region us-central1 \
  --format='value(status.url)') && \
echo "🔗 Service URL: $SERVICE_URL" && \
curl -X GET "$SERVICE_URL/api/health"
```

Expected: Returns `{"status": "ok"}` and URL ✅

**SAVE THIS URL!** You'll need it for the webhook.

---

## STEP 5: Configure Telegram Webhook
```bash
# Set your values
export BOT_TOKEN="YOUR_TOKEN_HERE"
export SERVICE_URL="https://tattoo-bot-XXXXX.run.app"  # From Step 4

# Set webhook
curl -X POST https://api.telegram.org/bot${BOT_TOKEN}/setWebhook \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${SERVICE_URL}/webhook/telegram\"}" && \
  
# Verify webhook
echo -e "\n\n✅ Webhook verification:" && \
curl https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo | jq '.result | {url, pending_update_count, last_error_message}'
```

Expected: `url` matches service URL, `pending_update_count: 0` ✅

---

## 📊 REAL-TIME MONITORING (Open in new terminal)

### Option 1: Live Stream (Best)
```bash
gcloud run services logs read tattoo-bot \
  --limit=0 \
  --follow \
  --region us-central1
```

### Option 2: Filter Important Events
```bash
gcloud run services logs read tattoo-bot \
  --limit=0 \
  --follow \
  --region us-central1 | grep -E "(ERROR|ADMIN|Function|ДОСТУП)"
```

**Keep this running in background - you'll see all bot activity in real-time!**

---

## 🧪 QUICK TEST (2 minutes)

### Test 1: Send Message in Telegram
```
1. Open Telegram
2. Find your bot
3. Send: "Привет"
4. Should respond naturally with NO BUTTONS
✅ Check logs for: "📨 Message received" and "🟢 Response sent"
```

### Test 2: Test Admin Function (as admin only)
```
1. Send: "Инка, обнови мастера 1: имя Анна"
2. Should process without "ДОСТУП ЗАПРЕЩЁН" error
✅ Check logs for: "👤 User XXXXX - Admin: True"
```

### Test 3: Test Access Denial (as non-admin)
```
1. Send: "Инка, обнови мастера 1: имя Петр"
2. Should respond: "❌ ДОСТУП ЗАПРЕЩЁН! Функция 'edit_master' доступна ТОЛЬКО администраторам"
✅ Check logs for: "👤 User XXXXX - Admin: False"
```

### Test 4: Web Admin Panel
```
1. Open: https://tattoo-bot-XXXXX.run.app/admin
2. Login: admin123
3. Should see dashboard with 6 red buttons
✅ Try clicking each button
```

---

## 📋 STATUS CHECKS (Paste anytime to verify)

```bash
# Check deployment status
echo "=== SERVICE STATUS ===" && \
gcloud run services describe tattoo-bot --region us-central1 \
  --format='value(status.url, status.conditions[0].status)' && \

# Check recent errors
echo -e "\n=== RECENT LOGS ===" && \
gcloud run services logs read tattoo-bot --region us-central1 --limit 10 && \

# Check environment variables
echo -e "\n=== ENV VARS ===" && \
gcloud run services describe tattoo-bot --region us-central1 \
  --format='value(spec.template.spec.containers[0].env[*].[name])' | head -20
```

---

## 🚨 EMERGENCY TROUBLESHOOTING

### Bot Not Responding?
```bash
# Check webhook
curl https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo | jq .

# Check logs for errors
gcloud run services logs read tattoo-bot --limit 30 | grep ERROR

# Restart service
gcloud run services update-traffic tattoo-bot --to-revisions LATEST=100
```

### Admin Functions Not Working?
```bash
# Check admin IDs
echo "Current ADMIN_IDS:"
gcloud run services describe tattoo-bot --region us-central1 \
  --format='value(spec.template.spec.containers[0].env[?name==ADMIN_IDS].value)'

# Your IDs should be: 438407739,457343487
```

### Web Panel Shows 403?
```bash
# Test endpoint directly
curl https://tattoo-bot-XXXXX.run.app/api/health -v

# Check logs
gcloud run services logs read tattoo-bot --limit 20 | grep -E "(auth|403|admin)"
```

---

## ✅ FINAL VERIFICATION

All green? Great! Here's what you should see:

```
✅ Docker image built and in GCR
✅ Service deployed to Cloud Run
✅ Service URL accessible
✅ Telegram webhook configured
✅ Bot responds to messages (no buttons)
✅ Admin functions work (for admins only)
✅ Non-admins get access denied
✅ Web admin panel loads
✅ Real-time logs stream
✅ No errors in logs
✅ All API endpoints working

🎉 PRODUCTION READY!
```

---

## 💾 Quick Backup - Run Before Deployment

```bash
cd /home/etcsys/projects/clien_db && \
git status && \
git add -A && \
git commit -m "📦 Pre-deployment commit - all tests passing" && \
echo "✅ Changes committed"
```

---

## 📞 Useful Links

- Cloud Run Console: https://console.cloud.google.com/run?project=tattoo-480007
- GCR Images: https://console.cloud.google.com/gcr/images/tattoo-480007
- Cloud Logs: https://console.cloud.google.com/logs
- Telegram Bot API: https://core.telegram.org/bots/api

---

**Deployment Time: ~20-30 minutes total**  
**Status: ✅ ALL SYSTEMS GO**

Good luck! 🚀
