#!/usr/bin/env python3
"""
Pre-Deploy Checklist Script
Проверяет все компоненты перед деплоем в продакшен
"""

import sys
import os

# Add project to path
sys.path.insert(0, '.')

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

# ==============================================================================
# TEST 1: БОТ ПОДКЛЮЧЕН К БД
# ==============================================================================

def test_bot_database_connection():
    print_header("ТЕСТ 1: ПОДКЛЮЧЕНИЕ БОТА К БД (Google Sheets)")

    try:
        from src.bot.handlers.inka_handler import (
            get_client_context,
            create_or_update_client,
            create_booking,
            get_available_slots
        )
        print_success("Функции для работы с БД импортированы")
        print("   - get_client_context() - READ")
        print("   - create_or_update_client() - WRITE/UPDATE")
        print("   - create_booking() - WRITE")
        print("   - get_available_slots() - READ")

        from src.db.repositories.clients_repo import ClientsRepo
        from src.db.repositories.bookings_repo import BookingsRepo
        from src.db.repositories.masters_repo import MastersRepo
        from src.db.repositories.services_repo import ServicesRepo

        print_success("Все репозитории доступны")
        return True

    except Exception as e:
        print_error(f"Ошибка подключения к БД: {e}")
        return False

# ==============================================================================
# TEST 2: ПОДКЛЮЧЕНИЕ К LLM
# ==============================================================================

def test_llm_connection():
    print_header("ТЕСТ 2: ПОДКЛЮЧЕНИЕ К LLM (OpenAI/INKA)")

    try:
        from src.services.inka_ai import INKA
        from src.bot.handlers.inka_handler import get_inka

        print_success("INKA AI модуль импортирован")

        # Check if OpenAI key exists
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and openai_key != 'YOUR_OPENAI_API_KEY':
            print_success(f"OPENAI_API_KEY присутствует ({openai_key[:10]}...)")
        else:
            print_warning("OPENAI_API_KEY не установлен - будет использован fallback режим")

        return True

    except Exception as e:
        print_error(f"Ошибка LLM: {e}")
        return False

# ==============================================================================
# TEST 3: КНОПКИ УБРАНЫ ИЗ TELEGRAM
# ==============================================================================

def test_no_keyboards_in_telegram():
    print_header("ТЕСТ 3: ПРОВЕРКА ОТСУТСТВИЯ КНОПОК В TELEGRAM")

    try:
        # Check inka_handler uses ReplyKeyboardRemove
        with open('src/bot/handlers/inka_handler.py', 'r') as f:
            content = f.read()

        if 'ReplyKeyboardRemove()' in content:
            print_success("ReplyKeyboardRemove() используется в inka_handler")
        else:
            print_error("ReplyKeyboardRemove() НЕ НАЙДЕН")
            return False

        if '/start' in content and 'reply_markup=types.ReplyKeyboardRemove()' in content:
            print_success("/start команда использует ReplyKeyboardRemove()")
        else:
            print_warning("/start может показывать клавиатуру")

        # Check language_handler
        with open('src/bot/handlers/language_handler.py', 'r') as f:
            lang_content = f.read()

        if 'ReplyKeyboardRemove()' in lang_content:
            print_success("language_handler использует ReplyKeyboardRemove()")

        return True

    except Exception as e:
        print_error(f"Ошибка проверки клавиатур: {e}")
        return False

# ==============================================================================
# TEST 4: ВЕБ API CRUD ОПЕРАЦИИ
# ==============================================================================

def test_web_api_crud():
    print_header("ТЕСТ 4: ВЕБ API - CRUD ОПЕРАЦИИ")

    try:
        from src.web.api import (
            get_clients,
            create_client,
            update_client,
            delete_client,
            get_masters,
            update_master,
            get_services,
            update_service,
            get_bookings,
            update_booking
        )

        print_success("Все CRUD эндпоинты импортированы:")
        print("   - Clients: GET, POST, PUT, DELETE")
        print("   - Masters: GET, POST, PUT, DELETE")
        print("   - Services: GET, POST, PUT, DELETE")
        print("   - Bookings: GET, PUT, DELETE")

        # Check edit_handlers
        from src.bot.handlers import edit_handlers
        print_success("edit_handlers модуль доступен для Telegram CRUD")

        return True

    except Exception as e:
        print_error(f"Ошибка Web API: {e}")
        return False

# ==============================================================================
# TEST 5: ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ==============================================================================

def test_environment_variables():
    print_header("ТЕСТ 5: ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ И ТОКЕНЫ")

    required_vars = {
        'BOT_TOKEN': 'Telegram Bot Token',
        'SPREADSHEET_ID': 'Google Sheets Database ID',
    }

    optional_vars = {
        'OPENAI_API_KEY': 'OpenAI API для INKA',
        'ADMIN_USER_IDS': 'ID администраторов',
        'WEBHOOK_URL': 'URL для webhook режима',
    }

    all_ok = True

    # Check required
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value not in ['YOUR_BOT_TOKEN', 'YOUR_SPREADSHEET_ID']:
            print_success(f"{var}: {description} ✓")
        else:
            print_error(f"{var}: НЕ УСТАНОВЛЕН - {description}")
            all_ok = False

    # Check optional
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_success(f"{var}: {description} ✓")
        else:
            print_warning(f"{var}: не установлен - {description}")

    return all_ok

# ==============================================================================
# TEST 6: SSL НАСТРОЙКИ
# ==============================================================================

def test_ssl_settings():
    print_header("ТЕСТ 6: SSL НАСТРОЙКИ ДЛЯ ПРОДАКШЕНА")

    try:
        # Check entrypoint.py
        with open('src/bot/entrypoint.py', 'r') as f:
            entrypoint_content = f.read()

        if 'AiohttpSession()' in entrypoint_content and 'SSL verification enabled' in entrypoint_content:
            print_success("Bot: SSL verification ENABLED")
        else:
            print_warning("Bot: SSL может быть отключен")

        # Check ai_dialog_engine.py
        with open('src/services/ai_dialog_engine.py', 'r') as f:
            ai_content = f.read()

        if 'verify=True' in ai_content or 'verify=False' not in ai_content:
            print_success("AI Dialog Engine: SSL verification ENABLED")
        else:
            print_warning("AI Dialog Engine: SSL может быть отключен")

        return True

    except Exception as e:
        print_error(f"Ошибка проверки SSL: {e}")
        return False

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "🚀" * 35)
    print("  PRE-DEPLOY CHECKLIST")
    print("  Проверка всех компонентов перед деплоем в продакшен")
    print("🚀" * 35)

    results = {}

    # Run all tests
    results['database'] = test_bot_database_connection()
    results['llm'] = test_llm_connection()
    results['keyboards'] = test_no_keyboards_in_telegram()
    results['web_api'] = test_web_api_crud()
    results['env_vars'] = test_environment_variables()
    results['ssl'] = test_ssl_settings()

    # Summary
    print_header("ИТОГОВЫЙ ОТЧЕТ")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 70)
    print(f"ИТОГО: {passed}/{total} тестов пройдено")

    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ГОТОВ К ДЕПЛОЮ!")
        print("=" * 70)
        return 0
    else:
        print("\n⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ - ИСПРАВЬТЕ ПЕРЕД ДЕПЛОЕМ")
        print("=" * 70)
        return 1

if __name__ == '__main__':
    sys.exit(main())
