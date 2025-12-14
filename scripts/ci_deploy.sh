#!/usr/bin/env bash
set -euo pipefail

# Script for CI to deploy using installer in non-interactive mode
# Expected environment variables (set in Jenkins):
# - GCP_PROJECT_ID
# - GCP_REGION
# - CLOUD_RUN_SERVICE
# - DOCKER_IMAGE
# - TELEGRAM_TOKEN (jenkins secret text)
# - LLM_API_KEY (jenkins secret text)
# - GCP_SA_FILE (jenkins credentials file path)
# - DRY_RUN (true/false)

PROJECT_ID=${GCP_PROJECT_ID:-}
REGION=${GCP_REGION:-europe-west1}
SERVICE=${CLOUD_RUN_SERVICE:-inka-bot}
IMAGE=${DOCKER_IMAGE:-gcr.io/${PROJECT_ID}/${SERVICE}:latest}
SCAN=${SCAN:-false}
REPORT_DIR=${REPORT_DIR:-reports}
SA_FILE=${GCP_SA_FILE:-/tmp/gcp_sa.json}
DRY_RUN=${DRY_RUN:-true}

mkdir -p "$REPORT_DIR"

if [[ -z "$PROJECT_ID" || -z "$TELEGRAM_TOKEN" ]]; then
  echo "Missing GCP_PROJECT_ID or TELEGRAM_TOKEN"
  exit 1
fi

# Authenticate with service account
if [[ -f "$SA_FILE" ]]; then
  gcloud auth activate-service-account --key-file="$SA_FILE"
else
  echo "Service account file not found: $SA_FILE"
  exit 1
fi

# Configure docker auth for gcr
gcloud auth configure-docker --quiet

# Optionally configure project
gcloud config set project "$PROJECT_ID"

echo "Running installer with dry_run=$DRY_RUN"
if [[ "$DRY_RUN" == "true" ]]; then
  python tools/install_and_deploy.py --project "$PROJECT_ID" --region "$REGION" --service "$SERVICE" --docker-image "$IMAGE" --sa-name "${SERVICE}-sa" --telegram-token "$TELEGRAM_TOKEN" --llm-api-key "$LLM_API_KEY" --set-webhook --dry-run
else
  python tools/install_and_deploy.py --project "$PROJECT_ID" --region "$REGION" --service "$SERVICE" --docker-image "$IMAGE" --sa-name "${SERVICE}-sa" --telegram-token "$TELEGRAM_TOKEN" --llm-api-key "$LLM_API_KEY" --set-webhook
fi

# Fetch deployed URL and print
if [[ "$DRY_RUN" == "false" ]]; then
  URL=$(gcloud run services describe $SERVICE --region $REGION --format="value(status.url)" --project $PROJECT_ID)
  echo "SERVICE_URL=${URL}"
  echo "SERVICE_URL=${URL}" > service_url.txt
  # Write to the reports directory for Jenkins artifact collection
  mkdir -p "$REPORT_DIR"
  echo "SERVICE_URL=${URL}" > "$REPORT_DIR/service_url.txt"
fi

if [[ "$SCAN" == "true" ]]; then
  echo "Running Trivy scan for image: $IMAGE"
  # Ensure we have docker auth / can pull the image
  docker pull "$IMAGE" || true
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "$REPORT_DIR":/reports aquasec/trivy:latest image --format json -o /reports/trivy.json "$IMAGE" || true
  echo "Trivy scan complete. Report written to $REPORT_DIR/trivy.json"
fi
