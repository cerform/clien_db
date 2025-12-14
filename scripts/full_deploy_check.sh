#!/bin/bash
set -euo pipefail

# Full deployment check & run script
# This script ties together predeploy checks, deployment, DB seeding, migrations checks, and health checks.

PROJECT_ID=${PROJECT_ID:-tattoo-480007}
REGION=${REGION:-us-central1}
SERVICE=${SERVICE:-tattoo-bot}

echo "🔍 Running pre-deploy checks..."
python3 scripts/predeploy_check.py || { echo "Predeploy checks failed — please fix failing items"; exit 2; }

echo "🔧 Validating environment..."
python3 scripts/validate_env.py || echo "Validation may have found missing env vars. Continue?"

echo "🚀 Deploying service..."
./deploy_cloudrun_postgres.sh

echo "⏳ Waiting a bit for deployment to finish..."
sleep 30

SERVICE_URL=$(gcloud run services describe ${SERVICE} --region=${REGION} --format='value(status.url)')
echo "Service URL: ${SERVICE_URL}"

echo "🌱 Seeding admins..."
python3 scripts/seed_admins.py || echo "Admin seeding failed or skipped"

echo "🔎 Checking DB migrations (tables presence)..."
python3 scripts/check_db_migrations.py || echo "DB migration check failed; ensure init_postgres ran"

echo "💚 Health check..."
./scripts/health_check.sh ${SERVICE_URL} || { echo "Health check failed; inspect logs"; exit 3; }

echo "✅ Full deploy & validation completed!"
#!/bin/bash
set -euo pipefail

# Full end-to-end deployment check
# 1) Validate env
# 2) Build and deploy Cloud Run
# 3) Seed admins
# 4) Validate DB schema
# 5) Check service health

if [ -f .env ]; then
    set -o allexport
    source .env
    set +o allexport
fi

echo "1) Validating environment..."
python3 scripts/predeploy_check.py
python3 scripts/validate_env.py

echo "2) Deploying..."
chmod +x deploy_cloudrun_postgres.sh
./deploy_cloudrun_postgres.sh

SERVICE_URL=$(gcloud run services describe tattoo-bot --region=us-central1 --format='value(status.url)')
echo "Service URL: ${SERVICE_URL}"

echo "3) Waiting for service to warm up..."
sleep 10

echo "4) Seeding admin users..."
python3 scripts/seed_admins.py || true

echo "5) Validating DB migrations..."
python3 scripts/check_db_migrations.py || true

echo "6) Health-checking service..."
./scripts/health_check.sh ${SERVICE_URL}

echo "All done"
