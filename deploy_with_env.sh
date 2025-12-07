#!/bin/bash
set -e

# Load environment variables
cd "$(dirname "$0")"
source .env

# Create env vars string with proper escaping
ENV_VARS="TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}"
ENV_VARS="${ENV_VARS},GOOGLE_SPREADSHEET_ID=${GOOGLE_SPREADSHEET_ID}"
ENV_VARS="${ENV_VARS},GOOGLE_CALENDAR_ID=${GOOGLE_CALENDAR_ID}"
ENV_VARS="${ENV_VARS},OPENAI_API_KEY=${OPENAI_API_KEY}"
ENV_VARS="${ENV_VARS},OPENAI_ASSISTANT_ID=${OPENAI_ASSISTANT_ID}"
ENV_VARS="${ENV_VARS},ADMIN_IDS=438407739"
ENV_VARS="${ENV_VARS},GOOGLE_CREDENTIALS_JSON=/app/credentials.json"
ENV_VARS="${ENV_VARS},TIMEZONE=Europe/Moscow"
ENV_VARS="${ENV_VARS},LOG_LEVEL=INFO"

# Deploy to Cloud Run with all environment variables
gcloud run deploy tattoo-bot \
  --image gcr.io/tattoo-480007/tattoo-bot:latest \
  --region us-central1 \
  --timeout 3600 \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated \
  --set-env-vars "${ENV_VARS}" \
  --quiet

echo "✅ Deploy completed!"
sleep 10
gcloud run services describe tattoo-bot --region us-central1 --format='value(status.url)'
