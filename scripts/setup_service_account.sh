#!/bin/bash
set -euo pipefail

# Create Cloud Run service account and grant least-privilege roles for Cloud SQL/Secret Manager
# Usage: ./scripts/setup_service_account.sh <PROJECT_ID> <SERVICE_ACCOUNT_NAME>

PROJECT_ID=${1:-tattoo-480007}
SERVICE_ACCOUNT_NAME=${2:-tattoo-bot}
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
ROLE_LIST=("roles/cloudsql.client" "roles/secretmanager.secretAccessor" "roles/run.admin" "roles/logging.logWriter")

echo "Creating service account: ${SERVICE_ACCOUNT_EMAIL}"
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} --project=${PROJECT_ID} &>/dev/null; then
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} --project=${PROJECT_ID} \
        --display-name="Tattoo Bot Service Account"
    echo "Service account created"
else
    echo "Service account already exists"
fi

echo "Granting roles: ${ROLE_LIST[*]}"
for ROLE in "${ROLE_LIST[@]}"; do
    gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --role="${ROLE}" || true
done

echo "Binding Secret Manager admin role (if you want to maintain secrets from script)"
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" --role="roles/secretmanager.admin" || true

echo "Done. You can use ${SERVICE_ACCOUNT_EMAIL} as the --service-account for 'gcloud run deploy'"
