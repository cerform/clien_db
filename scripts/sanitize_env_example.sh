#!/bin/bash
set -euo pipefail

EXAMPLE_FILE=".env.deploy.example"

echo "Sanitizing ${EXAMPLE_FILE}..."

cat > ${EXAMPLE_FILE} <<'EOF'
### Example deploy env - DO NOT STORE REAL SECRETS IN REPO
BOT_TOKEN=
OPENAI_API_KEY=
SPREADSHEET_ID=
WEBHOOK_SECRET=
ADMIN_USER_IDS=123456789
CLOUDSQL_PASSWORD=
DATABASE_URL=

# Add any other deploy-time env vars here. Keep real values in Secret Manager.
EOF

echo "Wrote sanitized ${EXAMPLE_FILE}."

exit 0
