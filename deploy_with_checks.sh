#!/bin/bash

###############################################################################
# 🚀 Deploy with Pre-deployment Checks
# Проверяет все критические компоненты перед деплоем в Cloud Run
###############################################################################

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_ID="tattoo-480007"
SERVICE_NAME="telegram-bot"
REGION="us-central1"
MEMORY="512Mi"

echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}🔍 PRE-DEPLOYMENT CHECKS${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}\n"

# Check 1: Python syntax errors
echo -e "${YELLOW}✓ Check 1: Python Syntax${NC}"
python3 -m py_compile src/services/data_sync.py 2>/dev/null && \
    echo -e "${GREEN}  ✅ No syntax errors in data_sync.py${NC}" || \
    { echo -e "${RED}  ❌ Syntax errors found${NC}"; exit 1; }

python3 -m py_compile src/ai/advanced_inka.py 2>/dev/null && \
    echo -e "${GREEN}  ✅ No syntax errors in advanced_inka.py${NC}" || \
    { echo -e "${RED}  ❌ Syntax errors found${NC}"; exit 1; }

# Check 2: Required files exist
echo -e "\n${YELLOW}✓ Check 2: Required Files${NC}"
REQUIRED_FILES=(
    "requirements.txt"
    "src/main.py"
    "src/config/config.py"
    "Dockerfile"
    "credentials.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file${NC}"
    else
        echo -e "${RED}  ❌ Missing: $file${NC}"
        exit 1
    fi
done

# Check 3: Environment variables
echo -e "\n${YELLOW}✓ Check 3: Environment Variables${NC}"
REQUIRED_ENV=(
    "GOOGLE_PROJECT_ID"
    "GOOGLE_SPREADSHEET_ID"
    "TELEGRAM_BOT_TOKEN"
    "OPENAI_API_KEY"
)

MISSING_ENV=0
for env_var in "${REQUIRED_ENV[@]}"; do
    if [ -z "${!env_var}" ]; then
        echo -e "${YELLOW}  ⚠️  ${env_var} not set (will check in .env)${NC}"
        ((MISSING_ENV++))
    else
        echo -e "${GREEN}  ✅ ${env_var}${NC}"
    fi
done

if [ $MISSING_ENV -gt 0 ] && [ ! -f ".env" ]; then
    echo -e "${RED}  ❌ Missing .env file with credentials${NC}"
    exit 1
fi

# Check 4: Docker is available
echo -e "\n${YELLOW}✓ Check 4: Docker${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}  ✅ Docker installed: $DOCKER_VERSION${NC}"
else
    echo -e "${RED}  ❌ Docker not found${NC}"
    exit 1
fi

# Check 5: gcloud is available
echo -e "\n${YELLOW}✓ Check 5: Google Cloud SDK${NC}"
if command -v gcloud &> /dev/null; then
    GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "not set")
    echo -e "${GREEN}  ✅ gcloud installed (project: $GCLOUD_PROJECT)${NC}"
else
    echo -e "${RED}  ❌ gcloud not found${NC}"
    exit 1
fi

# Check 6: Git status
echo -e "\n${YELLOW}✓ Check 6: Git Repository${NC}"
if [ -d ".git" ]; then
    STATUS=$(git status --short)
    if [ -z "$STATUS" ]; then
        echo -e "${GREEN}  ✅ Working directory clean${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Uncommitted changes:${NC}"
        echo "$STATUS" | sed 's/^/     /'
        read -p "  Continue with uncommitted changes? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}  ❌ Deployment cancelled${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}  ⚠️  Not a git repository${NC}"
fi

# Check 7: requirements.txt integrity
echo -e "\n${YELLOW}✓ Check 7: Python Dependencies${NC}"
if [ -f "requirements.txt" ]; then
    LINES=$(wc -l < requirements.txt)
    echo -e "${GREEN}  ✅ requirements.txt has $LINES dependencies${NC}"
    
    # Check for common issues
    if grep -q "^$" requirements.txt; then
        echo -e "${YELLOW}  ⚠️  Empty lines found in requirements.txt${NC}"
    fi
