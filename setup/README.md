# Setup — Local development and testing

This directory contains scripts to help you set up the local environment for running the bot and required infrastructure (PostgreSQL, Google Sheets, etc.).

Prerequisites
- Python 3.10+
- Docker (optional, for local Postgres and pgAdmin)
- Google credentials: either an OAuth client credentials JSON (type "installed" or "web") for interactive OAuth flow, or a Service Account JSON file (type "service_account").

Notes about Google credentials
- OAuth client credentials (installed/web) will launch an interactive browser flow to authorize the app to access your Drive/Sheets. Use these if you want to create the spreadsheet in your personal Drive and see it there.
- Service account JSON files are headless credentials useful for CI or server deployments. If using a service account, ensure the **Google Sheets API** and **Drive API** are enabled in your Google Cloud project, and either:
	- Share a template spreadsheet with the service account's email so it can operate on it, OR
	- Allow the service account to create spreadsheets on its own Drive (it will own created spreadsheets). If you get a 403 permission error, double-check API enablement and sharing/permissions.

Quick Start (Linux/macOS)

1. Activate and switch to the repo root
```bash
cd /path/to/clien_db
```

2. Run setup script
```bash
bash setup/setup.sh
```
If you prefer a non-interactive approach and want to auto-generate `.env` and restart the dev-compose, you can pass `--auto-env-restart` along with CLI args or environment variables (example):

```bash
# Provide values and generate env + restart compose
BOT_TOKEN=xxx OPENAI_API_KEY=yyy bash setup/setup.sh --auto-env-restart --database-url "postgresql://postgres:password@127.0.0.1:5432/admin_messages"

# Or via CLI args
bash setup/setup.sh --auto-env --bot-token xxx --openai-key yyy --database-url postgresql://postgres:password@127.0.0.1:5432/admin_messages --auto-env-restart
```

What the script does
- Creates a virtual environment in `.eco` (if not exist)
- Installs `pip` dependencies from `requirements.txt`
- Starts a local PostgreSQL container using `docker compose` (optional)
- Copies `.env.example` to `.env` and prompts you to fill values (BOT_TOKEN, GOOGLE_CREDENTIALS_PATH, etc.)
- Optionally creates a Google Sheets structure by using the provided `create_google_sheets_structure.py` (supports `--yes` to bypass confirmation and `--skip` to avoid creation).
- Optionally initializes Postgres schema by calling `init_database()`
- Optionally starts the bot (polling)
 - Optionally starts the bot (polling)
 - Use `setup/start_web.sh` to start the web UI (uvicorn) for development

Manual steps you still need
- Obtain a Telegram token from @BotFather and fill `TELEGRAM_BOT_TOKEN` in `.env`.
- Create OAuth credentials in the Google Cloud Console and place `credentials.json` in the repo root (or point `GOOGLE_CREDENTIALS_PATH` to them).
- If you want to use webhook deployment, configure `WEBHOOK_URL` and deploy to Cloud Run using provided Docker files and `deploy_cloudrun.sh`.

