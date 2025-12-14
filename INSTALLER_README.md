# One-Click Installer & Deployment for INKA (Tattoo Salon)

This README explains how to use the provided CLI installer and the web-based setup to deploy the system in Google Cloud Run.

## Quick Overview
 - `src/services/sheets_migrator.py` - utilities to migrate spreadsheets to the new schema safely.

### Migrations & Admin settings

From the Admin Panel: `/admin/settings` you can:
- Review status of integrations (Sheets, Telegram, LLM)
- Edit non-secret system settings (salon name, timezone, spreadsheet id)
- Run the spreadsheet schema migration (requires admin ID) — this is also available as CLI `tools/migrate_sheets.py`

### API Explorer (Admin)

There is now an interactive API explorer at `/admin/endpoints`:
- View grouped endpoints by tags (tabbed view)
- Filter by HTTP methods (All/GET/POST/PUT/DELETE)
- See OpenAPI metadata: parameters, requestBody schema, responses
- Test endpoints with a built-in Try feature for any method. For non-GET methods, default is "Simulate" (adds header `X-Simulate: 1` and the server returns a simulated response). To perform actual changes, uncheck "Simulate" and provide an admin token `Bearer admin_token_<id>` in the token field.

Now with enhancements:
- Simulated responses are *intelligent* — the server will look at your OpenAPI spec and return the `example` for the response if provided, or a reasonable mock generated from the response `schema`.
- You can provide `query params` directly in the UI (each endpoint with query parameters will show inputs for them); these will be included when running Try requests.
- JWT tokens are supported for admin authentication: login returns `token` (JWT) and `legacy_token`. Use either in the Test UI. If `X-Simulate` is checked, the call will not mutate the backend (simulated read-only).

Notes:
- Simulation sends `X-Simulate: 1` header and the server's middleware will not run the underlying handler; it returns a simulated JSON describing what would have been invoked.
- Use admin tokens returned during `/api/login` (default simple token format `admin_token_<id>`) when you want to execute a live POST request from the explorer.
## Prerequisites
- Google Cloud SDK (`gcloud`) installed and authenticated.
- Docker installed (for building images locally).
- A Google Project with billing enabled and APIs activated (if not, `gcloud` sdk will enable them during installer).
- `credentials.json` (client OAuth) if you want to use Sheets Calendar functionality in local dev flow; otherwise Cloud Run will use Application Default Service Account.
- A Telegram Bot token from BotFather, and a valid OpenAI API key (or another LLM provider key).

## Steps for Owner / Admin (One-click flow)
1. Clone the repo and checkout `fix-e2e-no-venv` branch.
2. Install Python 3.10+ and dependencies in `requirements.txt` (pip install -r requirements.txt).
3. Run the installer:
   ```bash
   python3 tools/install_and_deploy.py
   ```
   - Follow prompts for GCP project, region, service name, tokens and keys.
   - The installer builds the Docker image, pushes it to Container Registry, creates secrets, and deploys to Cloud Run.
4. After deploy opens Cloud Run URL, open `<CLOUD_RUN_URL>/setup` and go through the web UI to validate and configure the system.
### Web-based installer
You can also drive the installer from the deployed web UI. Visit `<CLOUD_RUN_URL>/installer/` to open the web setup wizard — fill in project, region, tokens and click "Start Install" to trigger a background deploy. Logs and status are available in the same UI (polling-based log viewer).

Notes:
- The web installer creates a lockfile `.installer_complete` in the project root after a successful deploy to prevent accidental re-runs. Admin users (as configured via `ADMIN_USER_IDS`) may bypass this lock.
 - The web installer creates a lockfile `.installer_complete` in the project root after a successful deploy to prevent accidental re-runs. Admin users (as configured via `ADMIN_USER_IDS`) may bypass this lock. Admins can remove the lock via `POST /installer/unlock` (requires admin token `Authorization: Bearer <token>`).
- The UI is a multi-step wizard (6 steps). Use the final Deploy step to run the installer. For CI runs prefer `scripts/ci_installer_smoke.sh --dry-run` or the CLI `tools/install_and_deploy.py --dry-run`.

## Steps for Developers (local testing)
1. Ensure you have `credentials.json` in the project root and run `python -m pip install -r requirements.txt`.
2. Run the web app locally:
   ```bash
   export TELEGRAM_BOT_TOKEN="<TELEGRAM_BOT_TOKEN>"
   export OPENAI_API_KEY="<OPENAI_API_KEY>"
   uvicorn src.web.app:create_app --host 0.0.0.0 --port 8080
   ```
