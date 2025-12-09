#!/usr/bin/env bash
set -euo pipefail

# Deploys container image to Google Cloud Run using gcloud.
# Requires: gcloud CLI installed, active service account or google-cloud-auth.

if [[ "$#" -lt 1 ]]; then
  echo "Usage: $0 <service-name> [image-tag]"
  echo "Environment variables required: PROJECT_ID, REGION"
  exit 1
fi

SERVICE_NAME=$1
IMAGE_TAG=${2:-"$GITHUB_SHA"}

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}
REGION=${REGION:-us-central1}
CONTAINER_REGISTRY=${CONTAINER_REGISTRY:-gcr.io}

if [[ -z "$PROJECT_ID" ]]; then
  echo "PROJECT_ID is not set. Set env var PROJECT_ID or run 'gcloud config set project <id>'."
  exit 1
fi

IMAGE_NAME=${CONTAINER_REGISTRY}/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}

echo "Building container: $IMAGE_NAME"
gcloud builds submit --tag $IMAGE_NAME

echo "Deploying to Cloud Run: service=${SERVICE_NAME}, region=${REGION}, image=${IMAGE_NAME}"
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --project $PROJECT_ID \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated || true

echo "Deployment finished"
