#!/bin/bash
set -e

echo "🔧 Настройка постоянного webhook для Telegram Bot"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get Cloud Run service URL
echo -e "\n${YELLOW}1. Получаю URL Cloud Run сервиса...${NC}"
SERVICE_URL=$(gcloud run services describe telegram-bot --region=us-central1 --format="value(status.url)" 2>/dev/null)

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}✗ Cloud Run сервис не найден или не развернут${NC}"
    echo "  Сначала запустите деплой:"
    echo "  gcloud run deploy telegram-bot --source . --region us-central1"
    exit 1
fi

echo -e "${GREEN}✓${NC} Service URL: $SERVICE_URL"

# Get bot token from Secret Manager
echo -e "\n${YELLOW}2. Получаю Telegram Bot Token из Secret Manager...${NC}"
BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token --project=tattoo-480007 2>/dev/null)

if [ -z "$BOT_TOKEN" ]; then
    echo -e "${RED}✗ Не удалось получить токен из Secret Manager${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Bot token получен"

# Webhook URL
WEBHOOK_URL="${SERVICE_URL}/webhook"
echo -e "\n${YELLOW}3. Webhook URL: ${WEBHOOK_URL}${NC}"

# Set webhook
echo -e "\n${YELLOW}4. Устанавливаю webhook в Telegram...${NC}"
RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"${WEBHOOK_URL}\",
    \"drop_pending_updates\": true,
    \"allowed_updates\": [\"message\", \"callback_query\", \"my_chat_member\"]
  }")

# Check if successful
if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo -e "${GREEN}✓${NC} Webhook установлен успешно!"
else
    echo -e "${RED}✗${NC} Ошибка установки webhook:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

# Get webhook info
echo -e "\n${YELLOW}5. Проверяю статус webhook...${NC}"
WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo")

echo "$WEBHOOK_INFO" | python3 -c "
import json
import sys
data = json.load(sys.stdin)
if data.get('ok'):
    result = data.get('result', {})
    print(f\"📊 Информация о webhook:\")
    print(f\"   URL: {result.get('url', 'не установлен')}\")
    print(f\"   Pending updates: {result.get('pending_update_count', 0)}\")
    if result.get('last_error_message'):
        print(f\"   ⚠️ Последняя ошибка: {result.get('last_error_message')}\")
        print(f\"      Время: {result.get('last_error_date')}\")
    else:
        print(f\"   ✅ Ошибок нет\")

    allowed = result.get('allowed_updates', [])
    print(f\"   Разрешенные обновления: {', '.join(allowed) if allowed else 'все'}\")
else:
    print(f\"❌ Ошибка: {data.get('description', 'неизвестная ошибка')}\")
"

# Save webhook URL to .env for local development
echo -e "\n${YELLOW}6. Сохраняю webhook URL в .env...${NC}"
if [ -f ".env" ]; then
    # Remove old WEBHOOK_URL if exists
    sed -i '/^WEBHOOK_URL=/d' .env 2>/dev/null || true
fi
echo "WEBHOOK_URL=${WEBHOOK_URL}" >> .env
echo -e "${GREEN}✓${NC} Webhook URL сохранен в .env"

# Test webhook
echo -e "\n${YELLOW}7. Тестирую webhook...${NC}"
TEST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${WEBHOOK_URL}")
if [ "$TEST_RESPONSE" = "200" ] || [ "$TEST_RESPONSE" = "405" ]; then
    echo -e "${GREEN}✓${NC} Webhook endpoint доступен (HTTP $TEST_RESPONSE)"
else
    echo -e "${YELLOW}⚠${NC}  Webhook endpoint вернул HTTP $TEST_RESPONSE"
    echo "  Это нормально, если сервис еще запускается"
fi

# Summary
echo -e "\n=================================================="
echo -e "${GREEN}✅ Webhook настроен успешно!${NC}"
echo -e "=================================================="
echo ""
echo "📱 Теперь отправьте /start вашему боту в Telegram"
echo "   Бот должен ответить сразу через webhook"
echo ""
echo "🔍 Полезные команды:"
echo "   # Проверить webhook:"
echo "   curl \"https://api.telegram.org/bot\${BOT_TOKEN}/getWebhookInfo\""
echo ""
echo "   # Удалить webhook (для тестирования с polling):"
echo "   curl \"https://api.telegram.org/bot\${BOT_TOKEN}/deleteWebhook\""
echo ""
echo "   # Посмотреть логи Cloud Run:"
echo "   gcloud run services logs read telegram-bot --region=us-central1 --limit=50"
echo ""
