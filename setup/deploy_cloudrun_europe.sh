#!/usr/bin/env bash
set -euo pipefail

# Deploy Tattoo Bot to Google Cloud Run (EU region)
# Usage:
#   bash setup/deploy_cloudrun_europe.sh <project_id> <region> [service_name] [cloudsql_instance]
# Example:
#   bash setup/deploy_cloudrun_europe.sh my-gcp-project europe-west1 tattoo-bot eu-instance

PROJECT_ID=${1:-tattoo-480007}
REGION=${2:-europe-west1}
SERVICE_NAME=${3:-tattoo-bot}
CLOUDSQL_INSTANCE=${4:-${SERVICE_NAME}-db}
DB_USER=${DB_USER:-postgres}
DB_NAME=${DB_NAME:-admin_messages}
set -u
set +x

echo "========================================="
echo "🚀 Deploying Tattoo Bot to Cloud Run (Europe)"
echo "========================================="

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl not found. Please install it (used for generating passwords)"
  exit 1
fi

# Confirm values with user
read -p "Project: ${PROJECT_ID}. Continue? [Y/n] " -r
if [[ ! $REPLY =~ ^[Yy] && -n $REPLY ]]; then
  echo "Aborted"
  exit 0
fi

# Set project and region
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com --project=${PROJECT_ID}

# Create Cloud SQL instance (Postgres) in the chosen region if it does not exist
if ! gcloud sql instances describe ${CLOUDSQL_INSTANCE} --project=${PROJECT_ID} >/dev/null 2>&1; then
  echo "Creating Cloud SQL Postgres instance: ${CLOUDSQL_INSTANCE} in ${REGION}"
  DB_PASS=$(openssl rand -base64 24)
  gcloud sql instances create ${CLOUDSQL_INSTANCE} \
    --database-version=POSTGRES_15 \
    --region=${REGION} \
    --tier=db-f1-micro \
    --root-password=${DB_PASS} --project=${PROJECT_ID}

  echo "Created instance. Setting up database and user"
  # Create database and user
  gcloud sql databases create ${DB_NAME} --instance=${CLOUDSQL_INSTANCE} --project=${PROJECT_ID}
  # Set the user password for 'postgres' (or another user if needed)
  gcloud sql users set-password postgres --host=% --instance=${CLOUDSQL_INSTANCE} --password=${DB_PASS} --project=${PROJECT_ID}
  # Create CLOUDSQL_PASSWORD secret so apps can read it via Secret Manager
  # The secret will be created later in the script once the create_or_update_secret func is defined
else
  echo "Cloud SQL instance ${CLOUDSQL_INSTANCE} already exists"
fi

# Compose Cloud SQL connection name
CLOUDSQL_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${CLOUDSQL_INSTANCE}"

# Create service account for Cloud Run if it doesn't exist
SERVICE_ACCOUNT_EMAIL="${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} --project=${PROJECT_ID} >/dev/null 2>&1; then
  gcloud iam service-accounts create ${SERVICE_NAME} --project=${PROJECT_ID} --display-name="Cloud Run service account for ${SERVICE_NAME}"
fi

# Grant the service account the Cloud SQL Client role and secret access
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --role="roles/cloudsql.client"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --role="roles/secretmanager.secretAccessor"

# Create Secret Manager secrets for sensitive env vars (BOT_TOKEN, OPENAI_API_KEY, CLOUDSQL_PASSWORD, SPREADSHEET_ID, GOOGLE_CREDENTIALS)
# If they are present in a local .env, read them. Otherwise prompt the user
source .env || true

ask_or_env() {
  # usage: ask_or_env ENV_VAR_NAME prompt
  local varname="$1"; shift
  local prompt="$*"
  local val="${!varname}"
  if [ -z "$val" ]; then
    read -p "${prompt}: " -r val
  fi
  echo "$val"
}

BOT_TOKEN=$(ask_or_env BOT_TOKEN "Enter TELEGRAM BOT TOKEN")
OPENAI_API_KEY=$(ask_or_env OPENAI_API_KEY "Enter OPENAI API KEY (optional)")
SPREADSHEET_ID=$(ask_or_env SPREADSHEET_ID "Enter SPREADSHEET ID (optional)")
CLOUDSQL_PASSWORD=$(ask_or_env CLOUDSQL_PASSWORD "Enter or confirm DB password (press enter to use previously-set password)")
if [ -z "$CLOUDSQL_PASSWORD" ]; then
  # If blank, try to derive from the instance if we created it
  echo "Using the previously generated password for DB user postgres"
  # It already set earlier if instance was created as DB_PASS; but we didn't store DB_PASS in env. For now, rely on the user.
fi

