#!/bin/bash
set -e
# Deploy multiple services to Cloud Run: backend, bot, ai, frontend

# Config (customize project/region)
PROJECT_ID=${PROJECT_ID:-tattoo-480007}
REGION=${REGION:-us-central1}
IMAGE_PREFIX=gcr.io/${PROJECT_ID}

SERVICES=(backend bot ai frontend)

echo "Deploying to GCP project: ${PROJECT_ID}, region: ${REGION}"
gcloud config set project ${PROJECT_ID}

# Enable APIs
gcloud services enable run.googleapis.com sqladmin.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com --project=${PROJECT_ID}

# Optional: create Cloud SQL instance if not existing
CLOUDSQL_INSTANCE=${CLOUDSQL_INSTANCE:-tattoo-db}
CLOUDSQL_DB=${CLOUDSQL_DB:-tattoo_salon}
CLOUDSQL_USER=${CLOUDSQL_USER:-tattoo_user}

if ! gcloud sql instances describe ${CLOUDSQL_INSTANCE} --project=${PROJECT_ID} &> /dev/null; then
  echo "Creating Cloud SQL instance ${CLOUDSQL_INSTANCE}..."
  gcloud sql instances create ${CLOUDSQL_INSTANCE} --database-version=POSTGRES_15 --region=${REGION} --project=${PROJECT_ID}
  gcloud sql databases create ${CLOUDSQL_DB} --instance=${CLOUDSQL_INSTANCE} --project=${PROJECT_ID}
fi
CLOUDSQL_CONNECTION_NAME=$(gcloud sql instances describe ${CLOUDSQL_INSTANCE} --project=${PROJECT_ID} --format='value(connectionName)')
echo "Cloud SQL Connection: ${CLOUDSQL_CONNECTION_NAME}"

# Create service accounts and add roles for each service
for SVC in ${SERVICES[@]}; do
  SA=tattoo-${SVC}-sa
  SA_EMAIL=${SA}@${PROJECT_ID}.iam.gserviceaccount.com
  if ! gcloud iam service-accounts describe ${SA_EMAIL} --project=${PROJECT_ID} &> /dev/null; then
    gcloud iam service-accounts create ${SA} --display-name="${SVC} service account" --project=${PROJECT_ID}
  fi
  # Grant basic roles to allow Cloud Run to run and access secretmanager and cloudsql
  gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/run.invoker" --project=${PROJECT_ID} || true
  gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/secretmanager.secretAccessor" --project=${PROJECT_ID} || true
  # Cloud SQL client role only for services that need DB
  # Attach cloudsql role for services that need DB access
  if [[ ${SVC} != "frontend" ]]; then
    gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SA_EMAIL}" --role="roles/cloudsql.client" --project=${PROJECT_ID} || true
  fi
done

# Ensure required secrets exist (BOT_TOKEN, OPENAI_API_KEY, CLOUDSQL_PASSWORD, SPREADSHEET_ID)
for SECRET_NAME in BOT_TOKEN OPENAI_API_KEY CLOUDSQL_PASSWORD SPREADSHEET_ID DATABASE_URL; do
  if ! gcloud secrets describe ${SECRET_NAME} --project=${PROJECT_ID} &> /dev/null; then
    # Create secrets if provided in .env
    if [ -f .env ]; then
      SECRET_VALUE=$(grep -E "^${SECRET_NAME}=" .env | sed -e 's/^${SECRET_NAME}=//') || true
      if [ -n "${SECRET_VALUE}" ]; then
        echo -n "${SECRET_VALUE}" | gcloud secrets create ${SECRET_NAME} --replication-policy="automatic" --data-file=- --project=${PROJECT_ID} || true
      else
        echo "Secret ${SECRET_NAME} not found and no value in .env; create it in Secret Manager or set it in .env" || true
      fi
    else
      echo "Secret ${SECRET_NAME} not found. You must create it in Secret Manager or provide in .env" || true
    fi
  fi
done

