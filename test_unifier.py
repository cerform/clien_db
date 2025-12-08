#!/usr/bin/env python3
"""
Тестовый скрипт для запуска унификатора базы данных
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    # Попробуем импортировать зависимости
    from src.config.config import Config
    from src.utils.database_unifier import DatabaseUnifier
    print("✅ Импорт модулей успешен")
    
    # Попробуем загрузить конфигурацию
    config = Config.from_env()
    print("✅ Конфигурация загружена")
    print(f"   - Google Spreadsheet ID: {config.google_spreadsheet_id[:20]}...")
    
    # Попробуем инициализировать Google Sheets клиент
    try:
        from src.db.sheets_client import GoogleSheetsClient
        credentials_file = PROJECT_ROOT / "credentials.json"
        sheets_client = GoogleSheetsClient(
            credentials_file=str(credentials_file),
            spreadsheet_id=config.google_spreadsheet_id
        )
        print("✅ Google Sheets клиент создан")
        
        # Создаем унификатор
        unifier = DatabaseUnifier(sheets_client)
        print("✅ DatabaseUnifier инициализирован")
        
        # Запускаем тестовую унификацию
        print("\n🔄 Начинаем унификацию базы данных...")
        results = unifier.unify_database(dry_run=True)
        
        print("\n📊 Результаты:")
        print(f"   - Статус: {'✅ Успешно' if 'error' not in results else '❌ Ошибка'}")
        if 'error' in results:
            print(f"   - Ошибка: {results['error']}")
        else:
            print(f"   - Мастеров: {results.get('masters', {}).get('count', 0)}")
            print(f"   - Клиентов: {results.get('clients', {}).get('count', 0)}")
            print(f"   - Услуг: {results.get('services', {}).get('count', 0)}")
            print(f"   - Ошибок валидации: {len(results.get('validation_errors', []))}")
        
    except Exception as e:
        print(f"❌ Ошибка при работе с Google Sheets: {e}")
        print("💡 Проверьте credentials.json и права доступа")
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Проверьте структуру проекта и зависимости")
    
except Exception as e:
    print(f"❌ Общая ошибка: {e}")
    print("💡 Проверьте конфигурацию в .env файле")