else
    echo -e "${RED}  ❌ requirements.txt not found${NC}"
    exit 1
fi

# Check 8: Dockerfile validation
echo -e "\n${YELLOW}✓ Check 8: Dockerfile${NC}"
if grep -q "CMD" Dockerfile && grep -q "FROM" Dockerfile; then
    echo -e "${GREEN}  ✅ Dockerfile appears valid${NC}"
else
    echo -e "${RED}  ❌ Dockerfile missing required instructions${NC}"
    exit 1
fi

# Check 9: Unit tests
echo -e "\n${YELLOW}✓ Check 9: Unit Tests${NC}"
if command -v pytest &> /dev/null; then
    pytest -q || { echo -e "${RED}  ❌ Unit tests failed${NC}"; exit 1; }
    echo -e "${GREEN}  ✅ All tests passed${NC}"
else
    echo -e "${YELLOW}  ⚠️ pytest not installed — skipping unit tests${NC}"
fi

# Check 10: Optional local server checks (requires GOOGLE_CREDENTIALS_JSON, GOOGLE_SPREADSHEET_ID)
echo -e "\n${YELLOW}✓ Check 10: Local server health checks (optional)${NC}"
if [ -f ".env" ]; then
    source .env
fi
if [ -n "$GOOGLE_CREDENTIALS_JSON" ] && [ -n "$GOOGLE_SPREADSHEET_ID" ]; then
    echo -e "  🔎 Credentials and spreadsheet detected — starting local server tests..."
    UVICORN_LOG=uvicorn_deploy_check.log
    # Run uvicorn in background
    nohup python3 -m uvicorn src.web.app:create_app --factory --host 127.0.0.1 --port 8000 > $UVICORN_LOG 2>&1 &
    UVICORN_PID=$!
    echo -e "  ▶️ Started uvicorn (pid: $UVICORN_PID), waiting for start..."
    # Wait for health start
    OK=0
    for i in {1..20}; do
        sleep 1
        if curl -s http://127.0.0.1:8000/api/health >/dev/null 2>&1 || curl -s http://127.0.0.1:8000/ >/dev/null 2>&1; then
            OK=1
            break
        fi
    done
    if [ $OK -eq 0 ]; then
        echo -e "${YELLOW}  ⚠️ Local server didn't respond — skipping endpoint checks${NC}"
    else
        echo -e "${GREEN}  ✅ Local server up — running endpoint checks${NC}"
        # Check admin page and db-manager
        endpoints=("/admin" "/admin/db-manager" "/api/sheets")
        for ep in "${endpoints[@]}"; do
            echo -e "    ⤷ Checking http://127.0.0.1:8000${ep}"
            # Use GET and print only status code to avoid issues with HEAD returning 405
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8000${ep})
            if [ "$ep" == "/admin" ] || [ "$ep" == "/admin/db-manager" ]; then
                # Accept 200 OK or 302 Redirect (to login/dashboard)
                if [ "$STATUS" == "200" ] || [ "$STATUS" == "302" ]; then
                    echo -e "      ${GREEN}${STATUS} OK${NC}"
                else
                    echo -e "      ${RED}${STATUS} FAILED${NC}"
                fi
            else
                # Default check: expect 200
                if [ "$STATUS" == "200" ]; then
                    echo -e "      ${GREEN}200 OK${NC}"
                else
                    echo -e "      ${RED}${STATUS} FAILED${NC}"
                fi
            fi
        done
    fi
    # Kill uvicorn
    kill $UVICORN_PID || true
    echo -e "  🛑 Local server stopped"
else
    echo -e "  ⚠️ Missing spreadsheet credentials — skipping local sheet checks${NC}"
fi


# Check 11: DB Format Validation (Google Sheets)
echo -e "\n${YELLOW}✓ Check 11: DB Format Validation${NC}"
python3 validate_db_format.py || { echo -e "${RED}  ❌ DB format validation failed${NC}"; exit 1; }

