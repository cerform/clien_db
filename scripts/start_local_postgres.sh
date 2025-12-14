#!/bin/bash
set -e

# Start local Postgres container for development and migrations
CONTAINER_NAME=${CONTAINER_NAME:-tattoo-postgres}
DB_USER=${CLOUDSQL_USER:-tattoo_user}
DB_PASS=${CLOUDSQL_PASSWORD:-strong_password_here}
DB_NAME=${CLOUDSQL_DB:-tattoo_salon}
DB_PORT=${CLOUDSQL_PORT:-5432}

# Check if already running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Container ${CONTAINER_NAME} already running"
  exit 0
fi

# Remove any exited container
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Removing existing container ${CONTAINER_NAME}"
  docker rm -f ${CONTAINER_NAME} || true
fi

# Run postgres
echo "Starting Postgres container ${CONTAINER_NAME}..."
docker run --name ${CONTAINER_NAME} -e POSTGRES_USER=${DB_USER} -e POSTGRES_PASSWORD=${DB_PASS} -e POSTGRES_DB=${DB_NAME} -p ${DB_PORT}:5432 -d postgres:15

# Wait for postgres to be ready
echo "Waiting for Postgres to be ready..."
until docker exec ${CONTAINER_NAME} pg_isready -U ${DB_USER} >/dev/null 2>&1; do
  sleep 1
done

echo "Postgres ${CONTAINER_NAME} started and ready (user=${DB_USER}, db=${DB_NAME})"

