#!/usr/bin/env bash
set -euo pipefail
# One-shot wrapper to deploy the microservices stack to GCP
# Usage:
#   PROJECT_ID=your-gcp-project REGION=us-central1 ./scripts/deploy_all.sh [--yes]
# Requires:
#   - gcloud installed and authenticated
#   - .env file with BOT_TOKEN, OPENAI_API_KEY, CLOUDSQL_PASSWORD, SPREADSHEET_ID if you want secrets auto-created

PROJECT_ID=${PROJECT_ID:-}
REGION=${REGION:-us-central1}
NONINTERACTIVE=${NONINTERACTIVE:-0}
YES=${1:-}

if [[ -z "$PROJECT_ID" ]]; then
  echo "Please set PROJECT_ID env var (e.g., PROJECT_ID=tattoo-480007)" >&2
  exit 1
fi

echo "Deploying all services to project=${PROJECT_ID}, region=${REGION}"

if [[ -f .env ]]; then
  echo "Sourcing .env (for secret creation and env values)..."
  # expose env vars defined; do not export safe shell code
  set -o allexport
  source .env
  set +o allexport
fi

if [[ ${NONINTERACTIVE} -ne 1 ]] && [[ -z ${YES} ]]; then
  read -p "This will deploy images and provision infra in project ${PROJECT_ID}. Continue? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborting."; exit 2
  fi
fi

# Delegate to multi-service deploy script
export PROJECT_ID REGION
./scripts/deploy_cloudrun_multi.sh

# After deploy, set Telegram webhook using BOT_TOKEN secret
echo "Attempting to configure Telegram webhook..."
BOT_TOKEN=""
if [[ -n ${BOT_TOKEN:-} ]]; then
  BOT_TOKEN=${BOT_TOKEN}
fi
# Try get bot token from Secret Manager if possible
if [[ -z "$BOT_TOKEN" ]]; then
  if gcloud secrets describe BOT_TOKEN --project=${PROJECT_ID} &>/dev/null; then
    BOT_TOKEN=$(gcloud secrets versions access latest --secret=BOT_TOKEN --project=${PROJECT_ID} | tr -d '\n')
  fi
fi
SERVICE_URL=$(gcloud run services describe tattoo-bot --region=${REGION} --format='value(status.url)' --project=${PROJECT_ID}) || true

if [[ -n "$BOT_TOKEN" && -n "$SERVICE_URL" ]]; then
  echo "Setting webhook to ${SERVICE_URL}/webhook/telegram"
  curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" -H "Content-Type: application/json" -d "{\"url\": \"${SERVICE_URL}/webhook/telegram\"}" | jq -r . || true
  echo -n "Webhook configured (if bot token is valid)."
else
  echo "Could not set webhook - BOT_TOKEN or SERVICE_URL is missing. (BOT_TOKEN present: ${BOT_TOKEN:+yes}, SERVICE_URL: ${SERVICE_URL:+yes})"
fi

# Wait a bit and run health checks
echo "Waiting 5 seconds for services to stabilize..."
sleep 5
echo "Running health checks..."
HEALTH_URL="$(gcloud run services describe tattoo-backend --region=${REGION} --format='value(status.url)' --project=${PROJECT_ID})/api/health"
if [[ -n "$HEALTH_URL" ]]; then
  curl -s "$HEALTH_URL" | jq -C . || true
else
  echo "Backend health endpoint not available to test"
fi

echo "Deploy complete. Verify service URLs and logs in GCP Console."
