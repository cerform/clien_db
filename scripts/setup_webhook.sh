#!/bin/bash
set -e

# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe telegram-bot --region=us-central1 --format="value(status.url)")

echo "🌐 Cloud Run Service URL: $SERVICE_URL"

# Get bot token from Secret Manager
BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token --project=tattoo-480007)

echo "🔧 Setting up Telegram webhook..."

# Set webhook
WEBHOOK_URL="${SERVICE_URL}/webhook"
echo "   Webhook URL: $WEBHOOK_URL"

# Call Telegram API to set webhook
RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${WEBHOOK_URL}\"}")

echo "📡 Response from Telegram:"
echo "$RESPONSE" | python3 -m json.tool

# Check webhook info
echo ""
echo "📊 Webhook Info:"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool

echo ""
echo "✅ Webhook setup complete!"
echo ""
echo "🧪 Test your bot by sending /start to @YourBotUsername"
