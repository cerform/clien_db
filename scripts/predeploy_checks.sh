#!/bin/bash
set -e

echo "🔍 Pre-Deploy Checks Starting..."
echo "================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Required files exist
echo -e "\n${YELLOW}1. Checking required files...${NC}"
REQUIRED_FILES=(
    "run_production.py"
    "requirements.txt"
    "src/config/constants.py"
    "src/auth/roles.py"
    "src/services/user_manager.py"
    "scripts/create_user.py"
    "Procfile"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file - MISSING!"
        exit 1
    fi
done

# Check 2: Python syntax
echo -e "\n${YELLOW}2. Checking Python syntax...${NC}"
source .venv/bin/activate
python3 -m py_compile run_production.py
python3 -m py_compile src/auth/roles.py
python3 -m py_compile src/services/user_manager.py
python3 -m py_compile scripts/create_user.py
echo -e "  ${GREEN}✓${NC} All Python files valid"

# Check 3: Required environment variables in secrets
echo -e "\n${YELLOW}3. Checking Secret Manager secrets...${NC}"
REQUIRED_SECRETS=(
    "telegram-bot-token"
    "openai-api-key"
    "database-url"
)

for secret in "${REQUIRED_SECRETS[@]}"; do
    if gcloud secrets describe "$secret" --project=tattoo-480007 &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $secret exists"
    else
        echo -e "  ${RED}✗${NC} $secret - MISSING!"
        exit 1
    fi
done

# Check 4: Service account has required permissions
echo -e "\n${YELLOW}4. Checking service account permissions...${NC}"
SA_EMAIL="telegram-bot-sa@tattoo-480007.iam.gserviceaccount.com"

# Check if SA can access secrets
if gcloud secrets get-iam-policy database-url --project=tattoo-480007 | grep -q "$SA_EMAIL"; then
    echo -e "  ${GREEN}✓${NC} Secret Manager access"
else
    echo -e "  ${RED}✗${NC} Missing Secret Manager access"
    exit 1
fi

# Check if SA has Cloud SQL Client role
if gcloud projects get-iam-policy tattoo-480007 | grep -q "roles/cloudsql.client" | grep -q "$SA_EMAIL"; then
    echo -e "  ${GREEN}✓${NC} Cloud SQL Client role"
else
    echo -e "  ${YELLOW}⚠${NC}  Cloud SQL Client role might be missing (proceeding anyway)"
fi

# Check 5: Cloud SQL instance is running
echo -e "\n${YELLOW}5. Checking Cloud SQL instance...${NC}"
INSTANCE_STATE=$(gcloud sql instances describe tattoo-db --project=tattoo-480007 --format="value(state)" 2>&1)
if [ "$INSTANCE_STATE" = "RUNNABLE" ]; then
    echo -e "  ${GREEN}✓${NC} Cloud SQL instance is RUNNABLE"
else
    echo -e "  ${RED}✗${NC} Cloud SQL instance state: $INSTANCE_STATE"
    exit 1
fi

# Ensure DATABASE_URL exists; construct from env vars if not provided
if [ -z "$DATABASE_URL" ]; then
    DB_USER=${CLOUDSQL_USER:-tattoo_user}
    DB_PASS=${CLOUDSQL_PASSWORD:-}
    DB_HOST=${CLOUDSQL_HOST:-127.0.0.1}
    DB_PORT=${CLOUDSQL_PORT:-5432}
    DB_NAME=${CLOUDSQL_DB:-tattoo_salon}
    if [ -z "$DB_PASS" ]; then
        echo -e "  ${YELLOW}⚠${NC} CLOUDSQL_PASSWORD is not set, trying to continue (may fail)"
    fi
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASS@${DB_HOST}:${DB_PORT}/${DB_NAME}"
fi

# Option: if you want to use Cloud SQL Proxy, set USE_CLOUDSQL_PROXY=true (default). For local Postgres, set it false and set CLOUDSQL_HOST/PORT.
USE_CLOUDSQL_PROXY=${USE_CLOUDSQL_PROXY:-true}

# Check 6: Database exists and has required tables
echo -e "\n${YELLOW}6. Checking database tables (via proxy)...${NC}"

# Start proxy if not running
if [ "$USE_CLOUDSQL_PROXY" = "true" ]; then
    if ! pgrep -f "cloud_sql_proxy.*tattoo-db" > /dev/null; then
            echo "  Starting Cloud SQL Proxy..."
            ./cloud_sql_proxy -instances=tattoo-480007:us-central1:tattoo-db=tcp:5432 > /dev/null 2>&1 &
            PROXY_PID=$!
            sleep 5
            STOP_PROXY=true
    else
            echo "  Proxy already running"
            STOP_PROXY=false
    fi
else
    echo "  Skipping Cloud SQL Proxy because USE_CLOUDSQL_PROXY=$USE_CLOUDSQL_PROXY"
    STOP_PROXY=false
fi

# Check tables

REQUIRED_TABLES=("masters" "clients" "bookings")
for table in "${REQUIRED_TABLES[@]}"; do
    if python3 -c "
from src.db.cloudsql_client import CloudSQLClient
client = CloudSQLClient()
result = client.execute_query('SELECT 1 FROM information_schema.tables WHERE table_name = %s', ('$table',))
exit(0 if result else 1)
" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Table '$table' exists"
    else
        echo -e "  ${RED}✗${NC} Table '$table' missing!"
        [ "$STOP_PROXY" = true ] && kill $PROXY_PID 2>/dev/null
        exit 1
    fi
done

# Check masters table has required columns
echo -e "\n${YELLOW}7. Checking masters table schema...${NC}"
REQUIRED_COLUMNS=("username" "password_hash" "role" "is_active")
for column in "${REQUIRED_COLUMNS[@]}"; do
    if python3 -c "
from src.db.cloudsql_client import CloudSQLClient
client = CloudSQLClient()
result = client.execute_query('SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s', ('masters', '$column'))
exit(0 if result else 1)
" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Column '$column' exists"
    else
        echo -e "  ${RED}✗${NC} Column '$column' missing!"
        [ "$STOP_PROXY" = true ] && kill $PROXY_PID 2>/dev/null
        exit 1
    fi
done

# Stop proxy if we started it
if [ "$STOP_PROXY" = true ]; then
    kill $PROXY_PID 2>/dev/null
    echo "  Stopped proxy"
fi

# Check 8: Docker/Cloud Build setup
echo -e "\n${YELLOW}8. Checking deployment configuration...${NC}"
if [ -f "Procfile" ]; then
    PROCFILE_CMD=$(cat Procfile | grep "^web:")
    echo -e "  ${GREEN}✓${NC} Procfile exists: $PROCFILE_CMD"
else
    echo -e "  ${RED}✗${NC} Procfile missing!"
    exit 1
fi

if [ -f "run_production.py" ] || [ -f "run.py" ]; then
    echo -e "  ${GREEN}✓${NC} Production entrypoint exists"
else
    echo -e "  ${RED}✗${NC} Production entrypoint missing!"
    exit 1
fi

# Final summary
echo -e "\n================================="
echo -e "${GREEN}✓ All pre-deploy checks passed!${NC}"
echo -e "================================="
echo ""
echo "Ready to deploy with:"
echo "  gcloud run deploy telegram-bot \\"
echo "    --source . \\"
echo "    --region us-central1 \\"
echo "    --service-account telegram-bot-sa@tattoo-480007.iam.gserviceaccount.com \\"
echo "    --add-cloudsql-instances tattoo-480007:us-central1:tattoo-db"
echo ""
