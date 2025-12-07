#!/bin/bash

# 🌍 INKA Multilingual Setup Script
# Быстрое развертывание многоязычной поддержки

set -e  # Exit on error

# Change to project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set Python path to find src module
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

echo "🚀 INKA Multilingual Setup"
echo "=========================="
echo "📁 Working directory: $PWD"
echo "📍 PYTHONPATH: $PYTHONPATH"
echo ""

# ============================================
# STEP 1: Check Prerequisites
# ============================================
echo "📋 Проверка требований..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден"
    exit 1
fi
echo "✅ Python 3 найден: $(python3 --version)"

# Check API Key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY не установлен"
    echo "   Установите: export OPENAI_API_KEY=sk-..."
    echo "   Многие тесты не будут работать без этого"
fi

echo ""

# ============================================
# STEP 2: Initialize Database
# ============================================
echo "💾 Инициализация базы данных..."

python3 setup/init_database.py

if [ $? -eq 0 ]; then
    echo "✅ БД инициализирована успешно"
else
    echo "❌ Ошибка при инициализации БД"
    exit 1
fi

echo ""

# ============================================
# STEP 3: Populate with Multilingual Data
# ============================================
echo "📝 Заполнение многоязычными тестовыми данными..."

python3 setup/populate_multilingual.py

if [ $? -eq 0 ]; then
    echo "✅ БД заполнена тестовыми данными"
else
    echo "❌ Ошибка при заполнении БД"
    exit 1
fi

echo ""

# ============================================
# STEP 4: Run Tests (Optional)
# ============================================
if [ -n "$OPENAI_API_KEY" ]; then
    echo "🧪 Запуск тестов локализации..."
    
    python3 tests/test_multilingual.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Все тесты пройдены"
    else
        echo "⚠️  Некоторые тесты не прошли"
    fi
else
    echo "⏭️  Пропуск тестов (нет OPENAI_API_KEY)"
fi

echo ""

# ============================================
# STEP 5: Display Summary
# ============================================
echo "📊 ИТОГИ УСТАНОВКИ"
echo "=================="
echo ""
echo "✅ Многоязычная поддержка INKA установлена!"
echo ""
echo "📚 Документация:"
echo "   • MULTILINGUAL_QUICKSTART.md - 5-минутный старт"
echo "   • MULTILINGUAL_README.md - полный README"
echo "   • docs/MULTILINGUAL_ARCHITECTURE.md - архитектура"
echo "   • docs/MULTILINGUAL_INTEGRATION_EXAMPLES.md - примеры кода"
echo ""
echo "🚀 Следующие шаги:"
echo "   1. Прочитать MULTILINGUAL_QUICKSTART.md"
echo "   2. Интегрировать в Advanced INKA"
echo "   3. Интегрировать в Telegram Handlers"
echo "   4. Deploy на production"
echo ""
echo "🌍 Поддерживаемые языки:"
echo "   🇷🇺 Русский (ru)"
echo "   🇬🇧 Английский (en)"
echo "   🇮🇱 Иврит (he)"
echo ""
echo "✨ Спасибо за использование INKA Multilingual!"
echo ""