3. Open `http://localhost:8080/setup` and test the UI. The Sheets OAuth will prompt to complete authorization in the browser.

## Notes & Caveats
- The installer stores secrets in Google Secret Manager. Cloud Run will mount them as environment variables via `--set-secrets` flag.
- The app uses Application Default Credentials on Cloud Run; we added fallback support to use ADC if `credentials.json` is missing.
- The `SheetsClient` still supports local OAuth via `credentials.json` and `token.json` for local dev flows.

## Known Gaps & Future Enhancements
- Better role & permission checks when creating service accounts and assigning IAM roles.
- Support for Artifact Registry as optional target instead of Container Registry.
- More robust secret handling for complex key values and avoiding shell-escaping pitfalls during secret creation in the installer.
# INKA One-Click Installer & Setup — Developer Guide

## Overview
This guide explains the steps to run the installer, setup the service, and verify local/in-cloud deployment.

## Files added/updated
- `tools/install_and_deploy.py` (UPDATED)
- `src/core/config_manager.py` (UPDATED)
- `src/core/llm_client.py` (UPDATED)
- `src/web/routes/setup.py` (UPDATED)
- `src/db/sheets_client.py` (UPDATED headers)
- `tests/unit/test_config_manager.py` (NEW)
- `tests/unit/test_llm_client.py` (NEW)
- `tests/integration/test_sheets_client.py` (NEW)
- `tests/e2e/test_setup_flow.py` (NEW)
- `Jenkinsfile` (NEW)
- `docs/QA/*` (NEW docs for QA Strategy, Plan, RTM, Test Cases, Checklist)

## Run locally
1. Activate `.eco` virtualenv:
```bash
python3 -m venv .eco
source .eco/bin/activate
pip install -r requirements.txt
```
2. Run setup locally (the service is expected to be started separately):
```bash
# 1) Start the FastAPI server
python -m uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000
# 2) Open http://localhost:8000/setup and fill information
```
3. Create test spreadsheet (if required):
```bash
python create_google_sheets_structure.py
```

## Deploy to GCP (with installer)
```bash
# 1) authenticate in gcloud
gcloud auth login
# 2) Run installer script
python tools/install_and_deploy.py
# Follow interactive prompts
```

### Non-interactive mode (CI/CD)
Use the following flags to run installer non-interactively from CI/CD or scripts:

```bash
python tools/install_and_deploy.py --project <GCP_PROJECT_ID> \
   --region <GCP_REGION> --service <CLOUD_RUN_SERVICE> \
   --docker-image gcr.io/<GCP_PROJECT_ID>/<SERVICE_NAME>:latest \
   --sa-name <SERVICE_ACCOUNT_NAME> --telegram-token <TELEGRAM_TOKEN> \
   --set-webhook --dry-run
```

Note: Do not keep `--dry-run` for real deploys. In Jenkins set these variables securely in the job or credentials store.

### Jenkins CI/CD instructions
1. Save a GCP service account JSON as a Jenkins *Secret File* credential id `GCP_SA_JSON`.
2. Save `TELEGRAM_TOKEN` and `LLM_API_KEY` as Jenkins *Secret Text* credentials.
3. Save `GCP_PROJECT_ID` as a plain credential string.
4. Set `DRY_RUN` environment variable to `true` for testing and false for production deploys.
5. Configure the pipeline to run `scripts/ci_deploy.sh` (Jenkinsfile already contains the stage to run the script).

### Jenkins Enhancements
- The Jenkinsfile now includes a **Security Scans** stage (Bandit for Python checks, Trivy for container images), **Staging Deploy** (which runs the installer against a staging env and generates reports), and an optional **Production Deploy** stage protected by a manual **Approval** step (Input) to prevent accidental production pushes.
- The `scripts/ci_deploy.sh` supports `SCAN=true` and `REPORT_DIR=reports` to run container scans and write scan results into `reports/` for archival and analysis.

Ensure `gcloud` and Docker are installed on pipeline agents and that service account has appropriate roles.

## Testing
- Unit tests:
```bash
pytest -q tests/unit
```
- Integration tests (mocking):
```bash
pytest -q tests/integration
```
- E2E tests (Playwright):
```bash
# Install Playwright
pip install playwright
playwright install
pytest -q tests/e2e
```
- Load tests (locust):
```bash
pip install locust
locust -f tests/performance/locustfile.py --host http://localhost:8000
```

## Next steps for QA
- Expand the functional and API tests according to `docs/QA/Test_Cases.md`
- Implement Playwright scripts to cover E2E flows fully
- Add integration tests for webhook and LLM with mocking layers

*** End of File
