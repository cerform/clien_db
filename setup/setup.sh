#!/usr/bin/env bash
set -euo pipefail

# Interactive setup script to prepare local development environment
# - Creates a virtualenv (in .eco)
# - Installs Python dependencies
# - Launches local Postgres (docker-compose)
# - Creates .env from .env.example and prompts necessary env vars
# - Attempts to create Google Spreadsheet (if credentials present)
# - Optionally initializes the DB schema

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/.."

cd "$REPO_ROOT"

die() { echo "ERROR: $*" >&2; exit 1; }
usage() {
  echo "Usage: $0 [options]"
  echo "  --auto-env                Auto-generate .env from provided CLI args"
  echo "  --bot-token <token>       Bot token for .env generation"
  echo "  --openai-key <key>        OpenAI key for .env generation"
  echo "  --spreadsheet-id <id>     Spreadsheet ID"
  echo "  --google-creds <file>     Path to google credentials json"
  echo "  --database-url <url>      Direct DATABASE_URL used for .env"
  echo "  --admin-ids <ids>         Comma-separated admin IDs"
  echo "  --env <development|production>"
}

check_py() {
  if ! command -v python3 >/dev/null 2>&1; then
    die "python3 not found in PATH. Install Python 3.10+ and retry."
  fi
  PY_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
  echo "Python version: $PY_VER"
}

create_virtualenv() {
  if [ -d ".eco" ]; then
    echo ".eco already exists. Skipping venv creation. Use 'source .eco/bin/activate' to activate."
  else
    python3 -m venv .eco
    echo "Virtual environment created at .eco"
  fi
}

install_requirements() {
  echo "Installing requirements..."
  source .eco/bin/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  echo "Requirements installed"
}

generate_env() {
  if [ -f ".env" ]; then
    echo ".env already exists. If you want to recreate it, delete or move the current one."
    return
  fi

  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "Copied .env.example to .env"
  else
    cat > .env <<EOL
TELEGRAM_BOT_TOKEN=
OPENAI_API_KEY=
SPREADSHEET_ID=
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
DEFAULT_TIMEZONE=Asia/Jerusalem
ADMIN_USER_IDS=
ENV=development
USE_WEBHOOK=false
WEBHOOK_URL=
PORT=8081
CLOUDSQL_USER=postgres
CLOUDSQL_PASSWORD=password
CLOUDSQL_DB=admin_messages
DATABASE_URL=
EOL
    echo "Created basic .env"
  fi

  echo "
Please edit the .env file and fill required values.
Hint: copy credentials.json into the project root and set GOOGLE_CREDENTIALS_PATH if needed.
"
  read -p "Open .env in $EDITOR (or nano)? Y/n: " -r
  if [[ $REPLY =~ ^[Yy] || -z $REPLY ]]; then
    ${EDITOR:-nano} .env
  fi
  # Load env so subsequent steps use settings from .env
  if [ -f .env ]; then
    echo "Loading .env into the environment for following steps"
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
  fi
}

start_postgres() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not found; skipping local Postgres creation. You can manually provide DATABASE_URL to connect to a DB."
    return
  fi
  echo "Starting local Postgres via docker-compose"
  # Prefer 'docker compose' (modern), fallback to 'docker-compose'
  if docker compose version >/dev/null 2>&1; then
    DOCKER_CMD=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1; then
    DOCKER_CMD=(docker-compose)
  else
    echo "docker (compose) CLI not found. Please install Docker with docker compose or docker-compose."
    return
  fi
  "${DOCKER_CMD[@]}" -f "$SCRIPT_DIR/docker-compose.yml" up -d
  echo "Waiting for Postgres to be ready..."
  # wait for postgres
  for i in {1..20}; do
    if docker exec clien_db_postgres pg_isready -U ${CLOUDSQL_USER:-postgres} >/dev/null 2>&1; then
      echo "Postgres ready"
      break
    fi
    sleep 1
  done
  echo "Ensure DATABASE_URL is set in .env: postgresql://<user>:<pass>@127.0.0.1:5432/<db>"
}

auto_env_and_restart_compose() {
  # Use configure_env.py to generate .env from provided CLI args or environment, then restart compose
  echo "Auto-generating .env using setup/configure_env.py"
  # Rebuild argument list from environment variables if present
  ARGS=(--out .env --force)
  [[ -n "${BOT_TOKEN:-}" ]] && ARGS+=(--bot-token "${BOT_TOKEN}")
  [[ -n "${OPENAI_API_KEY:-}" ]] && ARGS+=(--openai-key "${OPENAI_API_KEY}")
  [[ -n "${SPREADSHEET_ID:-}" ]] && ARGS+=(--spreadsheet-id "${SPREADSHEET_ID}")
  [[ -n "${GOOGLE_CREDENTIALS_PATH:-}" ]] && ARGS+=(--google-creds "${GOOGLE_CREDENTIALS_PATH}")
  [[ -n "${DATABASE_URL:-}" ]] && ARGS+=(--database-url "${DATABASE_URL}")
  python3 "$SCRIPT_DIR/configure_env.py" "${ARGS[@]}"
  echo ".env generated/updated. Restarting dev docker-compose..."
  if docker compose version >/dev/null 2>&1; then
    DOCKER_CMD=(docker compose)
  else
    DOCKER_CMD=(docker-compose)
  fi
  "${DOCKER_CMD[@]}" -f "$SCRIPT_DIR/docker-compose.dev.yml" down -v || true
  "${DOCKER_CMD[@]}" -f "$SCRIPT_DIR/docker-compose.dev.yml" up --build -d
  echo "Dev stack restarted. To view logs: docker-compose -f setup/docker-compose.dev.yml logs --tail 200"
}

