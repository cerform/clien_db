#!/bin/bash
# Deploy Tattoo Bot to Google Cloud Run with Cloud SQL

set -e

# Configuration
PROJECT_ID="tattoo-480007"
REGION="europe-west1"
SERVICE_NAME="tattoo-bot"
CLOUDSQL_INSTANCE="tattoo-bot-db"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "========================================="
echo "🚀 Deploying Tattoo Bot to Cloud Run"
echo "========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "📌 Setting GCP project: ${PROJECT_ID}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com

# Build container image using Cloud Build
echo "🔨 Building container image..."
# Run pre-deploy checks; if they fail abort
if command -v python3 &>/dev/null; then
    echo "🔍 Running pre-deploy checks..."
    python3 ./scripts/predeploy_check.py || { echo "Predeploy checks failed"; exit 2; }
else
    echo "⚠️ Python3 not found in PATH; skipping pre-deploy script checks"
fi
gcloud builds submit --tag ${IMAGE_NAME}

# Check if Cloud SQL instance exists
echo "🗄️  Checking Cloud SQL instance..."
if ! gcloud sql instances describe ${CLOUDSQL_INSTANCE} --project=${PROJECT_ID} &> /dev/null; then
    echo "⚠️  Cloud SQL instance not found. Creating..."
    gcloud sql instances create ${CLOUDSQL_INSTANCE} \
        --database-version=MYSQL_8_0 \
        --tier=db-f1-micro \
        --region=${REGION} \
        --root-password=$(openssl rand -base64 32)

    echo "✅ Cloud SQL instance created"

    # Create database
    echo "📦 Creating database..."
    gcloud sql databases create admin_messages --instance=${CLOUDSQL_INSTANCE}
else
    echo "✅ Cloud SQL instance exists"
fi

# Get Cloud SQL connection name
CLOUDSQL_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${CLOUDSQL_INSTANCE}"
echo "🔗 Cloud SQL Connection: ${CLOUDSQL_CONNECTION_NAME}"

# Check for secrets
echo "🔐 Checking secrets..."
SECRETS_TO_SET=""

