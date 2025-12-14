# Deploy to Staging (Cloud Run)

This document and `scripts/deploy_staging.sh` automate a reproducible staging deployment for the `clien_db` service.

Prerequisites
- gcloud CLI installed and authenticated: `gcloud auth login`
- Docker installed and able to push to Artifact Registry
- You have a service account with these roles:
  - `roles/run.admin` (or Cloud Run deployer role)
  - `roles/iam.serviceAccountUser` on the chosen service account
  - `roles/cloudsql.client` (if using Cloud SQL)
  - `roles/secretmanager.secretAccessor` for required secrets
- Create secrets in Secret Manager: `OPENAI_API_KEY`, `DB_PASSWORD`, `WEBHOOK_SECRET` (or reuse existing)

Recommended env variables (examples):
- `PROJECT` - your GCP project id (e.g. `tattoo-480007`)
- `REGION` - Cloud Run region (default in script: `us-central1`)
- `REPO` - Artifact Registry repository name (docker format)
- `SERVICE_ACCOUNT` - service account name (without `@project.iam.gserviceaccount.com`)
- `CLOUDSQL_INSTANCE` - Cloud SQL connection name `project:region:instance`

Quick start
1. Export variables (example):

```bash
export PROJECT=tattoo-480007
export REGION=us-central1
export REPO=inka-repo
export SERVICE_ACCOUNT=inka-sa
export CLOUDSQL_INSTANCE=tattoo-480007:us-central1:inka-db
export IMAGE_TAG=staging
```

2. Run the deploy script:

```bash
./scripts/deploy_staging.sh
```

Secrets
- Create secrets (example):

```bash
echo -n "$OPENAI_API_KEY" | gcloud secrets create OPENAI_API_KEY --data-file=- --project=$PROJECT
echo -n "$DB_PASSWORD" | gcloud secrets create DB_PASSWORD --data-file=- --project=$PROJECT
echo -n "$WEBHOOK_SECRET" | gcloud secrets create WEBHOOK_SECRET --data-file=- --project=$PROJECT
```

Grant runtime access to secrets to the Cloud Run service account:

```bash
gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=${PROJECT}
```

Notes & troubleshooting
- If you prefer Cloud Build instead of local Docker push, replace the build/push block with `gcloud builds submit --tag gcr.io/$PROJECT/inka:$IMAGE_TAG` and change `--image` parameter accordingly.
- The script sets `--allow-unauthenticated`. Remove this flag for private deployments and use IAM invoker roles.
- Use `gcloud run services logs read inka-staging --region=$REGION --project=$PROJECT` for logs.

Smoke checklist
- curl the health endpoint: `curl $URL/health` (or root) returns 200
- trigger a test message to the INKA endpoint and verify response
- verify logs show DB connection and LLM usage/telemetry

If you'd like, I can run the deploy now (I will prompt you for any missing values), or you can run the script locally and I can help debug any errors reported.
