# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram-based tattoo appointment booking system with Google Sheets/Calendar integration, AI-powered chat (INKA), and Cloud SQL for admin message storage. Supports both monolithic (polling/webhook) and microservices deployment.

## Development Commands

### Local Development

```bash
# Setup virtual environment and dependencies
bash setup/setup.sh

# Run bot in polling mode (local development)
python3 run.py

# Run bot in production mode (webhook)
python3 run_production.py

# Initialize Google Sheets database structure
python3 create_google_sheets_structure.py
```

### Microservices (Docker Compose)

```bash
# Start all services locally (backend, bot, ai, frontend, postgres)
docker compose up --build

# Services available at:
# - Backend API: http://localhost:8081
# - Bot webhook: http://localhost:8082
# - Frontend: http://localhost:8083
# - PostgreSQL: localhost:5432

# Development mode (with hot reload)
docker compose -f setup/docker-compose.dev.yml up --build

# Production mode (with nginx)
docker compose -f setup/docker-compose.prod.yml up --build -d
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_admin_messages_repo.py

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with verbose output
pytest -v
```

### Deployment

```bash
# One-line deploy to Google Cloud Run (all services)
PROJECT_ID=your-project REGION=us-central1 bash -c "./scripts/deploy_all.sh --yes"

# Multi-service deploy (backend, bot, ai)
./scripts/deploy_cloudrun_multi.sh

# Setup Telegram webhook after deploy
SERVICE_URL=$(gcloud run services describe tattoo-bot --region=us-central1 --format='value(status.url)')
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=${SERVICE_URL}/webhook/telegram"

# Terraform infrastructure provisioning
cd infra/terraform
terraform init
terraform plan -var='project_id=YOUR_PROJECT' -var='region=us-central1'
terraform apply
```

### Database Management

```bash
# Initialize Cloud SQL database schema
python src/db/init_postgres.py

# Connect to Cloud SQL via proxy (local development)
./cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:3306 &

# Connect to remote Cloud SQL instance
gcloud sql connect tattoo-bot-db --user=root

# Migrate admin messages from Sheets to Cloud SQL
python scripts/migrate_sheets_to_cloudsql.py
```

## Architecture

### Hybrid Storage Model

The system uses a **dual-database architecture**:

1. **Google Sheets** - Primary data store for:
   - `clients` - User profiles (telegram_id, name, phone, email, notes, tags)
   - `masters` - Tattoo artists (name, specialization, calendar_id, instagram, status)
   - `bookings` - Appointments (client_id, master_id, datetime, status, google_event_id)
   - `calendar` - Available time slots (date, master_id, slot_start, slot_end, available)
   - `services` - Service catalog (name, duration, price_from, price_to, category)

2. **Cloud SQL (PostgreSQL)** - High-performance storage for:
   - `admin_messages` - AI-categorized admin chat history with 12-month retention policy
   - Enables fast queries with indexes on timestamp, user_id, category
   - Supports PII redaction and GDPR compliance features

**Why this hybrid approach?**
- Google Sheets provides easy manual access/editing for business users
- Cloud SQL provides performance/indexing for high-volume admin messages
- Authentication is unified via Google OAuth for both systems

### Data Access Layer

All database operations go through repository classes in `src/db/repositories/`:
- `clients_repo.py` - Client CRUD operations
- `masters_repo.py` - Master/artist management
- `bookings_repo.py` - Appointment booking logic
- `calendar_repo.py` - Slot availability management
- `services_repo.py` - Service catalog operations
- `admin_messages_repo.py` - Admin chat history (Cloud SQL)

**Key abstraction**: Repositories use `SheetsClient` (for Google Sheets) or SQLAlchemy engine (for Cloud SQL), but handlers/services don't need to know which backend is used.

### Authentication Flow

Google OAuth is used for both Sheets and Calendar access:

1. **Service Account** (headless/production):
   - Use `credentials.json` with `"type": "service_account"`
   - No browser interaction needed
   - Sheets must be shared with service account email