# Read required environment variables
if [ -f .env ]; then
    echo "📝 Reading .env file..."
    source .env

    # Create secrets if they don't exist (skip suspicious placeholder values)
    for SECRET_NAME in BOT_TOKEN OPENAI_API_KEY CLOUDSQL_PASSWORD SPREADSHEET_ID; do
        SECRET_VALUE="${!SECRET_NAME}"
        if [ -n "$SECRET_VALUE" ]; then
            # Heuristic: skip obvious placeholders to avoid deploying invalid secrets
            if echo "$SECRET_VALUE" | grep -Ei "your|replace|dummy|test|example|bot_token" >/dev/null || [ ${#SECRET_VALUE} -lt 30 ] || [[ "$SECRET_VALUE" != *":"* && "$SECRET_NAME" == "BOT_TOKEN" ]]; then
                echo "⚠️ Skipping creation of secret $SECRET_NAME because its value looks like a placeholder or is too short"
                continue
            fi
            # Check if secret exists
            if ! gcloud secrets describe $SECRET_NAME --project=${PROJECT_ID} &> /dev/null; then
                 echo "Creating secret: $SECRET_NAME"
                 echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" --data-file=- --project="${PROJECT_ID}"
            else
                 echo "Updating secret: $SECRET_NAME"
                 echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project="${PROJECT_ID}"
            fi
            SECRETS_TO_SET="${SECRETS_TO_SET}${SECRET_NAME}=:${SECRET_NAME},"
        fi
    done
fi

# Decide BOT_MODE and resources based on presence of OpenAI API key
if [ -n "${OPENAI_API_KEY}" ]; then
    BOT_MODE=advanced
    MEM=1Gi
    echo "🔧 Detected OPENAI_API_KEY. Enabling AI mode (BOT_MODE=advanced) and setting memory to ${MEM}"
    ENABLE_LLM=true
else
    # If OPENAI_API_KEY not in .env, check Secret Manager for OPENAI_API_KEY
    # If secret exists, use advanced mode as well
    if gcloud secrets describe OPENAI_API_KEY --project=${PROJECT_ID} &> /dev/null; then
        OPENAI_SECRET_VALUE=$(gcloud secrets versions access latest --secret=OPENAI_API_KEY --project=${PROJECT_ID} 2>/dev/null || true)
        if [ -n "${OPENAI_SECRET_VALUE}" ]; then
            BOT_MODE=advanced
            MEM=1Gi
            echo "🔧 Found OPENAI_API_KEY in Secret Manager. Enabling AI mode (BOT_MODE=advanced) and setting memory to ${MEM}"
        else
            BOT_MODE=inka
            MEM=512Mi
            echo "🔧 OpenAI secret exists but is empty. Using INKA-only mode (BOT_MODE=inka) and memory ${MEM}"
            ENABLE_LLM=false
        fi
    else
        BOT_MODE=inka
        MEM=512Mi
        echo "🔧 No OpenAI key detected. Using INKA-only mode (BOT_MODE=inka) and memory ${MEM}"
        ENABLE_LLM=false
    fi
fi

# Ensure service account has access to secrets
echo "🔐 Granting Secret Manager access to service account: ${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
for SECRET_NAME in BOT_TOKEN OPENAI_API_KEY CLOUDSQL_PASSWORD SPREADSHEET_ID; do
    if gcloud secrets describe ${SECRET_NAME} --project=${PROJECT_ID} &> /dev/null; then
        gcloud secrets add-iam-policy-binding ${SECRET_NAME} \
            --member="serviceAccount:${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
            --role="roles/secretmanager.secretAccessor" --project=${PROJECT_ID} || true
    fi
done

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory ${MEM} \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --add-cloudsql-instances ${CLOUDSQL_CONNECTION_NAME} \
    --set-env-vars "CLOUD_RUN_ENV=true,DB_SOCKET_DIR=/cloudsql,CLOUDSQL_CONNECTION_NAME=${CLOUDSQL_CONNECTION_NAME},CLOUDSQL_DB=admin_messages,CLOUDSQL_USER=root,BOT_MODE=${BOT_MODE}" \
    --set-env-vars "ENABLE_LLM=${ENABLE_LLM}" \
    --set-secrets "BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,CLOUDSQL_PASSWORD=CLOUDSQL_PASSWORD:latest,SPREADSHEET_ID=SPREADSHEET_ID:latest" \
    --service-account ${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo "🌐 Service URL: ${SERVICE_URL}"
echo "🗄️  Cloud SQL: ${CLOUDSQL_CONNECTION_NAME}"
echo ""
echo "📋 Next steps:"
echo "1. Set Telegram webhook: ${SERVICE_URL}/webhook/telegram"
echo "2. Access admin panel: ${SERVICE_URL}"
echo "3. Check logs: gcloud run logs read --service=${SERVICE_NAME} --region=${REGION}"
echo ""
echo "📨 Auto-configuring webhook via /api/setup-webhook..."
if command -v curl &> /dev/null ; then
    # Wait a moment for service to become healthy
    sleep 5
    # Try calling the setup endpoint; this will configure Telegram webhook using BOT_TOKEN secret
    # First update the service to include SERVICE_URL env var so the application knows its public URL
    echo "🔄 Updating Cloud Run environment variables (SERVICE_URL) ..."
    gcloud run services update ${SERVICE_NAME} --region ${REGION} --update-env-vars SERVICE_URL=${SERVICE_URL} || true

    SETUP_RESULT=$(curl -s -X POST "${SERVICE_URL}/api/setup-webhook" -H "Content-Type: application/json" || true)
    echo "Webhook setup response: ${SETUP_RESULT}"
else
    echo "⚠️ curl not found: cannot call /api/setup-webhook. You can do it manually: curl -X POST ${SERVICE_URL}/api/setup-webhook"
fi
echo "🔄 Updating Cloud Run environment variables (SERVICE_URL) ..."
gcloud run services update ${SERVICE_NAME} --region ${REGION} --update-env-vars SERVICE_URL=${SERVICE_URL} || true
echo "⚠️  Don't forget to set Telegram webhook!"
echo "   Use: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=${SERVICE_URL}/webhook/telegram"
echo "========================================="
