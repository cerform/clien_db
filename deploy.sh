#!/bin/bash

# Скрипт для деплоя Telegram бота в Google Cloud Run
# Использование: ./deploy.sh [PROJECT_ID] [REGION]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Конфигурация по умолчанию
DEFAULT_REGION="us-central1"
SERVICE_NAME="telegram-bot"
IMAGE_NAME="telegram-bot"

# Функция для вывода сообщений
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
    echo "Использование: ./deploy.sh PROJECT_ID [REGION]"
    exit 1
fi

PROJECT_ID=$1
REGION=${2:-$DEFAULT_REGION}

print_step "Конфигурация деплоя:"
echo "  PROJECT_ID: $PROJECT_ID"
echo "  REGION: $REGION"
echo "  SERVICE_NAME: $SERVICE_NAME"
echo ""

# Проверка установки gcloud
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI не установлен"
    echo "Установите gcloud: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Установка проекта
print_step "Установка проекта..."
gcloud config set project $PROJECT_ID

# Включение необходимых API
print_step "Включение необходимых API..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# Создание секретов (если не существуют)
print_step "Проверка секретов..."

# Проверка TELEGRAM_BOT_TOKEN
if ! gcloud secrets describe telegram-bot-token &> /dev/null; then
    print_warning "Секрет telegram-bot-token не найден"
    read -p "Введите TELEGRAM_BOT_TOKEN: " BOT_TOKEN
    echo -n "$BOT_TOKEN" | gcloud secrets create telegram-bot-token \
        --data-file=- \
        --replication-policy="automatic"
    print_step "Секрет telegram-bot-token создан"
else
    print_step "Секрет telegram-bot-token существует"
fi

# Проверка GOOGLE_SHEETS_SPREADSHEET_ID
if ! gcloud secrets describe google-sheets-id &> /dev/null; then
    print_warning "Секрет google-sheets-id не найден"
    read -p "Введите GOOGLE_SHEETS_SPREADSHEET_ID: " SHEETS_ID
    echo -n "$SHEETS_ID" | gcloud secrets create google-sheets-id \
        --data-file=- \
        --replication-policy="automatic"
    print_step "Секрет google-sheets-id создан"
else
    print_step "Секрет google-sheets-id существует"
fi

# Создание Service Account для Google Sheets API
print_step "Создание Service Account для Google Sheets API..."
SHEETS_SA_NAME="telegram-bot-sheets-sa"
SHEETS_SA_EMAIL="${SHEETS_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
CREDENTIALS_FILE="credentials.json"

if ! gcloud iam service-accounts describe $SHEETS_SA_EMAIL &> /dev/null; then
    print_step "Создание нового Service Account для Google Sheets..."
    gcloud iam service-accounts create $SHEETS_SA_NAME \
        --display-name="Telegram Bot Google Sheets Service Account" \
        --description="Service Account для доступа к Google Sheets API"
    
    print_step "Service Account создан: $SHEETS_SA_EMAIL"
    
    # Создание и скачивание ключа
    print_step "Генерация ключа для Service Account..."
    gcloud iam service-accounts keys create $CREDENTIALS_FILE \
        --iam-account=$SHEETS_SA_EMAIL
    
    print_step "Ключ сохранен в: $CREDENTIALS_FILE"
    
    # Назначение ролей для Google Sheets
    print_step "Назначение прав для работы с Google Sheets..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SHEETS_SA_EMAIL}" \
        --role="roles/editor" \
        --quiet
    
    print_warning "ВАЖНО: Добавьте $SHEETS_SA_EMAIL в права доступа к Google Sheets!"
    echo "  1. Откройте вашу Google Sheets таблицу"
    echo "  2. Нажмите 'Поделиться'"
    echo "  3. Добавьте email: $SHEETS_SA_EMAIL"
    echo "  4. Дайте права 'Редактор'"
    echo ""
    read -p "Нажмите Enter когда добавите Service Account в Google Sheets..."
else
    print_step "Service Account для Sheets существует: $SHEETS_SA_EMAIL"
    
    # Проверка наличия credentials.json
    if [ ! -f "$CREDENTIALS_FILE" ]; then
        print_warning "Файл $CREDENTIALS_FILE не найден. Создаю новый ключ..."
        gcloud iam service-accounts keys create $CREDENTIALS_FILE \
            --iam-account=$SHEETS_SA_EMAIL
        print_step "Новый ключ создан: $CREDENTIALS_FILE"
    else
        print_step "Файл $CREDENTIALS_FILE найден"
    fi
fi

# Проверка Google credentials секрета
if ! gcloud secrets describe google-credentials &> /dev/null; then
    print_step "Создание секрета google-credentials..."
    gcloud secrets create google-credentials \
        --data-file=$CREDENTIALS_FILE \
        --replication-policy="automatic"
    print_step "Секрет google-credentials создан"
else
    print_step "Секрет google-credentials существует"
    # Обновление секрета если credentials.json был пересоздан
    if [ -f "$CREDENTIALS_FILE" ]; then
        read -p "Обновить секрет google-credentials новым ключом? (y/n): " UPDATE_SECRET
        if [ "$UPDATE_SECRET" = "y" ]; then
            gcloud secrets versions add google-credentials \
                --data-file=$CREDENTIALS_FILE
            print_step "Секрет google-credentials обновлен"
        fi
    fi
fi

# Создание Service Account для Cloud Run
print_step "Настройка Service Account для Cloud Run..."
SA_NAME="telegram-bot-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SA_EMAIL &> /dev/null; then
    gcloud iam service-accounts create $SA_NAME \
        --display-name="Telegram Bot Cloud Run Service Account"
    print_step "Service Account создан: $SA_EMAIL"
else
    print_step "Service Account существует: $SA_EMAIL"
fi

# Назначение прав для доступа к секретам
print_step "Назначение прав для Service Account..."
gcloud secrets add-iam-policy-binding telegram-bot-token \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

gcloud secrets add-iam-policy-binding google-sheets-id \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

gcloud secrets add-iam-policy-binding google-credentials \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

print_step "Access rights assigned to Service Account."

# Docker Image Build
print_step "Building..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME

# Image Deploy to Cloud Run
print_step "Deploying.."
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
    --quiet

# Get Service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

print_step "New deployment completed successfully!"
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
echo "Для обновления сервиса:"
echo "  ./deploy.sh $PROJECT_ID $REGION"
echo ""