2. **OAuth Desktop App** (local development):
   - Use `credentials.json` from Google Cloud Console OAuth client
   - First run opens browser for consent
   - Token saved to `token.json` and auto-refreshed

3. **Application Default Credentials** (Cloud Run):
   - Automatically uses Cloud Run service account
   - No credential files needed

See `src/db/sheets_client.py:_ensure_credentials()` for implementation.

### Bot Architecture

The bot uses **aiogram 3.x** with these key components:

- `src/bot/entrypoint.py` - Bot initialization, supports both polling and webhook modes
- `src/bot/router.py` - Registers all handlers and middlewares
- `src/bot/handlers/` - Command and callback handlers organized by role:
  - `client_handlers.py` - Client booking flow (`/start`, `/book`, `/bookings`)
  - `admin_handlers.py` - Admin panel commands (`/admin`)
  - `inka_handler.py` - AI chat integration (INKA S2 orchestrator)
  - `multilingual_handler.py` - Language detection and switching

**FSM (Finite State Machine)**: Booking flow uses aiogram FSM for multi-step conversations:
1. User sends `/book` → enters `BookingStates.waiting_for_master`
2. Selects master → `BookingStates.waiting_for_date`
3. Selects date → `BookingStates.waiting_for_slot`
4. Confirms → creates booking in Sheets + Google Calendar event

### AI Orchestrator (INKA S2)

`src/services/ai_orchestrator.py` bridges natural language to bot actions:

```python
# User sends: "забронируй меня на завтра в 15:00"
ai_response = await ai_engine.process_message(user_id, message, role, context)

# AI determines action: ActionType.CREATE_BOOKING
# Orchestrator executes: booking_service.create_booking(...)
# Returns: confirmation message in user's language
```

Supports:
- Multi-language detection (ru/en/he)
- Intent classification (book, cancel, check_availability, admin_query)
- Entity extraction (dates, times, master names)
- Context-aware conversations with history

### Microservices Architecture

When deployed via `docker-compose.yml`, the system runs as 4 services:

1. **backend** (`services/backend/`) - FastAPI web app
   - Admin panel UI at `/admin`
   - REST API for CRUD operations
   - Webhook management endpoint

2. **bot** (`services/bot/`) - Telegram webhook handler
   - Receives Telegram updates via POST /webhook/telegram
   - Processes commands and callbacks
   - Delegates to backend API for data operations

3. **ai** (`services/ai/`) - AI worker service
   - OpenAI API integration
   - Message classification and entity extraction
   - Independent scaling for AI workload

4. **frontend** (`services/frontend/`) - Static HTML UI
   - Admin dashboard (optional)
   - Documentation pages

All services share the same codebase (`src/`) mounted as volume in dev mode.

### Configuration

Environment variables are loaded via `src/config/config.py`:

**Required**:
- `BOT_TOKEN` or `TELEGRAM_BOT_TOKEN` - From @BotFather
- `SPREADSHEET_ID` - Created by `create_google_sheets_structure.py`

**Optional**:
- `OPENAI_API_KEY` - For INKA AI features
- `ADMIN_USER_IDS` - Comma/semicolon separated Telegram IDs
- `DEFAULT_TIMEZONE` - Default: `Asia/Jerusalem`
- `WEBHOOK_URL` - For webhook mode (auto-set on Cloud Run)
- `CLOUDSQL_CONNECTION_NAME` - For Cloud SQL (format: `project:region:instance`)
- `DATABASE_URL` - PostgreSQL connection string (for local postgres or Cloud SQL proxy)

**Modes**:
- `USE_WEBHOOK=false` → Polling mode (local development)
- `USE_WEBHOOK=true` → Webhook mode (production, requires `WEBHOOK_URL`)
- `CLOUD_RUN_ENV=true` → Enables Unix socket for Cloud SQL

### Deployment Environments

1. **Local Development** (`run.py`):
   - Polling mode (no webhook needed)
   - Uses `credentials.json` + `token.json` for Google auth
   - Optional local PostgreSQL via Docker

