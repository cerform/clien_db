#!/bin/bash
# Quick start guide for web interface

echo "🌐 Запуск веб-интерфейса для управления БД"
echo "==========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Активирование виртуального окружения..."
source venv/bin/activate

# Install dependencies
echo "📚 Установка зависимостей..."
pip install -r requirements.txt

# Check environment variables
echo ""
echo "🔐 Проверка переменных окружения..."
echo ""

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не установлен"
    echo "   Установите: export TELEGRAM_BOT_TOKEN=your_token"
    exit 1
fi

if [ -z "$GOOGLE_SPREADSHEET_ID" ]; then
    echo "❌ GOOGLE_SPREADSHEET_ID не установлен"
    echo "   Установите: export GOOGLE_SPREADSHEET_ID=your_id"
    exit 1
fi

# Set defaults
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8080}
export ADMIN_WEB_PASSWORD=${ADMIN_WEB_PASSWORD:-admin123}
export WEBHOOK_URL=${WEBHOOK_URL:-""}

# Print startup info
echo ""
echo "✅ Все переменные установлены"
echo ""
echo "🌐 Запуск сервера..."
echo "   Admin Panel: http://localhost:$PORT"
echo "   Login with: $ADMIN_WEB_PASSWORD"
echo "   API Docs: http://localhost:$PORT/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the application
python3 -m uvicorn src.web.app:create_app --host $HOST --port $PORT --reload --factory
