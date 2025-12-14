#!/usr/bin/env bash
set -euo pipefail

# deploy_staging.sh
# Usage: fill required env vars below or export them beforehand.
# Example:
# PROJECT=tattoo-480007 REGION=us-central1 REPO=inka-repo SERVICE_ACCOUNT=inka-sa CLOUDSQL_INSTANCE=project:region:instance ./scripts/deploy_staging.sh

: "${PROJECT:?Need to set PROJECT (gcloud project id)}"
: "${REGION:=us-central1}"
: "${REPO:?Need to set REPO (Artifact Registry repo name)}"
: "${SERVICE_ACCOUNT:?Need to set SERVICE_ACCOUNT (service account email without @project)}"
: "${IMAGE_TAG:=staging}"
: "${CLOUDSQL_INSTANCE:?Need to set CLOUDSQL_INSTANCE (project:region:instance)}"
: "${ENABLE_LLM:=true}"

IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}/inka:${IMAGE_TAG}"

echo "Project: $PROJECT"
echo "Region: $REGION"
echo "Image: $IMAGE"

# Ensure artifact registry API
gcloud services enable artifactregistry.googleapis.com --project="$PROJECT"

# Authenticate docker
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --project="$PROJECT"

# Build image
echo "Building docker image..."
docker build -t "$IMAGE" -f Dockerfile .

# Push
echo "Pushing image to Artifact Registry..."
docker push "$IMAGE"

# Grant service account access to secrets should be done outside this script.
# Deploy to Cloud Run
SERVICE_NAME="inka-staging"

echo "Deploying to Cloud Run as ${SERVICE_NAME}"

gcloud run deploy "$SERVICE_NAME" \
  --image="$IMAGE" \
  --platform=managed \
  --region="$REGION" \
  --service-account="${SERVICE_ACCOUNT}@${PROJECT}.iam.gserviceaccount.com" \
  --set-env-vars ENABLE_LLM=${ENABLE_LLM},ENV=staging \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=5 \
  --concurrency=80 \
  --add-cloudsql-instances="${CLOUDSQL_INSTANCE}" \
  --quiet

URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --platform=managed --format="value(status.url)")

echo "Deployed. Service URL: $URL"

echo "Tip: tail logs with: gcloud run services logs read ${SERVICE_NAME} --region=${REGION} --project=${PROJECT} --limit=100"

exit 0
