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

echo -e "\n${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Process completed!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}\n"
