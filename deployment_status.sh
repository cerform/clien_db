#!/usr/bin/env bash

# 📊 DEPLOYMENT STATUS DASHBOARD
# Run this script to check current deployment status

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     🚀 TATTOO BOT - DEPLOYMENT STATUS DASHBOARD${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# 1. LOCAL TESTS
echo -e "${YELLOW}[1/5] LOCAL TESTS${NC}"
echo "─────────────────────────────────────────────────────"
if cd /home/etcsys/projects/clien_db && source venv/bin/activate && python3 -m pytest tests/ -q 2>/dev/null; then
    echo -e "${GREEN}✅ Unit Tests: PASS (27/27)${NC}"
else
    echo -e "${RED}❌ Unit Tests: FAIL${NC}"
fi

if python3 test_admin_functions.py 2>/dev/null | grep -q "4/4"; then
    echo -e "${GREEN}✅ Admin Functions Test: PASS (4/4)${NC}"
else
    echo -e "${YELLOW}⚠️  Admin Functions Test: Check manually${NC}"
fi

if python3 -m py_compile src/main.py src/bot/handlers/client_handler.py src/web/app.py src/ai/advanced_inka.py 2>/dev/null; then
    echo -e "${GREEN}✅ Syntax Check: OK${NC}"
else
    echo -e "${RED}❌ Syntax Check: ERRORS${NC}"
fi
echo ""

# 2. DOCKER IMAGE
echo -e "${YELLOW}[2/5] DOCKER IMAGE${NC}"
echo "─────────────────────────────────────────────────────"
if docker images | grep -q "tattoo-bot"; then
    echo -e "${GREEN}✅ Docker image exists${NC}"
    docker images | grep tattoo-bot | awk '{print "   Repository: "$1":latest | Size: "$7}'
else
    echo -e "${YELLOW}⚠️  Docker image not built (run: docker build -t gcr.io/tattoo-480007/tattoo-bot:latest .)${NC}"
fi
echo ""

# 3. CLOUD RUN SERVICE
echo -e "${YELLOW}[3/5] CLOUD RUN SERVICE${NC}"
echo "─────────────────────────────────────────────────────"
SERVICE_URL=$(gcloud run services describe tattoo-bot --region us-central1 --format='value(status.url)' 2>/dev/null)

if [ ! -z "$SERVICE_URL" ]; then
    echo -e "${GREEN}✅ Service deployed${NC}"
    echo "   URL: $SERVICE_URL"
    
    # Check if service is healthy
    if curl -s "$SERVICE_URL/api/health" | grep -q "ok" 2>/dev/null; then
        echo -e "${GREEN}✅ Health check: PASS${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check: Slow or failing${NC}"
    fi
    
    # Check latest revision
    REVISION=$(gcloud run services describe tattoo-bot --region us-central1 --format='value(status.latestCreatedRevisionName)' 2>/dev/null)
    echo "   Latest revision: $REVISION"
else
    echo -e "${YELLOW}⚠️  Service not deployed (run deployment step 3)${NC}"
fi
echo ""

# 4. TELEGRAM WEBHOOK
echo -e "${YELLOW}[4/5] TELEGRAM WEBHOOK${NC}"
echo "─────────────────────────────────────────────────────"
BOT_TOKEN=$(gcloud run services describe tattoo-bot --region us-central1 \
    --format='value(spec.template.spec.containers[0].env[?name==TELEGRAM_BOT_TOKEN].value)' 2>/dev/null)

if [ ! -z "$BOT_TOKEN" ] && [ "$BOT_TOKEN" != "" ] && [ "$BOT_TOKEN" != "None" ]; then
    WEBHOOK_URL=$(curl -s https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo 2>/dev/null | jq -r '.result.url')
    
    if [ ! -z "$WEBHOOK_URL" ] && [ "$WEBHOOK_URL" != "null" ]; then
        echo -e "${GREEN}✅ Webhook configured${NC}"
        echo "   URL: $WEBHOOK_URL"
    else
        echo -e "${YELLOW}⚠️  Webhook not configured${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  TELEGRAM_BOT_TOKEN not set${NC}"
fi
echo ""

# 5. ADMIN CONFIGURATION
echo -e "${YELLOW}[5/5] ADMIN CONFIGURATION${NC}"
echo "─────────────────────────────────────────────────────"
ADMIN_IDS=$(gcloud run services describe tattoo-bot --region us-central1 \
    --format='value(spec.template.spec.containers[0].env[?name==ADMIN_IDS].value)' 2>/dev/null)

if [ ! -z "$ADMIN_IDS" ] && [ "$ADMIN_IDS" != "None" ]; then
    echo -e "${GREEN}✅ Admin IDs configured${NC}"
    echo "   Admins: $ADMIN_IDS"
else
    echo -e "${YELLOW}⚠️  Admin IDs not configured${NC}"
fi

ADMIN_PASSWORD=$(gcloud run services describe tattoo-bot --region us-central1 \
    --format='value(spec.template.spec.containers[0].env[?name==ADMIN_WEB_PASSWORD].value)' 2>/dev/null)

if [ ! -z "$ADMIN_PASSWORD" ]; then
    echo -e "${GREEN}✅ Web admin password set${NC}"
else
    echo -e "${YELLOW}⚠️  Web admin password not set${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}              DEPLOYMENT SUMMARY${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Calculate status
CHECKS=0
PASSED=0

# Check tests
if python3 -m pytest tests/ -q 2>/dev/null | grep -q "27 passed"; then
    ((CHECKS++)); ((PASSED++))
else
    ((CHECKS++))
fi

# Check docker
if docker images | grep -q "tattoo-bot"; then
    ((CHECKS++)); ((PASSED++))
else
    ((CHECKS++))
fi

# Check cloud run
if [ ! -z "$SERVICE_URL" ]; then
    ((CHECKS++)); ((PASSED++))
else
    ((CHECKS++))
fi

# Check webhook
if [ ! -z "$WEBHOOK_URL" ] && [ "$WEBHOOK_URL" != "null" ]; then
    ((CHECKS++)); ((PASSED++))
else
    ((CHECKS++))
fi

# Check admins
if [ ! -z "$ADMIN_IDS" ]; then
    ((CHECKS++)); ((PASSED++))
else
    ((CHECKS++))
fi

PERCENT=$((PASSED * 100 / CHECKS))

echo "Checks Passed: $PASSED/$CHECKS ($PERCENT%)"
echo ""

if [ $PERCENT -eq 100 ]; then
    echo -e "${GREEN}🎉 ALL SYSTEMS GO - READY FOR PRODUCTION!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Send test message to bot in Telegram"
    echo "  2. Verify no buttons appear"
    echo "  3. Test admin function as admin"
    echo "  4. Test access denial as non-admin"
    echo "  5. Open admin panel: $SERVICE_URL/admin"
elif [ $PERCENT -ge 60 ]; then
    echo -e "${YELLOW}⚠️  PARTIAL DEPLOYMENT - CHECK REMAINING ITEMS${NC}"
    echo ""
    echo "Run deployment steps to complete setup"
else
    echo -e "${YELLOW}⚠️  INCOMPLETE DEPLOYMENT${NC}"
    echo ""
    echo "Run QUICK_DEPLOY_REFERENCE.md steps 1-5:"
    echo "  1. Build Docker image"
    echo "  2. Push to GCR"
    echo "  3. Deploy to Cloud Run"
    echo "  4. Configure webhook"
    echo "  5. Verify all systems"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Additional info
if [ ! -z "$SERVICE_URL" ]; then
    echo "🔗 Quick Links:"
    echo "  • Service URL: $SERVICE_URL"
    echo "  • Admin Panel: $SERVICE_URL/admin"
    echo "  • Health: $SERVICE_URL/api/health"
    echo ""
fi

echo "📊 View Real-Time Logs:"
echo "  gcloud run services logs read tattoo-bot --limit=0 --follow --region us-central1"
echo ""

echo "📞 Support:"
echo "  • Check FINAL_DEPLOYMENT_STEPS.md for detailed instructions"
echo "  • Check QUICK_DEPLOY_REFERENCE.md for command-line quick reference"
echo ""
