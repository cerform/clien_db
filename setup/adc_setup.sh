#!/usr/bin/env bash
set -euo pipefail

# ADC setup helper — configures Application Default Credentials for local development
# It supports two modes:
# 1) Use user credentials -> gcloud auth application-default login
# 2) Use service account JSON (recommended for CI/local non-interactive): set GOOGLE_APPLICATION_CREDENTIALS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."

usage() {
  echo "Usage: $0 [--service-account credentials.json]"
  echo "  --service-account <path>  Use JSON service account key and set GOOGLE_APPLICATION_CREDENTIALS"
  echo "  --login                   Run 'gcloud auth application-default login' to configure user ADC"
  echo "Example: $0 --service-account ../credentials.json"
}

if [ "$#" -eq 0 ]; then
  usage
  exit 0
fi

while (( "$#" )); do
  case "$1" in
    --service-account)
      SA_PATH="$2"; shift 2; ;;
    --login)
      LOGIN=true; shift; ;;
    *)
      echo "Unknown arg: $1"; usage; exit 1; ;;
  esac
done

if [ "${LOGIN:-false}" == true ]; then
  echo "Running: gcloud auth application-default login"
  gcloud auth application-default login
  echo "Done. ADC configured for your user."
fi

if [ -n "${SA_PATH:-}" ]; then
  if [ ! -f "$SA_PATH" ]; then
    echo "Service account JSON not found at: $SA_PATH"
    exit 1
  fi
  # Copy the file to a well-known location inside project (but not commit). Also set env var in .env if desired.
  TARGET="$REPO_ROOT/.gcp_adc.json"
  cp "$SA_PATH" "$TARGET"
  echo "Copied service account key to: $TARGET"

  echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$TARGET\"" >> "$REPO_ROOT/.env"
  echo "Added GOOGLE_APPLICATION_CREDENTIALS to .env (ensure .env is safe and not committed)"
  echo "You may want to re-run: source .env or restart services so they pick up the ADC variable."
fi

# Quick test - attempt to use ADC to access Secret Manager
if command -v python3 >/dev/null 2>&1; then
  python3 - <<PY || true
from google.cloud import secretmanager
import os
try:
    client = secretmanager.SecretManagerServiceClient()
    print('ADC check ok; Secret Manager client created')
except Exception as e:
    print('ADC test failed:', e)
PY
fi
