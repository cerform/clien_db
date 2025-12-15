# Staging Deployment Checklist

Quick checklist to deploy the current branch to staging and validate the human-like dialog changes.

1) Pre-deploy checks (local)
   - Run test suite: `pytest -q` (must pass)
   - Lint and static checks (optional): `flake8` / `bandit`
   - Confirm branch is pushed: `git push origin HEAD`

2) Environment & Secrets
   - Confirm GCP project and region (e.g., `PROJECT=tattoo-480007`, `REGION=europe-west1`)
   - Artifact Registry repo (e.g., `REPO=inka-repo`) and service account (`SERVICE_ACCOUNT`)
   - Cloud SQL instance connection name (e.g., `CLOUDSQL_INSTANCE=project:region:instance`)
   - Ensure Secret Manager contains: `BOT_TOKEN`, `OPENAI_API_KEY` (if enabling LLM), `CLOUDSQL_PASSWORD`, `SPREADSHEET_ID`, `WEBHOOK_SECRET`
   - Grant the Cloud Run service account `roles/secretmanager.secretAccessor` on the required secrets

3) Deploy to staging
   - Example (change values to match your project):

```bash
PROJECT=tattoo-480007 \
REGION=europe-west1 \
REPO=inka-repo \
SERVICE_ACCOUNT=inka-sa \
CLOUDSQL_INSTANCE=tattoo-480007:europe-west1:inka-db \
IMAGE_TAG=staging \
ENABLE_LLM=true \
./scripts/deploy_staging.sh
```

4) Smoke tests after deploy
   - Curl health: `curl $URL/api/health` -> status `healthy` or `degraded` (200)
   - Send a small test message to Telegram webhook via `/api/setup-webhook` or direct Telegram message to bot and ensure no errors
   - Check logs: `gcloud run services logs read inka-staging --region=$REGION --project=$PROJECT --limit=200`
   - Confirm LLM responses abide by dialog rules (no date offers early, one question at a time, no "I am a bot")

5) Rollback (if needed)
   - Use Cloud Run revisions to rollback: `gcloud run services revisions list --service inka-staging --region $REGION` and `gcloud run services update-traffic` to move traffic back

6) Post-deploy
   - Document staging URL and any observed issues
   - Run example conversations for the four psychotypes (Aggressive/Hesitant/VIP/Neutral) and capture logs

If you'd like, I can run the deploy now with suggested defaults — please confirm the values for the required variables above (or say "use project defaults") and I will proceed.