# Helper to create or update secrets
create_or_update_secret() {
  local name="$1"
  local value="$2"
  if gcloud secrets describe ${name} --project=${PROJECT_ID} >/dev/null 2>&1; then
    echo "Updating secret: ${name}"
    echo -n "$value" | gcloud secrets versions add ${name} --data-file=- --project=${PROJECT_ID}
  else
    echo -n "$value" | gcloud secrets create ${name} --data-file=- --project=${PROJECT_ID}
  fi
}

# If DB_PASS was generated earlier (we created the instance), store as secret
if [ -n "${DB_PASS:-}" ]; then
  create_or_update_secret "CLOUDSQL_PASSWORD" "${DB_PASS}"
fi

create_or_update_secret "BOT_TOKEN" "$BOT_TOKEN"
if [ -n "${OPENAI_API_KEY}" ]; then create_or_update_secret "OPENAI_API_KEY" "$OPENAI_API_KEY"; fi
if [ -n "${SPREADSHEET_ID}" ]; then create_or_update_secret "SPREADSHEET_ID" "$SPREADSHEET_ID"; fi
if [ -n "${CLOUDSQL_PASSWORD}" ]; then create_or_update_secret "CLOUDSQL_PASSWORD" "$CLOUDSQL_PASSWORD"; fi

# Store GOOGLE_CREDENTIALS as a secret (optional)
if [ -f "${GOOGLE_CREDENTIALS_PATH:-credentials.json}" ]; then
  CREDENTIAL_JSON=$(cat "${GOOGLE_CREDENTIALS_PATH:-credentials.json}")
  create_or_update_secret "GOOGLE_CREDENTIALS_JSON" "$CREDENTIAL_JSON"
fi

# Build container image and push to GCR
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Building container image and pushing to Container Registry"
gcloud builds submit --tag ${IMAGE_NAME} --project=${PROJECT_ID}

# Deploy to Cloud Run
# Map secrets to env vars: BOT_TOKEN, OPENAI_API_KEY, CLOUDSQL_PASSWORD, SPREADSHEET_ID, GOOGLE_CREDENTIALS_JSON
SECRETS_ARRAY=()
SECRETS_ARRAY+=("BOT_TOKEN=BOT_TOKEN:latest")
if [ -n "${OPENAI_API_KEY}" ]; then SECRETS_ARRAY+=("OPENAI_API_KEY=OPENAI_API_KEY:latest"); fi
if [ -n "${SPREADSHEET_ID}" ]; then SECRETS_ARRAY+=("SPREADSHEET_ID=SPREADSHEET_ID:latest"); fi
if [ -n "${CLOUDSQL_PASSWORD}" ]; then SECRETS_ARRAY+=("CLOUDSQL_PASSWORD=CLOUDSQL_PASSWORD:latest"); fi
if [ -f "${GOOGLE_CREDENTIALS_PATH:-credentials.json}" ]; then SECRETS_ARRAY+=("GOOGLE_CREDENTIALS_JSON=GOOGLE_CREDENTIALS_JSON:latest"); fi
SECRET_MAP=$(IFS=, ; echo "${SECRETS_ARRAY[*]}")

# Deploy with Cloud SQL instance attachment
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --service-account ${SERVICE_ACCOUNT_EMAIL} \
  --set-env-vars "CLOUD_RUN_ENV=true,DB_SOCKET_DIR=/cloudsql,CLOUDSQL_CONNECTION_NAME=${CLOUDSQL_CONNECTION_NAME},CLOUDSQL_DB=${DB_NAME},CLOUDSQL_USER=postgres" \
  --set-secrets "${SECRET_MAP}" \
  --add-cloudsql-instances ${CLOUDSQL_CONNECTION_NAME} --project=${PROJECT_ID}

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)' --project=${PROJECT_ID})

echo "✅ Deployment Complete!"
echo "========================================="
echo "🌐 Service URL: ${SERVICE_URL}"
echo "🗄️  Cloud SQL: ${CLOUDSQL_CONNECTION_NAME}"

echo "Next steps:"
echo "  - Set Telegram webhook: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=${SERVICE_URL}/webhook/telegram"
echo "  - Check logs: gcloud run logs read --service=${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID}"

echo "If you need to initialize Postgres schema, the app's startup script attempts it automatically."

# Prompt to set webhook automatically if BOT_TOKEN secret exists
read -p "Set Telegram webhook to ${SERVICE_URL}/webhook/telegram now? [Y/n] " -r
if [[ $REPLY =~ ^[Yy] || -z $REPLY ]]; then
  # Access token from Secret Manager
  BOT_TOKEN_VAL=$(gcloud secrets versions access latest --secret=BOT_TOKEN --project=${PROJECT_ID})
  if [ -n "${BOT_TOKEN_VAL}" ]; then
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN_VAL}/setWebhook?url=${SERVICE_URL}/webhook/telegram"
    echo "Webhook request sent. Check bot response and logs."
  else
    echo "BOT_TOKEN secret not found. Set manually."
  fi
fi
