#!/bin/bash
# Deploy Tattoo Bot to Google Cloud Run with Cloud SQL (Postgres)

set -e

# Configuration (customize these values)
PROJECT_ID="tattoo-480007"
REGION="us-central1"
SERVICE_NAME="tattoo-bot"
CLOUDSQL_INSTANCE="tattoo-db"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
DB_NAME="tattoo_salon"
DB_USER="tattoo_user"
SERVICE_ACCOUNT_NAME="${SERVICE_NAME}"
ADMIN_IDS="438407739,457343487"

echo "========================================="
echo "🚀 Deploying Tattoo Bot to Cloud Run (Postgres)"
echo "========================================="

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
if command -v python3 &>/dev/null; then
    echo "🔍 Running pre-deploy checks..."
    python3 ./scripts/predeploy_check.py || { echo "Predeploy checks failed"; exit 2; }
else
    echo "⚠️ Python3 not found in PATH; skipping pre-deploy script checks"
fi
gcloud builds submit --tag ${IMAGE_NAME}

# Create Cloud SQL instance (Postgres) if not exists
echo "🗄️  Checking Cloud SQL instance..."
if ! gcloud sql instances describe ${CLOUDSQL_INSTANCE} --project=${PROJECT_ID} &> /dev/null; then
    echo "⚠️  Cloud SQL instance not found. Creating..."
    # Adjust machine size as needed
    gcloud sql instances create ${CLOUDSQL_INSTANCE} \
        --database-version=POSTGRES_15 \
        --tier=db-custom-1-3840 \
        --region=${REGION}

    echo "✅ Cloud SQL instance created"

    # Create database
    echo "📦 Creating database ${DB_NAME}..."
    gcloud sql databases create ${DB_NAME} --instance=${CLOUDSQL_INSTANCE}
else
    echo "✅ Cloud SQL instance exists"
fi

# Get Cloud SQL connection name
CLOUDSQL_CONNECTION_NAME=$(gcloud sql instances describe ${CLOUDSQL_INSTANCE} --project=${PROJECT_ID} --format='value(connectionName)')
echo "🔗 Cloud SQL Connection: ${CLOUDSQL_CONNECTION_NAME}"

echo "🔐 NOTE: Create or update secrets for BOT_TOKEN, OPENAI_API_KEY, CLOUDSQL_PASSWORD in Secret Manager before continuing."

# Ensure service account and IAM roles are in place
echo "🔧 Ensuring service account and IAM roles are configured"
if [ ! -f ./scripts/setup_service_account.sh ]; then
    echo "⚠️ scripts/setup_service_account.sh not found, skipping service account setup."
else
    ./scripts/setup_service_account.sh ${PROJECT_ID} ${SERVICE_ACCOUNT_NAME}
fi
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant Secret Manager access to service account
echo "🔐 Granting Secret Manager access to service account: ${SERVICE_ACCOUNT_EMAIL}"
for SECRET_NAME in BOT_TOKEN OPENAI_API_KEY CLOUDSQL_PASSWORD SPREADSHEET_ID DATABASE_URL; do
    if gcloud secrets describe ${SECRET_NAME} --project=${PROJECT_ID} &> /dev/null; then
        gcloud secrets add-iam-policy-binding ${SECRET_NAME} \
            --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
            --role="roles/secretmanager.secretAccessor" --project=${PROJECT_ID} || true
    fi
done

# Check for secrets and optionally create/update them from .env
SECRETS_TO_SET=""
if [ -f .env ]; then
    echo "📝 Reading .env file..."
    set -o allexport
    source .env
    set +o allexport
fi

for SECRET_NAME in BOT_TOKEN OPENAI_API_KEY CLOUDSQL_PASSWORD SPREADSHEET_ID; do
    SECRET_VALUE="${!SECRET_NAME:-}"
    if [ -n "${SECRET_VALUE}" ]; then
        if ! gcloud secrets describe $SECRET_NAME --project=${PROJECT_ID} &> /dev/null; then
            echo "Creating secret: $SECRET_NAME"
            echo -n "$SECRET_VALUE" | gcloud secrets create $SECRET_NAME --replication-policy="automatic" --data-file=- --project=${PROJECT_ID}
        else
            echo "Updating secret: $SECRET_NAME"
            echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME --data-file=- --project=${PROJECT_ID}
        fi
        SECRETS_TO_SET="${SECRETS_TO_SET}${SECRET_NAME}=:${SECRET_NAME},"
    else
        echo "⚠️ Secret ${SECRET_NAME} not set in .env; ensure it exists in Secret Manager or set it before deployment."
    fi
