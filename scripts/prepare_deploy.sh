#!/usr/bin/env bash
set -euo pipefail

# Prepare deploy: run tests, run SQL migrations, create RBAC roles, then optionally deploy to Cloud Run.
# Usage:
#   ./scripts/prepare_deploy.sh --run-tests --migrate --rbac --deploy

RUN_TESTS=false
RUN_MIGRATIONS=false
RUN_RBAC=false
DO_DEPLOY=false
DRY_RUN=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-tests)
      RUN_TESTS=true; shift;;
    --migrate)
      RUN_MIGRATIONS=true; shift;;
    --rbac)
      RUN_RBAC=true; shift;;
    --deploy)
      DO_DEPLOY=true; shift;;
    --no-dry-run)
      DRY_RUN=false; shift;;
    -h|--help)
      echo "Usage: $0 [--run-tests] [--migrate] [--rbac] [--deploy] [--no-dry-run]"; exit 0;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

echo "Preparing deploy with options:" \
     "run-tests=$RUN_TESTS" "migrate=$RUN_MIGRATIONS" "rbac=$RUN_RBAC" "deploy=$DO_DEPLOY" "dry-run=$DRY_RUN"

if [ "$RUN_TESTS" = true ]; then
  echo "Running unit tests (pytest -q)..."
  # Ensure testing dependencies installed (pytest version in requirements.txt)
  if command -v python3 &>/dev/null; then
    python3 -m pip install -r requirements.txt --no-cache-dir || true
    # Check pytest version
    PYTEST_VER=$(pytest --version 2>/dev/null | awk '{print $2}' || true)
    if [ -n "$PYTEST_VER" ]; then
      PYTEST_MAJOR=$(echo $PYTEST_VER | cut -d. -f1)
      if [ "$PYTEST_MAJOR" -lt 8 ]; then
        echo "⚠️ Detected pytest $PYTEST_VER < 8.0. Attempting to install latest pytest locally..."
        python3 -m pip install --user pytest==8.3.4 || true
        echo "Retrying pytest..."
      fi
    fi
  fi
  # Run everything except selenium tests by default; CI can run selenium separately
  pytest -q -k "not selenium"
fi

if [ "$RUN_MIGRATIONS" = true ]; then
  echo "Running SQL migrations (scripts/apply_sql_migrations.py)..."
  if [ -z "${DATABASE_URL:-}" ]; then
    echo "DATABASE_URL is not set. Set it to run migrations against the target DB (or create secret DATABASE_URL in cloud)."
    read -p "Proceed without DATABASE_URL and skip applying migrations? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      echo "Skipping migrations..."
    else
      echo "Please set DATABASE_URL environment variable and re-run the script."; exit 2
    fi
  else
    if [ "$DRY_RUN" = true ]; then
      python3 scripts/apply_sql_migrations.py
    else
      python3 scripts/apply_sql_migrations.py --apply
    fi
  fi
fi

if [ "$RUN_RBAC" = true ]; then
  echo "Creating or updating RBAC roles (scripts/create_rbac_roles.py)..."
  if [ -z "${DATABASE_URL:-}" ]; then
    echo "DATABASE_URL is not set. Set it to run RBAC scripts against the target DB."
    read -p "Proceed without DATABASE_URL and skip applying RBAC? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      echo "Skipping RBAC create/update..."
    else
      echo "Please set DATABASE_URL environment variable and re-run the script."; exit 2
    fi
  else
    if [ "$DRY_RUN" = true ]; then
      python3 scripts/create_rbac_roles.py
    else
      python3 scripts/create_rbac_roles.py --apply
    fi
  fi
fi

if [ "$DO_DEPLOY" = true ]; then
  echo "Starting Cloud Run deployment..."
  # Use the existing deployment script
  if [ -f ./deploy_cloudrun_postgres.sh ]; then
    if [ "$DRY_RUN" = true ]; then
      echo "DRY-RUN: would call deploy_cloudrun_postgres.sh"
    else
      ./deploy_cloudrun_postgres.sh
    fi
  else
    echo "Deploy script deploy_cloudrun_postgres.sh not found. Skipping."; exit 1
  fi
fi

echo "Prepare deploy finished"
