#!/usr/bin/env bash
set -euo pipefail

# Simple script to run a local Postgres container for migration and testing
CONTAINER_NAME=clien_db_pg
PG_USER=pguser
PG_PASS=pass
PG_DB=clien_db
PG_PORT=${PG_PORT:-5432}

docker run --rm --name ${CONTAINER_NAME} -e POSTGRES_PASSWORD=${PG_PASS} -e POSTGRES_USER=${PG_USER} -e POSTGRES_DB=${PG_DB} -p ${PG_PORT}:5432 -d postgres:15

echo "Started Postgres container: ${CONTAINER_NAME}"
echo "DATABASE_URL=postgresql+psycopg2://${PG_USER}:${PG_PASS}@localhost:${PG_PORT}/${PG_DB}"
