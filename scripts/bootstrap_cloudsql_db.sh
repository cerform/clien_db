#!/usr/bin/env bash
set -euo pipefail

# Bootstraps Cloud SQL database by setting password for `tattoo_user` and running schema migrations
# Usage:
#   CLOUDSQL_PASSWORD=secret ./scripts/bootstrap_cloudsql_db.sh tattoo-db tattoo-salon tattoo_user [--start-proxy]

INSTANCE=${1:-tattoo-db}
DB_NAME=${2:-tattoo_salon}
DB_USER=${3:-tattoo_user}
START_PROXY=${4:---start-proxy}

PROJECT_ID=${PROJECT_ID:-tattoo-480007}

PASSWORD=${CLOUDSQL_PASSWORD:-}
if [ -z "$PASSWORD" ]; then
  read -s -p "Enter password for $DB_USER (will be set on Cloud SQL): " PASSWORD
  echo
fi

# Set the SQL user password
echo "Setting password for Cloud SQL user $DB_USER on instance $INSTANCE"
gcloud sql users set-password "$DB_USER" --instance="$INSTANCE" --password="$PASSWORD" --project="$PROJECT_ID" || { echo "Failed to set password"; exit 1; }

# Start a Cloud SQL Proxy to connect locally (if required)
if [ "$START_PROXY" = "--start-proxy" ]; then
  PORT=${LOCAL_POSTGRES_PORT:-5432}
  echo "Starting Cloud SQL Proxy for instance $INSTANCE on port $PORT"
  ./cloud_sql_proxy -instances=${PROJECT_ID}:us-central1:${INSTANCE}=tcp:${PORT} > /dev/null 2>&1 &
  PROXY_PID=$!
  trap "kill $PROXY_PID" EXIT
  sleep 3
fi

# Now run migrations against the proxy
export DATABASE_URL="postgresql://$DB_USER:$PASSWORD@localhost:${LOCAL_POSTGRES_PORT:-5432}/$DB_NAME"
export CLOUDSQL_HOST=127.0.0.1
export CLOUDSQL_PORT=${LOCAL_POSTGRES_PORT:-5432}
python3 scripts/migrate_all_to_postgres.py

# If we started proxy, it will be killed by trap on exit

echo "Cloud SQL bootstrap completed. Tables should now exist in $DB_NAME on instance $INSTANCE." 
echo "You may want to revoke the password change or rotate it after migration if necessary."