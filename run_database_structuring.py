#!/usr/bin/env python3
"""
🗄️ СКРИПТ СТРУКТУРИРОВАНИЯ БАЗЫ ДАННЫХ
=====================================
Запуск унификации и структурирования базы данных
"""
import sys
import os
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    parser = argparse.ArgumentParser(description='Структурирование базы данных')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Только проверка, без изменений')
    parser.add_argument('--verbose', action='store_true',
                       help='Подробный вывод')
    
    args = parser.parse_args()
    
    try:
        print("🗄️ СТРУКТУРИРОВАНИЕ БАЗЫ ДАННЫХ")
        print("=" * 50)
        
        # Импорт модулей
        from src.config.config import Config
        from src.utils.database_unifier import DatabaseUnifier
        from src.db.db_initializer import DatabaseInitializer
        from src.db.sheets_client import GoogleSheetsClient
        
        # Загрузка конфигурации
        print("📋 Загрузка конфигурации...")
        config = Config.from_env()
        print(f"   ✅ Google Spreadsheet ID: {config.google_spreadsheet_id[:20]}...")
        
        # Инициализация клиента
        print("🔗 Подключение к Google Sheets...")
        credentials_file = PROJECT_ROOT / "credentials.json"
        sheets_client = GoogleSheetsClient(
            credentials_file=str(credentials_file),
            spreadsheet_id=config.google_spreadsheet_id
        )
        print("   ✅ Подключение успешно")
        
        # Создание унификатора
        print("🔄 Инициализация унификатора...")
        unifier = DatabaseUnifier(sheets_client)
        print("   ✅ Унификатор готов")

        # Ensure the spreadsheet has the expected structure before unifying
        print("🔧 Проверка и создание структуры листов (если необходимо)...")
        db_initializer = DatabaseInitializer(
            credentials_file=str(credentials_file),
            spreadsheet_id=config.google_spreadsheet_id
        )
        if args.dry_run:
            print("   ℹ️ Dry run: структура таблиц не будет изменена (показаны бы действия)")
        else:
            created = db_initializer.initialize_database()
            if not created:
                print("   ⚠️ Не удалось создать/обновить структуру таблиц")
            else:
                print("   ✅ Структура листов проверена/создана")
        
        # Запуск унификации
        print("\n" + "=" * 50)
        print("🚀 НАЧАЛО СТРУКТУРИРОВАНИЯ")
        print("=" * 50)
        
        results = unifier.unify_database(dry_run=args.dry_run)
        
        # Вывод результатов
        print("\n" + "=" * 50)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
        print("=" * 50)
        
        if 'error' in results:
            print(f"❌ Ошибка: {results['error']}")
            return 1
        
        masters_count = results.get('masters', {}).get('total_masters', 0)
        clients_count = results.get('clients', {}).get('count', 0) 
        services_count = results.get('services', {}).get('count', 0)
        errors_count = len(results.get('validation_errors', []))
        
        print(f"👥 Мастеров структурировано: {masters_count}")
        print(f"🧑‍💼 Клиентов структурировано: {clients_count}")
        print(f"💼 Услуг структурировано: {services_count}")
        print(f"⚠️ Ошибок валидации: {errors_count}")
        
        if args.dry_run:
            print("\nℹ️ Режим проверки - изменения не сохранены")
            print("💡 Для сохранения запустите без --dry-run")
        else:
            print("\n✅ Структурирование завершено успешно!")
            print("📊 Данные сохранены в Google Sheets")
        
        # Детальная информация об ошибках
        if errors_count > 0 and args.verbose:
            print(f"\n⚠️ ДЕТАЛИ ОШИБОК ВАЛИДАЦИИ:")
            for i, error in enumerate(results.get('validation_errors', [])[:10]):
                print(f"   {i+1}. {error.get('table', 'Unknown')}: {error.get('errors', [])}")
            
            if errors_count > 10:
                print(f"   ... и еще {errors_count - 10} ошибок")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Операция прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())