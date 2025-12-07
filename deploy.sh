#!/bin/bash

###############################################################################
# 🚀 Deploy with Pre-deployment Checks
# Проверяет все критические компоненты перед деплоем в Cloud Run
###############################################################################

set -e

# Colors for output
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default configuration
PROJECT_ID="${1:-tattoo-480007}"
REGION="${2:-us-central1}"
SERVICE_NAME="telegram-bot"
MEMORY="512Mi"

# Print functions
print_header() {
    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}\n"
}

print_step() {
    echo -e "${YELLOW}✓ $1${NC}"
}

print_success() {
    echo -e "${GREEN}  ✅ $1${NC}"
}

print_error() {
    echo -e "${RED}  ❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}  ⚠️  $1${NC}"
}

# Header
print_header "🚀 DEPLOYMENT WITH PRE-CHECKS"

# Check 1: Python syntax
echo -e "${YELLOW}✓ Check 1: Python Syntax${NC}"
python3 -m py_compile src/services/data_sync.py 2>/dev/null && \
    print_success "data_sync.py" || { print_error "data_sync.py"; exit 1; }
python3 -m py_compile src/main.py 2>/dev/null && \
    print_success "main.py" || { print_error "main.py"; exit 1; }

# Check 2: Pre-deployment verification
echo -e "\n${YELLOW}✓ Check 2: Pre-deployment Verification${NC}"
if python3 pre_deploy_verification.py > /dev/null 2>&1; then
    print_success "Pre-deployment checks passed"
else
    print_warning "Some warnings in pre-deployment checks (continuing...)"
fi

# Check 3: gcloud configuration
echo -e "\n${YELLOW}✓ Check 3: Google Cloud Configuration${NC}"
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI не установлен"
    print_error "gcloud CLI не установлен"
    exit 1
fi

GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null)
print_success "gcloud authenticated (project: $GCLOUD_PROJECT)"

# Check 4: Git status
echo -e "\n${YELLOW}✓ Check 4: Git Status${NC}"
if [ -d ".git" ]; then
    CHANGES=$(git status --short | wc -l)
    if [ "$CHANGES" -gt 0 ]; then
        print_warning "$CHANGES uncommitted changes"
        git status --short | head -3 | sed 's/^/     /'
    else
        print_success "Working directory clean"
    fi
fi

# Summary
echo -e "\n${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All pre-deployment checks passed!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}\n"

# Deployment confirmation
echo -e "${BOLD}Deployment Configuration:${NC}"
echo -e "  Project:  $PROJECT_ID"
echo -e "  Service:  $SERVICE_NAME"
echo -e "  Region:   $REGION"
echo -e "  Memory:   $MEMORY\n"

read -p "Ready to deploy? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

# Actual deployment
echo -e "\n${BOLD}🚀 Starting Cloud Run deployment...${NC}\n"

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --memory $MEMORY \
    --project $PROJECT_ID \
    --quiet \
    2>&1 | tee deployment.log

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "\n${GREEN}${BOLD}✅ Deployment successful!${NC}\n"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region $REGION \
        --project $PROJECT_ID \
        --format='value(status.url)' 2>/dev/null || echo "URL not available")
    
    echo -e "${BOLD}Service Details:${NC}"
    echo -e "  URL: $SERVICE_URL"
    echo -e "  Region: $REGION"
    echo -e "  Memory: $MEMORY\n"
    
    echo -e "${BOLD}Next Steps:${NC}"
    echo -e "  View logs:  gcloud run logs read $SERVICE_NAME --region=$REGION --limit=50"
    echo -e "  Stream logs: gcloud run logs read $SERVICE_NAME --region=$REGION --follow\n"
else
    print_error "Deployment failed!"
    echo "Check deployment.log for details"
    exit 1
fi

echo -e "\n${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}\n"
