#!/bin/bash
# Cloud SQL Proxy & Migration Automation Script

set -e

PROJECT_ID="tattoo-480007"
INSTANCE="tattoo-bot-db"
REGION="us-central1"
DB_NAME="admin_messages"
DB_USER="root"
DB_PASS="your-password"
CREDENTIALS_FILE="credentials.json"
PORT=3306

# 1. Download Cloud SQL Proxy if not present
if ! [ -f ./cloud_sql_proxy ]; then
  wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
  chmod +x cloud_sql_proxy
fi

# 2. Start Cloud SQL Proxy in background
./cloud_sql_proxy -instances=${PROJECT_ID}:${REGION}:${INSTANCE}=tcp:${PORT} &
PROXY_PID=$!
echo "Cloud SQL Proxy started with PID $PROXY_PID"
sleep 5

# 3. Set environment variables
export CLOUDSQL_USER=${DB_USER}
export CLOUDSQL_PASSWORD=${DB_PASS}
export CLOUDSQL_DB=${DB_NAME}
export CLOUDSQL_HOST=127.0.0.1
export CLOUDSQL_PORT=${PORT}
export GOOGLE_CREDENTIALS=${CREDENTIALS_FILE}
export ADMIN_MESSAGES_SHEET="admin_messages"

# 4. Activate gcloud service account
gcloud auth activate-service-account --key-file=${CREDENTIALS_FILE}

# 4. Install Python dependencies
pip install sqlalchemy pymysql gspread google-auth

# 5. Initialize database and user
python scripts/setup_database.py

# 6. Migrate data from Google Sheets
python scripts/migrate_sheets_to_cloudsql.py

# 7. Stop Cloud SQL Proxy
kill $PROXY_PID

echo "Cloud SQL migration complete."
