# Setting up Cloud SQL (Postgres) and Cloud Run for Tattoo Bot

This document outlines the steps required to create a Cloud SQL (Postgres) instance, initialize a database, create users, store secrets in Secret Manager, and deploy the Tattoo Bot to Cloud Run.

⚠️ Security note: Do not share your real secrets (Bot token, OpenAI key, DB credentials). Use Secret Manager and restrict permissions.

## 1) Prepare GCP environment

1. Ensure you have the Google Cloud SDK (gcloud) installed and authenticated:

```bash
gcloud auth login
gcloud config set project tattoo-480007
```

## 2) Create Postgres Cloud SQL instance

Change region / machine size as needed.

```bash
gcloud sql instances create tattoo-db \
  --project=tattoo-480007 \
  --database-version=POSTGRES_15 \
  --tier=db-custom-1-3840 \
  --region=us-central1

gcloud sql databases create tattoo_salon --instance=tattoo-db
```

## 3) Create database user

```bash
DB_PASSWORD="$(openssl rand -base64 24)"
gcloud sql users create tattoo_user --instance=tattoo-db --password="$DB_PASSWORD"

# Save the password (store securely). We'll store it in Secret Manager in the next step.
```

## 4) Store secrets in Secret Manager (recommended)

```bash
# BOT_TOKEN and OPENAI_API_KEY should be created with your real values
echo -n "<your_bot_token>" | gcloud secrets create BOT_TOKEN --replication-policy="automatic" --data-file=-
echo -n "<your_openai_key>" | gcloud secrets create OPENAI_API_KEY --replication-policy="automatic" --data-file=-
echo -n "$DB_PASSWORD" | gcloud secrets create CLOUDSQL_PASSWORD --replication-policy="automatic" --data-file=-
```

Optionally create a DATABASE_URL secret to make life easier for database initialization:

```bash
DATABASE_URL="postgresql+psycopg2://tattoo_user:${DB_PASSWORD}@/tattoo_salon?host=/cloudsql/tattoo-480007:us-central1:tattoo-db"
echo -n "$DATABASE_URL" | gcloud secrets create DATABASE_URL --replication-policy="automatic" --data-file=-
```

## 5) Deploy to Cloud Run with Cloud SQL connection

Use the `deploy_cloudrun_postgres.sh` script we added. It will deploy and wire secrets.

Before running, ensure you created BOT_TOKEN and OPENAI_API_KEY in Secret Manager (and CLOUDSQL_PASSWORD). The script optionally asks to create DATABASE_URL.

```bash
chmod +x deploy_cloudrun_postgres.sh
./deploy_cloudrun_postgres.sh
```

Alternatively, you can fully automate infrastructure using Terraform (recommended for production). See `infra/terraform/README.md` for usage.

CI & predeploy checks
----------------------
This repo provides a GitHub Actions workflow in `.github/workflows/ci.yml` that runs predeploy checks and `validate_env.py`. If you use Cloud Build, the repository `cloudbuild.yaml` already runs `scripts/predeploy_check.py` during the build.


## 6) Validate DB & schema

After deployment, check logs to make sure `init_postgres` ran successfully and schema was created. If you used DATABASE_URL secret the schema init will run automatically.

```bash
gcloud run logs read --service=tattoo-bot --region=us-central1
```

If the schema did not initialize, manually connect via Cloud SQL Proxy from your laptop and run `src/db/init_postgres.py` or use psql to apply schema.

## Interactive secret creation & deploy (recommended step-by-step)

1. Authenticate with Google Cloud CLI:

```bash
gcloud auth login
gcloud config set project tattoo-480007
gcloud auth application-default login
```

2. Run the interactive secrets helper and paste your secrets when prompted:

```bash
chmod +x scripts/import_secrets_interactive.sh
./scripts/import_secrets_interactive.sh
```

3. Run the full deploy check that deploys and validates the stack:

```bash
chmod +x scripts/full_deploy_check.sh
./scripts/full_deploy_check.sh
```

This will run the predeploy checks, optionally create the DB if needed, deploy to Cloud Run, seed admins, and check health.

## 7) Configure Telegram webhook

Replace <YOUR_BOT_TOKEN> and <SERVICE_URL> accordingly:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<SERVICE_URL>/webhook/telegram"
```

## 8) Testing

1. Send the Bot a message and check logs:

```bash
gcloud run logs read --service=tattoo-bot --region=us-central1
```

2. Use `psql` or Cloud Run admin tools to check data in `tattoo_salon`.

---
If you prefer more control, create the database and users manually and then update `deploy_cloudrun.sh` accordingly.

## 9) Full deploy validation helper

To run the entire validation/deploy flow (including seeding admin users and DB checks), use the helper script:

```bash
chmod +x scripts/full_deploy_check.sh
./scripts/full_deploy_check.sh
```

This will run the pre-deploy checks, deploy the service, seed admins from `ADMIN_USER_IDS`, and run a health-check.