2. **Cloud Run** (via `scripts/deploy_all.sh`):
   - Webhook mode automatically configured
   - Cloud SQL connection via Unix socket (`/cloudsql/CONNECTION_NAME`)
   - Secrets from Google Secret Manager
   - Auto-scaling based on requests

3. **Microservices** (`docker-compose.yml`):
   - All services + PostgreSQL in containers
   - Code mounted as volume for hot reload
   - Ideal for testing full stack locally

### Infrastructure as Code (Terraform)

`infra/terraform/` provisions:
- Cloud SQL PostgreSQL instance
- Cloud Run services (backend, bot, ai)
- Service accounts with least-privilege IAM
- Secret Manager secrets (BOT_TOKEN, DB passwords)
- Cloud Build triggers for CI/CD
- Optional Jenkins on GKE with Workload Identity + GitHub OAuth

**Important**: Never commit `terraform.tfvars` with secrets. Use Secret Manager or environment variables.

## Key Implementation Details

### Google Calendar Sync

When a booking is created, if the master has `calendar_id` set:
1. `src/db/sheets_client.py:create_calendar_event()` creates event
2. Event ID stored in `bookings.google_event_id` column
3. On cancellation, `delete_calendar_event()` removes it

### PII Policy & Data Retention

Admin messages in Cloud SQL have 12-month retention (see `PII_POLICY.md`):
- `AdminMessagesRepo.delete_old_messages(months=12)` - Auto-cleanup
- `AdminMessagesRepo.redact_pii_by_user(user_id)` - GDPR compliance
- Run cleanup periodically via cron or Cloud Scheduler

### SSL Verification Disabled

**Development only**: The bot disables SSL verification to avoid certificate issues:
```python
# src/bot/entrypoint.py
class NoSSLVerifyAiohttpSession(AiohttpSession):
    # Creates session with ssl.CERT_NONE
```
**Production**: Remove this and use proper certificates.

### Error Handling

- All services use Python's `logging` module
- Handlers catch exceptions and send user-friendly messages
- Cloud Run logs viewable via: `gcloud run logs read --service=tattoo-bot --limit=50`

## Common Workflows

### Adding a New Bot Command

1. Create handler in `src/bot/handlers/`
2. Register in `src/bot/router.py:register_handlers()`
3. Add keyboard button in `src/bot/keyboards/` if needed
4. Test locally with `python3 run.py`

### Adding a New Database Table/Sheet

1. Update `src/db/sheets_client.py:create_spreadsheet_template()` with new sheet
2. Create repository in `src/db/repositories/new_repo.py`
3. Add to service factory `src/services/service_factory.py`
4. Run `python3 create_google_sheets_structure.py` to recreate Sheets DB

### Migrating Sheets to Cloud SQL

If you need to move a Google Sheets table to Cloud SQL for performance:
1. Create table schema in `src/db/init_postgres.py`
2. Write migration script in `scripts/` (see `migrate_sheets_to_cloudsql.py` example)
3. Update repository to use SQLAlchemy instead of SheetsClient
4. Test with local PostgreSQL before deploying

## Troubleshooting

### "BOT_TOKEN not set"
Add `BOT_TOKEN=xxx` to `.env` file or export as environment variable.

### "SPREADSHEET_ID not set"
Run `python3 create_google_sheets_structure.py` to create Sheets and get ID.

### "Permission denied" on Google Sheets
If using service account, share the spreadsheet with the service account email (found in `credentials.json`).

### Cloud SQL connection fails locally
Start Cloud SQL Proxy: `./cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432 &`
Then set `CLOUDSQL_HOST=127.0.0.1` in `.env`.

### Webhook not receiving updates
Check webhook status: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
Delete and reset: `scripts/setup_webhook.sh`

## Additional Documentation

- `README.md` - Full setup guide and feature list
- `PII_POLICY.md` - Data retention and privacy compliance
- `infra/terraform/README.md` - Infrastructure provisioning
- `setup/README.md` - Detailed local setup instructions
- `docs/ARCHITECTURE.md` - Detailed system design (if exists)
- `docs/GOOGLE_SHEETS_STRUCTURE.md` - Database schema details (if exists)
