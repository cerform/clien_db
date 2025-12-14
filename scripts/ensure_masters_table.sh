#!/usr/bin/env bash
set -euo pipefail

# Ensure masters table exists on Cloud SQL
if [ -z "${DATABASE_URL:-}" ]; then
  echo "Need DATABASE_URL to connect to Cloud SQL. Set it before running or use cloud_sql_proxy."
  exit 1
fi

python3 scripts/ensure_masters_table.py

echo "Masters table ensured."
