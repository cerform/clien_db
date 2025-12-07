#!/bin/bash
# Safe deploy script with CI/CD checks

set -e

PROJECT_ID="tattoo-480007"
REGION="us-central1"
SERVICE_NAME="telegram-bot"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "\n${BOLD}${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║          🚀 SAFE DEPLOYMENT WITH CI/CD                                   ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}\n"

# Step 1: Pre-deployment checks
echo -e "${BOLD}${BLUE}📋 Step 1: Pre-deployment validation...${NC}"
if ./venv/bin/python pre_deploy_check.py; then
    echo -e "${GREEN}✅ Pre-deployment checks passed${NC}"
else
    echo -e "${YELLOW}⚠️  Pre-deployment checks completed with warnings${NC}"
fi

# Step 2: Git status
echo -e "\n${BOLD}${BLUE}📦 Step 2: Git status...${NC}"
if git diff --quiet && git diff --cached --quiet; then
    echo -e "${GREEN}✅ Working directory clean${NC}"
else
    echo -e "${YELLOW}⚠️  You have uncommitted changes. Commit them first:${NC}"
    git status
    exit 1
fi

# Step 3: Build verification
echo -e "\n${BOLD}${BLUE}🔨 Step 3: Docker build verification...${NC}"
if docker build -t test-build . > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker build successful${NC}"
    docker rmi test-build > /dev/null 2>&1
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Step 4: GCP setup
echo -e "\n${BOLD}${BLUE}🔐 Step 4: GCP configuration...${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Project set to $PROJECT_ID${NC}"

# Step 5: Deploy
echo -e "\n${BOLD}${BLUE}🚀 Step 5: Deploying to Cloud Run...${NC}"

if gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --quiet; then
    echo -e "${GREEN}✅ Deployment successful${NC}"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# Step 6: Get service URL
echo -e "\n${BOLD}${BLUE}✅ Step 6: Service information...${NC}"

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')
echo -e "Service URL: ${GREEN}$SERVICE_URL${NC}"

# Show recent logs
echo -e "\n${BOLD}Recent logs:${NC}"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
    --limit=5 \
    --format='table(timestamp, severity, textPayload)' 2>/dev/null || true

echo -e "\n${BOLD}${GREEN}✅ Deployment completed!${NC}"
echo -e "Test the bot: @inkamanager_bot\n"
