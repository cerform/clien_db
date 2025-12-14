# QA Checklist — INKA

## Global system checks
1. Ensure environment variables are read from Secret Manager or `.env` securely.
2. Ensure `config.json` is not containing raw secrets.
3. Ensure `.eco` is in `.gitignore`.
4. Verify that `gcloud` CLI is available on CI.
5. Verify Docker is present on build agents.
6. Setup SSO or service account for CI.

## API & Back-end (FastAPI)
7. Linting passed
8. All endpoints are covered by unit tests
9. Input validation exists for all POST endpoints
10. Rate limiting for dangerous operations
11. Error handling with clear codes
12. Logging enabled and structured
13. Health endpoint `/health` present and returns OK
14. Config manager loads secrets and normal config
...

## Google Sheets & Calendar
- Data schema validation
- Resilience to missing columns
- Permissions checks
- Race condition tests for simultaneous writes
...

## Telegram Bot
- Webhook endpoint processes updates
- Bot token is never exposed
- Admin-only endpoints validated via admin ID
- Rate limits and spam protection
...

## LLM/AI
- LLM input sanitization
- Timeout enforcement
- Provider switching via config
- Mocked LLM tests for expected outputs
...

## Installer / Setup Wizard
- CLI checks dependencies and prints help
- Installer supports both interactive and non-interactive modes
- Deploy flow includes steps: enable APIs, create SA, grant roles, build image, push, deploy
- Setup page validates tokens and saves secrets into Secret Manager
...

## Security
- Secrets never logged in plaintext
- IAM roles set to least privilege
- SQL injection vector checks
- XSS protection on UI
- CSRF disabled or controlled for API endpoints
...

## Performance
- Load test for webhook: 1000 updates/second (gradual) simulated
- Concurrency for bot: 200 parallel messages
- Soak test: run 12 hours at moderate load
...

# Notes
This checklist is not final; it must be linked to test cases in the RTM.
