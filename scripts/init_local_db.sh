#!/bin/bash
set -e

# Helper script to start Cloud SQL Proxy and initialize DB schema for local dev
# Usage: ./scripts/init_local_db.sh [--start-proxy-only]

PROXY_INSTANCES=${CLOUDSQL_CONNECTION_NAME:-"tattoo-480007:us-central1:tattoo-db"}
PROXY_HOST=${CLOUDSQL_HOST:-localhost}
PROXY_PORT=${CLOUDSQL_PORT:-5432}
LOCAL_POSTGRES_PORT=${LOCAL_POSTGRES_PORT:-5433}

# Load environment variables from .env if present
if [ -f .env ]; then
  echo "Loading .env variables"
  set -a
  source .env
  set +a
fi
DB_USER=${CLOUDSQL_USER:-tattoo_user}
DB_PASS=${CLOUDSQL_PASSWORD:-}
DB_NAME=${CLOUDSQL_DB:-tattoo_salon}

function start_proxy() {
  if pgrep -f "cloud_sql_proxy.*${PROXY_INSTANCES}" > /dev/null; then
    echo "Cloud SQL Proxy already running"
  else
    echo "Starting Cloud SQL Proxy..."
    ./cloud_sql_proxy -instances=${PROXY_INSTANCES}=tcp:${PROXY_PORT} > /dev/null 2>&1 &
    PROXY_PID=$!
    sleep 3
    echo "Cloud SQL Proxy started (pid=${PROXY_PID})"
  fi
}

function start_local_postgres() {
  scripts/start_local_postgres.sh
}

function run_migrations() {
  if [ -z "$DB_PASS" ]; then
    echo "CLOUDSQL_PASSWORD is empty; please set in .env or export it before running this script"
    exit 1
  fi
  export DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@${PROXY_HOST}:${PROXY_PORT}/${DB_NAME}"
  echo "Running PostgreSQL migration script using DATABASE_URL=$DATABASE_URL"
  python3 scripts/migrate_all_to_postgres.py
}

# Main
if [ "$1" == "--start-proxy-only" ]; then
  start_proxy
  exit 0
fi

if [ "$1" == "--local" ]; then
  echo "Using local Postgres container for migrations"
  # ensure start_local_postgres sees the desired port
  export CLOUDSQL_PORT=${LOCAL_POSTGRES_PORT}
  start_local_postgres
  # If Docker is used, extract credentials from the container if available
  if docker ps --format '{{.Names}}' | grep -q "^tattoo-postgres$"; then
    POSTGRES_USER=$(docker inspect tattoo-postgres --format='{{range $k,$v := .Config.Env}}{{println $v}}{{end}}' | grep '^POSTGRES_USER=' | cut -d'=' -f2)
    POSTGRES_PASSWORD=$(docker inspect tattoo-postgres --format='{{range $k,$v := .Config.Env}}{{println $v}}{{end}}' | grep '^POSTGRES_PASSWORD=' | cut -d'=' -f2)
    POSTGRES_DB=$(docker inspect tattoo-postgres --format='{{range $k,$v := .Config.Env}}{{println $v}}{{end}}' | grep '^POSTGRES_DB=' | cut -d'=' -f2)
    # Fallback if inspect didn't return values
    DB_USER=${POSTGRES_USER:-$DB_USER}
    DB_PASS=${POSTGRES_PASSWORD:-$DB_PASS}
    DB_NAME=${POSTGRES_DB:-$DB_NAME}
  fi
  # override proxy host and port to local postgres
  PROXY_HOST=localhost
  PROXY_PORT=${LOCAL_POSTGRES_PORT}
  export CLOUDSQL_HOST=${PROXY_HOST}
  export CLOUDSQL_PORT=${PROXY_PORT}
  export DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@${PROXY_HOST}:${PROXY_PORT}/${DB_NAME}"
  run_migrations
else
  start_proxy
  run_migrations
fi

echo "Initialization complete"
