#!/usr/bin/env bash
set -euo pipefail
# Simple deploy helper for production Cloud Run service
# Usage: PROJECT=... IMAGE=... ./scripts/deploy_production.sh

: "${IMAGE:?Please set IMAGE (eg gcr.io/<project>/tattoo-bot:sha)}"
: "${PROJECT:=$(gcloud config get-value project)}"
: "${REGION:=europe-west1}"

SERVICE_NAME="tattoo-bot-prod"

echo "Deploying $SERVICE_NAME to $REGION in project $PROJECT"

gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --set-secrets TELEGRAM_BOT_TOKEN=projects/$PROJECT/secrets/TELEGRAM_BOT_TOKEN:latest,OPENAI_API_KEY=projects/$PROJECT/secrets/OPENAI_API_KEY:latest,CLOUDSQL_PASSWORD=projects/$PROJECT/secrets/CLOUDSQL_PASSWORD:latest,SPREADSHEET_ID=projects/$PROJECT/secrets/SPREADSHEET_ID:latest,WEBHOOK_SECRET=projects/$PROJECT/secrets/WEBHOOK_SECRET:latest \
  --update-env-vars CLOUDSQL_CONNECTION_NAME=${CLOUDSQL_CONNECTION_NAME:-},CLOUDSQL_DB=${CLOUDSQL_DB:-inka},CLOUDSQL_USER=${CLOUDSQL_USER:-postgres},ENV=production,ENABLE_LLM=${ENABLE_LLM:-true} \
  --platform managed \
  --allow-unauthenticated

echo "Deployment submitted. Use gcloud run services describe $SERVICE_NAME --region $REGION to view the status." 