done

# Decide BOT_MODE and memory based on presence of OPENAI_API_KEY
if [ -n "${OPENAI_API_KEY}" ]; then
    BOT_MODE=advanced
    MEM=1Gi
    echo "🔧 Detected OPENAI_API_KEY in .env. Enabling AI mode (BOT_MODE=advanced) and setting memory to ${MEM}"
else
    if gcloud secrets describe OPENAI_API_KEY --project=${PROJECT_ID} &> /dev/null; then
        OPENAI_SECRET_VALUE=$(gcloud secrets versions access latest --secret=OPENAI_API_KEY --project=${PROJECT_ID} 2>/dev/null || true)
        if [ -n "${OPENAI_SECRET_VALUE}" ]; then
            BOT_MODE=advanced
            MEM=1Gi
            echo "🔧 Found OPENAI_API_KEY in Secret Manager. Enabling AI mode (BOT_MODE=advanced) and setting memory to ${MEM}"
        else
            BOT_MODE=inka
            MEM=512Mi
            echo "🔧 OpenAI secret exists but empty. Using INKA-only (BOT_MODE=inka) and memory ${MEM}"
        fi
    else
        BOT_MODE=inka
        MEM=512Mi
        echo "🔧 No OpenAI key found. Using INKA-only mode (BOT_MODE=inka) and memory ${MEM}"
    fi
fi

# Optional: store DATABASE_URL as a secret (unix socket format) to ensure init_postgres runs
read -p "Create secret DATABASE_URL from DB credentials now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Please enter DB password (it will not be echoed):"
    read -s DB_PASSWORD
    echo
    DATABASE_URL="postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CLOUDSQL_CONNECTION_NAME}"
    echo -n "${DATABASE_URL}" | gcloud secrets create DATABASE_URL --replication-policy="automatic" --data-file=- --project=${PROJECT_ID} || \
        echo -n "${DATABASE_URL}" | gcloud secrets versions add DATABASE_URL --data-file=- --project=${PROJECT_ID}
fi

# Apply SQL migrations and RBAC to the target database if user agrees
read -p "Apply SQL migrations now? (recommended) (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Applying migrations..."
    # Export DATABASE_URL for the migration scripts
    export DATABASE_URL
    python3 scripts/apply_sql_migrations.py --apply || { echo "Migrations failed"; exit 1; }
fi

read -p "Create RBAC roles now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating RBAC roles..."
    export DATABASE_URL
    python3 scripts/create_rbac_roles.py --apply || { echo "RBAC update failed"; exit 1; }
fi

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
    --set-env-vars "CLOUD_RUN_ENV=true,DB_SOCKET_DIR=/cloudsql,CLOUDSQL_CONNECTION_NAME=${CLOUDSQL_CONNECTION_NAME},CLOUDSQL_DB=${DB_NAME},CLOUDSQL_USER=${DB_USER},ADMIN_USER_IDS=${ADMIN_IDS},BOT_MODE=${BOT_MODE}" \
    --set-secrets "BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,CLOUDSQL_PASSWORD=CLOUDSQL_PASSWORD:latest,DATABASE_URL=DATABASE_URL:latest" \
    --service-account ${SERVICE_ACCOUNT_EMAIL}

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo "🌐 Service URL: ${SERVICE_URL}"
echo "🗄️  Cloud SQL: ${CLOUDSQL_CONNECTION_NAME}"
echo "📋 Next steps:"
echo "1. Ensure secrets are set in Secret Manager for BOT_TOKEN, OPENAI_API_KEY, CLOUDSQL_PASSWORD (and DATABASE_URL if used)."
echo "2. Setup webhook: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=${SERVICE_URL}/webhook/telegram"
echo "3. Check logs: gcloud run logs read --service=${SERVICE_NAME} --region=${REGION}"
echo "========================================="

echo "🔄 Updating Cloud Run environment variables (SERVICE_URL) ..."
gcloud run services update ${SERVICE_NAME} --region ${REGION} --update-env-vars SERVICE_URL=${SERVICE_URL} || true

echo "📨 Auto-configuring webhook via /api/setup-webhook..."
if command -v curl &> /dev/null ; then
    sleep 5
    SETUP_RESULT=$(curl -s -X POST "${SERVICE_URL}/api/setup-webhook" -H "Content-Type: application/json" || true)
    echo "Webhook setup response: ${SETUP_RESULT}"
else
    echo "⚠️ curl not found: cannot call /api/setup-webhook. You can do it manually: curl -X POST ${SERVICE_URL}/api/setup-webhook"
fi
