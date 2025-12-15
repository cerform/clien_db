#!/usr/bin/env bash
set -euo pipefail
# Helper to import values from .env into Google Secret Manager.
# Usage: ./scripts/import_env_to_secrets.sh [--dry-run]

DRY_RUN=false
if [[ ${1:-} == "--dry-run" ]]; then
  DRY_RUN=true
fi

PROJECT=$(gcloud config get-value project 2>/dev/null || true)
if [[ -z "$PROJECT" ]]; then
  echo "ERROR: gcloud project not set. Run 'gcloud config set project <project-id>'" >&2
  exit 1
fi

ENV_FILE=.env
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Create it from .env.example with real secret values." >&2
  exit 1
fi

declare -a KEYS=("TELEGRAM_BOT_TOKEN" "OPENAI_API_KEY" "CLOUDSQL_PASSWORD" "SPREADSHEET_ID" "WEBHOOK_SECRET" "BOT_TOKEN")

echo "Importing secrets from $ENV_FILE into project $PROJECT (dry-run=$DRY_RUN)"

for key in "${KEYS[@]}"; do
  value=$(grep -E "^${key}=" "$ENV_FILE" || true)
  if [[ -z "$value" ]]; then
    echo " - $key: not present in $ENV_FILE, skipping"
    continue
  fi
  # value after '='
  secret_value=$(printf "%s" "$value" | sed -E "s/^${key}=(.*)$/\1/")
  if [[ "$secret_value" == "REPLACE_ME" || -z "$secret_value" ]]; then
    echo " - $key: placeholder or empty, skipping"
    continue
  fi

  # Sanitize name for Secret Manager
  secret_name=$(echo "$key" | tr '[:upper:]' '[:lower:]')

  if $DRY_RUN; then
    echo "DRY: would import $key -> secret ${secret_name}"
    continue
  fi

  # Create secret if it doesn't exist
  if ! gcloud secrets describe "$secret_name" --project="$PROJECT" >/dev/null 2>&1; then
    echo "Creating secret: $secret_name"
    echo -n "$secret_value" | gcloud secrets create "$secret_name" --data-file=- --replication-policy="automatic" --project="$PROJECT"
  else
    echo "Adding new version to secret: $secret_name"
    echo -n "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=- --project="$PROJECT"
  fi

  echo "Granting access to service account: inka-sa@${PROJECT}.iam.gserviceaccount.com"
  gcloud secrets add-iam-policy-binding "$secret_name" \
    --member="serviceAccount:inka-sa@${PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --project="$PROJECT" || true
done

echo "Import complete. Verify secrets in Secret Manager and rotate keys where necessary."
