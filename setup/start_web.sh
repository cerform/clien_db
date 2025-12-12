#!/usr/bin/env bash
set -euo pipefail

# Start the web app (uvicorn), useful for testing the web UI
# Make sure .env is configured (load env)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."
cd "$REPO_ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

if [ -d .eco ]; then
  source .eco/bin/activate
fi

# Bind to port from .env PORT
PORT=${PORT:-8081}

# Use fast-reload for development
exec python -m uvicorn src.web.app:create_app --factory --host 0.0.0.0 --port ${PORT} --reload