# Build images per service and deploy
for SVC in ${SERVICES[@]}; do
  IMAGE=${IMAGE_PREFIX}/${SVC}
  echo "Building ${SVC} image -> ${IMAGE}"
  case ${SVC} in
    backend)
      gcloud builds submit --tag ${IMAGE} --project=${PROJECT_ID}
      echo "Deploying backend..."
      gcloud run deploy tattoo-backend --image ${IMAGE} --region=${REGION} --platform=managed --memory=512Mi --allow-unauthenticated --service-account=backend-sa@${PROJECT_ID}.iam.gserviceaccount.com --set-env-vars CLOUD_RUN_ENV=true,DB_SOCKET_DIR=/cloudsql,CLOUDSQL_CONNECTION_NAME=${CLOUDSQL_CONNECTION_NAME},CLOUDSQL_DB=${CLOUDSQL_DB},CLOUDSQL_USER=${CLOUDSQL_USER},SPREADSHEET_ID=SPREADSHEET_ID,OPENAI_API_KEY=OPENAI_API_KEY --set-secrets SPREADSHEET_ID=SPREADSHEET_ID:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest --add-cloudsql-instances ${CLOUDSQL_CONNECTION_NAME} --project=${PROJECT_ID}
      ;;
    bot)
      gcloud builds submit --tag ${IMAGE} --project=${PROJECT_ID}
      echo "Deploying bot..."
      gcloud run deploy tattoo-bot --image ${IMAGE} --region=${REGION} --platform=managed --memory=512Mi --allow-unauthenticated --service-account=bot-sa@${PROJECT_ID}.iam.gserviceaccount.com --set-env-vars CLOUD_RUN_ENV=true,DB_SOCKET_DIR=/cloudsql,CLOUDSQL_CONNECTION_NAME=${CLOUDSQL_CONNECTION_NAME},CLOUDSQL_DB=${CLOUDSQL_DB},CLOUDSQL_USER=${CLOUDSQL_USER},SPREADSHEET_ID=SPREADSHEET_ID,ADMIN_USER_IDS=${ADMIN_USER_IDS} --set-secrets BOT_TOKEN=BOT_TOKEN:latest,CLOUDSQL_PASSWORD=CLOUDSQL_PASSWORD:latest,SPREADSHEET_ID=SPREADSHEET_ID:latest,DATABASE_URL=DATABASE_URL:latest --add-cloudsql-instances ${CLOUDSQL_CONNECTION_NAME} --project=${PROJECT_ID}
      ;;
    ai)
      gcloud builds submit --tag ${IMAGE} --project=${PROJECT_ID}
      echo "Deploying ai..."
      gcloud run deploy tattoo-ai --image ${IMAGE} --region=${REGION} --platform=managed --memory=512Mi --allow-unauthenticated --service-account=ai-sa@${PROJECT_ID}.iam.gserviceaccount.com --set-env-vars OPENAI_API_KEY=OPENAI_API_KEY,SPREADSHEET_ID=SPREADSHEET_ID --set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest,SPREADSHEET_ID=SPREADSHEET_ID:latest,DATABASE_URL=DATABASE_URL:latest --add-cloudsql-instances ${CLOUDSQL_CONNECTION_NAME} --project=${PROJECT_ID}
      ;;
    frontend)
      gcloud builds submit --tag ${IMAGE} --project=${PROJECT_ID} --pack=image=${IMAGE}
      echo "Deploying frontend..."
      gcloud run deploy tattoo-frontend --image ${IMAGE} --region=${REGION} --platform=managed --memory=128Mi --allow-unauthenticated --service-account=frontend-sa@${PROJECT_ID}.iam.gserviceaccount.com --project=${PROJECT_ID}
      ;;
    *)
      echo "Unknown service: ${SVC}";
  esac
done

echo "All services deployed"
echo "Backend URL: " $(gcloud run services describe tattoo-backend --format='value(status.url)' --region=${REGION} --project=${PROJECT_ID})
echo "Bot URL: " $(gcloud run services describe tattoo-bot --format='value(status.url)' --region=${REGION} --project=${PROJECT_ID})
echo "AI URL: " $(gcloud run services describe tattoo-ai --format='value(status.url)' --region=${REGION} --project=${PROJECT_ID})
echo "Frontend URL: " $(gcloud run services describe tattoo-frontend --format='value(status.url)' --region=${REGION} --project=${PROJECT_ID})

echo "⚠️ Remember to set webhook for Telegram bot using BOT_TOKEN and the bot's Service URL"
echo "curl -X POST \"https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=$(gcloud run services describe tattoo-bot --format='value(status.url)' --region=${REGION} --project=${PROJECT_ID})/webhook/telegram\""