Running in production (Cloud Run)
- The repository includes `deploy_cloudrun.sh`, `setup/deploy_cloudrun_europe.sh` and `cloudbuild.yaml` for building and deploying to Cloud Run.
- The Cloud Run build uses a `cloudbuild.yaml` that can be configured to deploy to an EU region using substitutions. To build & deploy via Cloud Build set substitutions like `_REGION` and `_CLOUDSQL_INSTANCE`.
- Example (using Cloud Build's gcloud CLI):

```bash
# Deploy using the provided EU deployment script (will submit a Cloud Build and deploy to Cloud Run)
ASSUME_YES=1 bash setup/deploy_cloudrun_europe.sh my-gcp-project europe-west1 tattoo-bot eu-instance

# Or directly via gcloud builds submit with substitutions:
gcloud builds submit --tag gcr.io/${PROJECT_ID}/tattoo-bot:latest --project=${PROJECT_ID} --substitutions=_REGION=europe-west1,_CLOUDSQL_INSTANCE=tattoo-bot-db,_SERVICE_NAME=tattoo-bot
```

GitHub Actions: Use the included workflow `.github/workflows/deploy-cloudrun-eu.yml` for CI-triggered deploys. The workflow reads `GCP_SA_KEY` and `GCP_PROJECT_ID` from GitHub repository secrets and will submit a Cloud Build with EU region substitutions.

Secrets and Secret Manager
- Cloud Build deploys use Secret Manager secrets to pass BOT_TOKEN, OPENAI_API_KEY, CLOUDSQL_PASSWORD, SPREADSHEET_ID and GOOGLE_CREDENTIALS_JSON. Ensure the required secrets exist in your project under the same names or create them before running the build.

Example to create secrets before deployment:

```bash
gcloud secrets create BOT_TOKEN --data-file=- --project=${PROJECT_ID} < <(echo -n "<BOT_TOKEN_HERE>")
gcloud secrets create OPENAI_API_KEY --data-file=- --project=${PROJECT_ID} < <(echo -n "<OPENAI_KEY_HERE>")
gcloud secrets create CLOUDSQL_PASSWORD --data-file=- --project=${PROJECT_ID} < <(echo -n "<DB_PASS>")
gcloud secrets create SPREADSHEET_ID --data-file=- --project=${PROJECT_ID} < <(echo -n "<SPREADSHEET_ID>")
gcloud secrets create GOOGLE_CREDENTIALS_JSON --data-file=- --project=${PROJECT_ID} < credentials.json
```

If you want, I can:
- Add a Windows `install.bat` or `install.ps1` which performs similar tasks
- Add support for generating `.env` from CLI arguments to better support automated CI runs
- Add a Docker Compose service to run the web/uvicorn server for an integrated development environment

CLI `.env` generator
--------------------

You can generate `.env` without opening an editor using `setup/configure_env.py` directly or via the `setup/setup.sh` script with the `--auto-env` flag.
Example:

```bash
python3 setup/configure_env.py --bot-token abc123 --openai-key sk-xxx --spreadsheet-id 17mB1... --google-creds credentials.json --out .env --force

# Or use setup shim
bash setup/setup.sh --auto-env --bot-token abc123 --openai-key sk-xxx --database-url postgresql://postgres:password@127.0.0.1:5432/admin_messages --admin-ids 12345
```

Development Docker Compose (dev)
--------------------------------

Start local dev stack to run the web server connected to a local Postgres using the dev docker-compose:

```bash
docker compose -f setup/docker-compose.dev.yml up --build
```

Production Docker Compose (prod)
--------------------------------

Basic production stack is available in `setup/docker-compose.prod.yml`. The service composes `web` (app), `postgres` and `nginx` as a reverse proxy.

Note: For production, prefer using cloud providers and secret managers (GCP Secret Manager / AWS Secrets Manager). The example uses `env_file`—make sure `.env` is outside your repo.

Windows installer notes
----------------------

The Windows Tkinter installer will now create simple `run_bot.bat` and `uninstall.bat` files in the install directory and on Desktop to help users run and remove the installed application quickly (no OS-level shortcuts are created to avoid additional dependency complexity). If you need full Start-Menu shortcuts, we can add pywin32 or a more advanced installer.

Migration and security
----------------------
See `setup/MIGRATION_AND_SECURITY.md` for migration and security best practices.

Helpful scripts
- `setup/start_web.sh` — Starts the web UI with uvicorn (dev server)
- `setup/setup.sh` — Main interactive setup script
- `setup/docker-compose.yml` — DB+pgAdmin for local testing
- `setup/install_windows.ps1` — Windows PowerShell setup

Google Cloud ADC for local Secret Manager (optional)
- To enable Secret Manager access locally, either login with your user account: `gcloud auth application-default login` or use a service account JSON:
	```bash
	bash setup/adc_setup.sh --service-account /path/to/credentials.json
	# then restart docker compose: bash setup/setup.sh --auto-env-restart
	```

Security note
- Do not commit `.env` or any tokens/credentials into version control. Use `.env.example` and keep secrets outside of Git.
