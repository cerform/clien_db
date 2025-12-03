#!/usr/bin/env python3
"""
Утилита для форматирования Google Sheets таблицы
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_sheets():
    """Отформатировать Google Sheets таблицу"""
    
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_JSON', 'credentials.json')
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    
    if not spreadsheet_id:
        print("\n❌ ОШИБКА: GOOGLE_SPREADSHEET_ID не установлен в .env")
        return False
    
    if not os.path.exists(credentials_file):
        print(f"\n❌ ОШИБКА: Файл {credentials_file} не найден")
        print("📝 Инструкция:")
        print("  1. Перейдите в Google Cloud Console")
        print("  2. Создайте Service Account")
        print("  3. Скачайте JSON файл с ключом")
        print("  4. Сохраните как credentials.json")
        return False
    
    try:
        from src.db.sheets_formatter import get_sheets_formatter
        
        print("\n" + "="*60)
        print("🚀 ФОРМАТИРОВАНИЕ GOOGLE SHEETS")
        print("="*60)
        
        # Создаём форматировщик
        formatter = get_sheets_formatter(credentials_file, spreadsheet_id)
        
        print("\n📋 Проверка листов...")
        
        # Создаём все листы (игнорируем ошибки если листы уже существуют)
        try:
            if formatter.create_masters_sheet():
                print("✅ Лист 'Мастера' создан")
            else:
                print("ℹ️  Лист 'Мастера' уже существует")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Лист 'Мастера' уже существует")
            else:
                print(f"❌ Ошибка: {str(e)}")
        
        try:
            if formatter.create_bookings_sheet():
                print("✅ Лист 'Записи' создан")
            else:
                print("ℹ️  Лист 'Записи' уже существует")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Лист 'Записи' уже существует")
            else:
                print(f"❌ Ошибка: {str(e)}")
        
        try:
            if formatter.create_clients_sheet():
                print("✅ Лист 'Клиенты' создан")
            else:
                print("ℹ️  Лист 'Клиенты' уже существует")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Лист 'Клиенты' уже существует")
            else:
                print(f"❌ Ошибка: {str(e)}")
        
        try:
            if formatter.create_procedures_sheet():
                print("✅ Лист 'Услуги' создан")
            else:
                print("ℹ️  Лист 'Услуги' уже существует")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Лист 'Услуги' уже существует")
            else:
                print(f"❌ Ошибка: {str(e)}")
        
        try:
            if formatter.create_reviews_sheet():
                print("✅ Лист 'Отзывы' создан")
            else:
                print("ℹ️  Лист 'Отзывы' уже существует")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Лист 'Отзывы' уже существует")
            else:
                print(f"❌ Ошибка: {str(e)}")
        
        try:
            if formatter.create_schedule_sheet():
                print("✅ Лист 'Расписание' создан")
            else:
                print("ℹ️  Лист 'Расписание' уже существует")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Лист 'Расписание' уже существует")
            else:
                print(f"❌ Ошибка: {str(e)}")
        
        try:
            if formatter.create_prices_sheet():
                print("✅ Лист 'Прайс-лист' создан")
            else:
                print("ℹ️  Лист 'Прайс-лист' уже существует")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Лист 'Прайс-лист' уже существует")
            else:
                print(f"❌ Ошибка: {str(e)}")
        
        try:
            if formatter.create_statistics_sheet():
                print("✅ Лист 'Статистика' создан")
            else:
                print("ℹ️  Лист 'Статистика' уже существует")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Лист 'Статистика' уже существует")
            else:
                print(f"❌ Ошибка: {str(e)}")
        
        try:
            if formatter.create_settings_sheet():
                print("✅ Лист 'Настройки' создан")
            else:
                print("ℹ️  Лист 'Настройки' уже существует")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Лист 'Настройки' уже существует")
            else:
                print(f"❌ Ошибка: {str(e)}")
        
        print("\n" + "="*60)
        print("✅ ТАБЛИЦА ГОТОВА К РАБОТЕ!")
        print("="*60)
        
        print("\n📊 Структура таблицы (9 листов):")
        print("  1️⃣  Лист 'Мастера' - информация о мастерах")
        print("  2️⃣  Лист 'Клиенты' - информация о клиентах")
        print("  3️⃣  Лист 'Записи' - записи клиентов на процедуры")
        print("  4️⃣  Лист 'Услуги' - доступные услуги и описание")
        print("  5️⃣  Лист 'Отзывы' - отзывы клиентов о мастерах")
        print("  6️⃣  Лист 'Расписание' - расписание работы мастеров")
        print("  7️⃣  Лист 'Прайс-лист' - прайс-лист услуг по мастерам")
        print("  8️⃣  Лист 'Статистика' - статистика по мастерам и клиентам")
        print("  9️⃣  Лист 'Настройки' - общие настройки салона")
        
        print("\n🔗 Откройте таблицу:")
        print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        print("\n")
        
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"\n❌ ОШИБКА: Не удалось импортировать модули")
        print(f"   {str(e)}")
        return False
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ ОШИБКА: {str(e)}")
        return False

def add_sample_data():
    """Добавить пример данных в таблицу"""
    
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_JSON', 'credentials.json')
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    
    if not spreadsheet_id:
        print("\n❌ ОШИБКА: GOOGLE_SPREADSHEET_ID не установлен в .env")
        return False
    
    try:
        from src.db.sheets_formatter import get_sheets_formatter
        
        formatter = get_sheets_formatter(credentials_file, spreadsheet_id)
        
        print("\n" + "="*60)
        print("📝 ДОБАВЛЕНИЕ ПРИМЕРОВ ДАННЫХ")
        print("="*60)
        
        # Примеры мастеров
        masters = [
            {
                "id": "1",
                "name": "Иван Петров",
                "specialty": "Татуировка",
                "experience": "7",
                "rating": "4.9",
                "phone": "+79001234567",
                "instagram": "@ivan_petrov_tattoo",
                "price": "2000",
                "availability": "Пн-Пт 10:00-18:00",
                "description": "Специалист по реалистичным татуировкам"
            },
            {
                "id": "2",
                "name": "Александра Сидорова",
                "specialty": "Пирсинг",
                "experience": "5",
                "rating": "4.8",
                "phone": "+79009876543",
                "instagram": "@alex_piercing",
                "price": "1500",
                "availability": "Пн-Сб 12:00-20:00",
                "description": "Специалист по пирсингу всех типов"
            }
        ]
        
        # Примеры услуг
        procedures = [
            {
                "id": "1",
                "name": "Татуировка малая",
                "description": "Татуировка размером до 5x5 см",
                "price": "2000",
                "duration": "30",
                "category": "Татуировка",
                "popularity": "5",
                "active": "ДА"
            },
            {
                "id": "2",
                "name": "Татуировка средняя",
                "description": "Татуировка размером от 5x5 до 15x15 см",
                "price": "5000",
                "duration": "120",
                "category": "Татуировка",
                "popularity": "5",
                "active": "ДА"
            },
            {
                "id": "3",
                "name": "Пирсинг ушей",
                "description": "Профессиональный пирсинг с использованием стерильного оборудования",
                "price": "1500",
                "duration": "15",
                "category": "Пирсинг",
                "popularity": "4",
                "active": "ДА"
            }
        ]
        
        print("\n➕ Добавление мастеров...")
        for master in masters:
            if formatter.add_master(master):
                print(f"  ✅ Добавлен: {master['name']}")
            else:
                print(f"  ❌ Ошибка добавления: {master['name']}")
        
        print("\n➕ Добавление услуг...")
        for proc in procedures:
            row = [
                proc["id"],
                proc["name"],
                proc["description"],
                proc["price"],
                proc["duration"],
                proc["category"],
                proc["popularity"],
                proc["active"]
            ]
            
            # Добавляем вручную через Google Sheets API
            try:
                formatter.service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range="Услуги!A:H",
                    valueInputOption="RAW",
                    body={"values": [row]}
                ).execute()
                print(f"  ✅ Добавлена: {proc['name']}")
            except Exception as e:
                print(f"  ❌ Ошибка: {str(e)}")
        
        print("\n" + "="*60)
        print("✅ ПРИМЕРЫ ДАННЫХ ДОБАВЛЕНЫ!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ ОШИБКА: {str(e)}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Утилита для работы с Google Sheets')
    parser.add_argument(
        'action',
        choices=['format', 'add-data', 'all'],
        help='Действие: format (создать структуру), add-data (добавить примеры), all (всё)'
    )
    
    args = parser.parse_args()
    
    success = True
    
    if args.action in ['format', 'all']:
        success = format_sheets() and success
    
    if args.action in ['add-data', 'all']:
        success = add_sample_data() and success
    
    sys.exit(0 if success else 1)
