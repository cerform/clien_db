#!/bin/bash

# Упрощенный деплой для ситуаций с SSL проблемами
# Использует gcloud с отключенной проверкой SSL

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Конфигурация
DEFAULT_REGION="us-central1"
SERVICE_NAME="telegram-bot"
IMAGE_NAME="telegram-bot"

print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Проверка аргументов
if [ -z "$1" ]; then
    print_error "PROJECT_ID не указан"
    echo "Использование: ./deploy_simple.sh PROJECT_ID [REGION]"
    exit 1
fi

PROJECT_ID=$1
REGION=${2:-$DEFAULT_REGION}

print_step "Конфигурация деплоя:"
echo "  PROJECT_ID: $PROJECT_ID"
echo "  REGION: $REGION"
echo "  SERVICE_NAME: $SERVICE_NAME"
echo ""

# Отключаем SSL проверку
export CLOUDSDK_PYTHON_SITEPACKAGES=1
export REQUESTS_CA_BUNDLE=""
export PYTHONWARNINGS="ignore:Unverified HTTPS request"

print_step "SSL проверка отключена (из-за корпоративного прокси)"

# Установка проекта
print_step "Установка проекта..."
gcloud config set project $PROJECT_ID 2>/dev/null || {
    print_error "Не удалось установить проект $PROJECT_ID"
    exit 1
}

# Включение необходимых API (с игнорированием SSL предупреждений)
print_step "Включение необходимых API..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    2>&1 | grep -v "InsecureRequestWarning" || true

# Создание секретов
print_step "Создание секретов..."

# TELEGRAM_BOT_TOKEN
if ! gcloud secrets describe telegram-bot-token &> /dev/null; then
    BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d '=' -f2)
    if [ -n "$BOT_TOKEN" ]; then
        echo -n "$BOT_TOKEN" | gcloud secrets create telegram-bot-token \
            --data-file=- \
            --replication-policy="automatic" 2>&1 | grep -v "InsecureRequestWarning"
        print_step "Секрет telegram-bot-token создан"
    else
        print_warning "TELEGRAM_BOT_TOKEN не найден в .env"
    fi
else
    print_step "Секрет telegram-bot-token существует"
fi

# GOOGLE_SHEETS_SPREADSHEET_ID
if ! gcloud secrets describe google-sheets-id &> /dev/null; then
    SHEETS_ID=$(grep GOOGLE_SHEETS_SPREADSHEET_ID .env | cut -d '=' -f2)
    if [ -n "$SHEETS_ID" ]; then
        echo -n "$SHEETS_ID" | gcloud secrets create google-sheets-id \
            --data-file=- \
            --replication-policy="automatic" 2>&1 | grep -v "InsecureRequestWarning"
        print_step "Секрет google-sheets-id создан"
    else
        print_warning "GOOGLE_SHEETS_SPREADSHEET_ID не найден в .env"
    fi
else
    print_step "Секрет google-sheets-id существует"
fi

# Создание Service Account для Google Sheets API
print_step "Создание Service Account для Google Sheets..."
SHEETS_SA_NAME="telegram-bot-sheets-sa"
SHEETS_SA_EMAIL="${SHEETS_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
CREDENTIALS_FILE="credentials.json"

if ! gcloud iam service-accounts describe $SHEETS_SA_EMAIL &> /dev/null; then
    print_step "Создание нового Service Account..."
    gcloud iam service-accounts create $SHEETS_SA_NAME \
        --display-name="Telegram Bot Google Sheets Service Account" \
        2>&1 | grep -v "InsecureRequestWarning"
    
    # Генерация ключа
    print_step "Генерация ключа для Service Account..."
    gcloud iam service-accounts keys create $CREDENTIALS_FILE \
        --iam-account=$SHEETS_SA_EMAIL \
        2>&1 | grep -v "InsecureRequestWarning"
    
    print_step "Ключ сохранен: $CREDENTIALS_FILE"
    
    print_warning "ВАЖНО: Добавьте $SHEETS_SA_EMAIL в права доступа к Google Sheets!"
    echo "  1. Откройте вашу Google Sheets таблицу"
    echo "  2. Нажмите 'Поделиться'"
    echo "  3. Добавьте email: $SHEETS_SA_EMAIL"
    echo "  4. Дайте права 'Редактор'"
fi

# Создание секрета для credentials
if [ -f "$CREDENTIALS_FILE" ]; then
    if ! gcloud secrets describe google-credentials &> /dev/null; then
        gcloud secrets create google-credentials \
            --data-file=$CREDENTIALS_FILE \
            --replication-policy="automatic" \
            2>&1 | grep -v "InsecureRequestWarning"
        print_step "Секрет google-credentials создан"
    fi
fi

# Service Account для Cloud Run
print_step "Настройка Service Account для Cloud Run..."
SA_NAME="telegram-bot-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SA_EMAIL &> /dev/null; then
    gcloud iam service-accounts create $SA_NAME \
        --display-name="Telegram Bot Cloud Run Service Account" \
        2>&1 | grep -v "InsecureRequestWarning"
    print_step "Service Account создан: $SA_EMAIL"
fi

# Назначение прав
print_step "Назначение прав для Service Account..."
for secret in telegram-bot-token google-sheets-id google-credentials; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet 2>&1 | grep -v "InsecureRequestWarning" || true
done

print_step "Права назначены"

# Сборка образа через Cloud Build
print_step "Сборка Docker образа через Cloud Build..."
print_warning "Это может занять несколько минут..."

gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME \
    2>&1 | grep -v "InsecureRequestWarning" | grep -v "Unverified HTTPS"

if [ $? -eq 0 ]; then
    print_step "Образ успешно собран!"
else
    print_error "Ошибка при сборке образа"
    print_warning "Попробуйте собрать образ локально с Docker"
    exit 1
fi

# Деплой в Cloud Run
print_step "Деплой в Cloud Run..."

gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --service-account $SA_EMAIL \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 3 \
    --port 8080 \
    --timeout 300s \
    --set-env-vars PYTHONUNBUFFERED=1,PYTHONDONTWRITEBYTECODE=1 \
    --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,GOOGLE_SHEETS_SPREADSHEET_ID=google-sheets-id:latest \
    --quiet \
    2>&1 | grep -v "InsecureRequestWarning"

# Получение URL сервиса
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)' 2>&1 | grep -v "InsecureRequestWarning")

print_step "Деплой завершен успешно!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓${NC} Сервис URL: $SERVICE_URL"
echo -e "${GREEN}✓${NC} Регион: $REGION"
echo -e "${GREEN}✓${NC} Service Account: $SA_EMAIL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Для просмотра логов:"
echo "  gcloud run services logs read $SERVICE_NAME --region $REGION"
echo ""