create_google_spreadsheet() {
  # Try to create the spreadsheet if credentials exist and user approves
  source .eco/bin/activate || true
  if [ ! -f "${GOOGLE_CREDENTIALS_PATH:-credentials.json}" ]; then
    echo "Google credentials not found at ${GOOGLE_CREDENTIALS_PATH:-credentials.json}. Skipping spreadsheet creation."
    return
  fi

  read -p "Create Google Sheets spreadsheet from template now? Y/n: " -r
  if [[ $REPLY =~ ^[Yy] || -z $REPLY ]]; then
    python3 create_google_sheets_structure.py
    echo "If the script printed a SPREADSHEET_ID, paste it into .env as SPREADSHEET_ID"
    ${EDITOR:-nano} .env
  fi
}

init_db_schema() {
  # Initialize Postgres schema by calling run_production which initializes DB on startup
  read -p "Initialize local Postgres schema now? Y/n: " -r
  if [[ $REPLY =~ ^[Yy] || -z $REPLY ]]; then
    # Start the app in the background just to execute init hooks
    echo "Starting app to trigger DB initialization..."
    source .eco/bin/activate || true
    # Run initialization via execute init_postgres directly
    python3 - <<PY
from src.db.init_postgres import init_database
print('Initializing DB...')
init_database()
print('Done')
PY
  fi
}

start_bot() {
  read -p "Start bot now (local development mode)? Y/n: " -r
  if [[ $REPLY =~ ^[Yy] || -z $REPLY ]]; then
    source .eco/bin/activate || true
    echo "Starting bot via run.py (Polling)"
    python3 run.py &
    echo "Bot started in the background (Polling). Check logs to confirm it's running."
  fi
}

parse_args() {
  AUTO_ENV=false
  # Capture CLI args for auto env generation
  while (( "$#" )); do
    case "$1" in
      --auto-env)
        AUTO_ENV=true
        shift
        ;;
      --bot-token)
        BOT_TOKEN="$2"; shift 2; ;;
      --openai-key)
        OPENAI_API_KEY="$2"; shift 2; ;;
      --spreadsheet-id)
        SPREADSHEET_ID="$2"; shift 2; ;;
      --google-creds)
        GOOGLE_CREDENTIALS_PATH="$2"; shift 2; ;;
      --database-url)
        DATABASE_URL="$2"; shift 2; ;;
      --admin-ids)
        ADMIN_USER_IDS="$2"; shift 2; ;;
      --env)
        ENV="$2"; shift 2; ;;
      --auto-env-restart)
        AUTO_ENV_RESTART=true; shift ;;
      -h|--help)
        usage; exit 0 ;;
      *)
        # stop parsing at unknown arg
        break
        ;;
    esac
  done
}

parse_args "$@"

main() {
  check_py
  create_virtualenv
  install_requirements
  # If auto env flag supplied, generate .env via configure_env.py
  if [[ ${AUTO_ENV:-false} == true ]]; then
    echo "Generating .env automatically using CLI parameters"
    # Build argument list for configure_env
    ARGS=(--out .env --force)
    [[ -n "${BOT_TOKEN:-}" ]] && ARGS+=(--bot-token "${BOT_TOKEN}")
    [[ -n "${OPENAI_API_KEY:-}" ]] && ARGS+=(--openai-key "${OPENAI_API_KEY}")
    [[ -n "${SPREADSHEET_ID:-}" ]] && ARGS+=(--spreadsheet-id "${SPREADSHEET_ID}")
    [[ -n "${GOOGLE_CREDENTIALS_PATH:-}" ]] && ARGS+=(--google-creds "${GOOGLE_CREDENTIALS_PATH}")
    [[ -n "${DATABASE_URL:-}" ]] && ARGS+=(--database-url "${DATABASE_URL}")
    [[ -n "${ADMIN_USER_IDS:-}" ]] && ARGS+=(--admin-ids "${ADMIN_USER_IDS}")
    [[ -n "${ENV:-}" ]] && ARGS+=(--env "${ENV}")
    python3 "$SCRIPT_DIR/configure_env.py" "${ARGS[@]}"
    echo "Generated .env"
  else
    generate_env
  fi
  # If user requested auto-env + restart compose
  if [[ ${AUTO_ENV_RESTART:-false} == true ]]; then
    auto_env_and_restart_compose
  fi
  start_postgres
  create_google_spreadsheet
  init_db_schema
  start_bot
  echo "Local setup complete. See setup/README.md for more info."
}

main "$@"
