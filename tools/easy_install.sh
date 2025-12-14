#!/bin/bash
# 🚀 One-Click Installer для Tattoo Bot
# Для администраторов салона без знания программирования

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🎨 Tattoo Bot - Автоматический установщик                ║"
echo "║  Версия 1.0 - Для администраторов салона                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Welcome
echo -e "${GREEN}Этот скрипт автоматически установит весь бот за 5 минут!${NC}"
echo ""
echo "Вам понадобятся:"
echo "  1. Google Cloud Project ID"
echo "  2. Telegram Bot Token (от @BotFather)"
echo "  3. OpenAI API Key (для AI ассистента)"
echo ""
read -p "Продолжить? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Step 2: Collect info
echo ""
echo -e "${YELLOW}Шаг 1/5: Сбор информации${NC}"
echo ""

read -p "Google Cloud Project ID: " GCP_PROJECT
read -p "Telegram Bot Token: " BOT_TOKEN
read -p "OpenAI API Key: " OPENAI_KEY
read -p "Название салона: " SALON_NAME

echo ""
echo -e "${GREEN}✓ Информация собрана${NC}"

# Step 3: Setup GCP
echo ""
echo -e "${YELLOW}Шаг 2/5: Настройка Google Cloud${NC}"
gcloud config set project $GCP_PROJECT

# Enable APIs
echo "Включаю необходимые API..."
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com

# Step 4: Create secrets
echo ""
echo -e "${YELLOW}Шаг 3/5: Сохранение ключей${NC}"
echo $BOT_TOKEN | gcloud secrets create telegram-bot-token --data-file=-
echo $OPENAI_KEY | gcloud secrets create openai-api-key --data-file=-

echo -e "${GREEN}✓ Ключи сохранены безопасно${NC}"

# Step 5: Deploy
echo ""
echo -e "${YELLOW}Шаг 4/5: Деплой на Cloud Run (это займёт 3-5 минут)${NC}"
gcloud run deploy telegram-bot \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,OPENAI_API_KEY=openai-api-key:latest

SERVICE_URL=$(gcloud run services describe telegram-bot --region=us-central1 --format="value(status.url)")

echo -e "${GREEN}✓ Бот развёрнут!${NC}"

# Step 6: Setup webhook
echo ""
echo -e "${YELLOW}Шаг 5/5: Настройка Telegram webhook${NC}"
./scripts/setup_persistent_webhook.sh

# Done
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ УСТАНОВКА ЗАВЕРШЕНА!                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Ваш бот готов к работе!${NC}"
echo ""
echo "🤖 Telegram бот: @inkamanager_bot"
echo "🌐 Веб-панель: $SERVICE_URL"
echo "📝 Настройка: $SERVICE_URL/setup"
echo ""
echo "Следующие шаги:"
echo "  1. Откройте $SERVICE_URL/setup для финальной настройки"
echo "  2. Добавьте мастеров и расписание"
echo "  3. Протестируйте бота в Telegram"
echo ""
echo "Документация: см. QUICKSTART_INSTALLER.md"
echo ""
