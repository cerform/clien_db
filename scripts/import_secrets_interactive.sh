#!/bin/bash
set -euo pipefail

# Interactive secrets creation helper
# Prompts for secrets (BOT_TOKEN, OPENAI_API_KEY, CLOUDSQL_PASSWORD, SPREADSHEET_ID) and stores them in Google Secret Manager

PROJECT_ID=${PROJECT_ID:-tattoo-480007}

read -p "Enter Telegram BOT_TOKEN: " BOT_TOKEN
read -p "Enter OpenAI API KEY: " OPENAI_API_KEY
read -p "Enter Cloud SQL DB password (for tattoo_user): " -s CLOUDSQL_PASSWORD
echo
read -p "Enter SPREADSHEET_ID (optional): " SPREADSHEET_ID

function create_or_update() {
  name=$1
  value=$2
  if gcloud secrets describe ${name} --project=${PROJECT_ID} &>/dev/null; then
    echo "Updating secret ${name}"
    echo -n "${value}" | gcloud secrets versions add ${name} --data-file=- --project=${PROJECT_ID}
  else
    echo "Creating secret ${name}"
    echo -n "${value}" | gcloud secrets create ${name} --replication-policy="automatic" --data-file=- --project=${PROJECT_ID}
  fi
}

create_or_update BOT_TOKEN "${BOT_TOKEN}"
create_or_update OPENAI_API_KEY "${OPENAI_API_KEY}"
create_or_update CLOUDSQL_PASSWORD "${CLOUDSQL_PASSWORD}"
if [ -n "${SPREADSHEET_ID}" ]; then
  create_or_update SPREADSHEET_ID "${SPREADSHEET_ID}"
fi

echo "All requested secrets created or updated in project ${PROJECT_ID}"
