#!/usr/bin/env bash
# Upload an SQL migration file to GCS and import it into Cloud SQL using gcloud
# Usage: ./scripts/migrate_cloudsql.sh <CLOUDSQL_INSTANCE> <GCS_BUCKET> [sql_file] [database]
# Example: ./scripts/migrate_cloudsql.sh tattoo-bot-db my-bucket db/migrations/001_create_admins.sql admin_messages
set -euo pipefail

INSTANCE=${1:-}
BUCKET=${2:-}
SQL_FILE=${3:-db/migrations/001_create_admins.sql}
DB_NAME=${4:-${CLOUDSQL_DB:-admin_messages}}

if [[ -z "$INSTANCE" || -z "$BUCKET" ]]; then
  echo "Usage: $0 <CLOUDSQL_INSTANCE> <GCS_BUCKET> [sql_file] [database]"
  exit 2
fi

if [[ ! -f "$SQL_FILE" ]]; then
  echo "SQL file not found: $SQL_FILE"
  exit 3
fi

OBJECT_PATH="migrations/$(basename $SQL_FILE)"

echo "Uploading $SQL_FILE to gs://$BUCKET/$OBJECT_PATH ..."
gsutil cp "$SQL_FILE" "gs://$BUCKET/$OBJECT_PATH"

echo "Starting import into Cloud SQL instance $INSTANCE (database: $DB_NAME) ..."
# Use gcloud sql import sql command. This requires the file to be in GCS and the instance to be a Cloud SQL instance.
# Note: The import operation runs asynchronously; export/import status can be checked with gcloud sql operations list/get
gcloud sql import sql "$INSTANCE" "gs://$BUCKET/$OBJECT_PATH" --database="$DB_NAME" --quiet

if [[ $? -eq 0 ]]; then
  echo "Import requested successfully. Use 'gcloud sql operations list' to follow progress." 
else
  echo "Import failed. Check gcloud logs and verify permissions: service account for Cloud SQL should have object access to the bucket." >&2
  exit 4
fi