# Summary
echo -e "\n${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All pre-deployment checks passed!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}\n"

# Deployment
echo -e "${BOLD}🚀 Starting deployment...${NC}\n"

if [ "$1" == "--dry-run" ]; then
    echo -e "${YELLOW}DRY RUN MODE - Not actually deploying${NC}"
    echo -e "\n${BOLD}Would deploy:${NC}"
    echo -e "  Project: ${BOLD}$PROJECT_ID${NC}"
    echo -e "  Service: ${BOLD}$SERVICE_NAME${NC}"
    echo -e "  Region: ${BOLD}$REGION${NC}"
    echo -e "  Memory: ${BOLD}$MEMORY${NC}"
    exit 0
fi

# Actual deployment
echo -e "${BOLD}📦 Building and deploying to Cloud Run...${NC}\n"

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --memory $MEMORY \
    --project $PROJECT_ID \
    --quiet \
    2>&1 | tee deployment.log

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Deployment successful!${NC}"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region $REGION \
        --project $PROJECT_ID \
        --format='value(status.url)' 2>/dev/null || echo "URL not available")
    
    echo -e "\n${BOLD}Service Details:${NC}"
    echo -e "  URL: ${BOLD}$SERVICE_URL${NC}"
    echo -e "  Region: ${BOLD}$REGION${NC}"
    echo -e "  Memory: ${BOLD}$MEMORY${NC}"
    
    echo -e "\n${BOLD}📝 Check logs:${NC}"
    echo -e "  ${YELLOW}gcloud run logs read $SERVICE_NAME --region=$REGION --limit=50${NC}"
    
else
    echo -e "\n${RED}❌ Deployment failed!${NC}"
    echo -e "${YELLOW}Check deployment.log for details${NC}"
    exit 1
fi

# ============== POST-DEPLOY: Smoke tests on deployed service ==============
if [ -n "$SERVICE_URL" ] && [ "$1" != "--dry-run" ]; then
    echo -e "\n${YELLOW}🚨 POST-DEPLOY: Service smoke tests${NC}"
    # Remove trailing slash if present
    SERVICE_BASE=${SERVICE_URL%/}
    sleep 3
    # try up to 20 times for health to be ready
    for i in {1..20}; do
        echo -e "  ▶️ Checking health (attempt $i)"
        if curl -s "$SERVICE_BASE/api/health" | grep -q "ok"; then
            echo -e "    ${GREEN}Health OK${NC}"
            break
        fi
        sleep 3
    done

    # Check admin page(s)
    echo -e "  ▶️ Checking /admin and /admin/db-manager"
    if curl -sI "$SERVICE_BASE/admin" | grep -q "200"; then
        echo -e "    ${GREEN}/admin OK${NC}"
    else
        echo -e "    ${RED}/admin FAILED${NC}"
    fi

    if curl -sI "$SERVICE_BASE/admin/db-manager" | grep -q "200"; then
        echo -e "    ${GREEN}/admin/db-manager OK${NC}"
    else
        echo -e "    ${YELLOW}/admin/db-manager WARNING: maybe requires auth, check manually${NC}"
    fi

    # Check API sheets (may require spreadsheet credentials; note that a 500 here might be okay if credentials missing)
    echo -e "  ▶️ Checking /api/sheets"
    # Use GET to retrieve a status code for /api/sheets; a 200 means sheets are accessible.
    RES=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$SERVICE_BASE/api/sheets")
    if [ "$RES" == "200" ]; then
        echo -e "    ${GREEN}/api/sheets OK${NC}"
    elif [ "$RES" == "500" ]; then
        # 500 might indicate missing credentials or internal server error; keep as warning
        echo -e "    ${YELLOW}/api/sheets POST-DEPLOY WARNING: status: $RES (may require credentials)${NC}"
    else
        echo -e "    ${RED}/api/sheets FAILED: status $RES${NC}"
    fi
fi

echo -e "\n${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Process completed!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}\n"
