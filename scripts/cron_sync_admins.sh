#!/usr/bin/env bash
# Script for scheduled admin sync (can be used with Cloud Scheduler or cron)
set -euo pipefail
SPREADSHEET_ID=${SPREADSHEET_ID:-}
if [ -z "$SPREADSHEET_ID" ]; then
  echo "Please set SPREADSHEET_ID env var"
  exit 1
fi
PYTHONPATH=. python3 scripts/sync_admins.py --id "$SPREADSHEET_ID"
