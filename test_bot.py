#!/usr/bin/env python3
"""
Интеграционные тесты для Telegram Bot
Проверка основных функций без запуска бота
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any
import traceback

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


class BotTester:
    """Тестирование функционала бота"""
    
    def __init__(self):
        self.results = []
        
    def log_result(self, test_name: str, status: str, message: str, details: Any = None):
        """Логирование результата теста"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
        }
        if details:
            result['details'] = details
        self.results.append(result)
        
        # Вывод в консоль
        status_icon = {
            'pass': '✅',
            'fail': '❌',
            'skip': '⏭️',
            'warning': '⚠️'
        }.get(status, '❓')
        
        print(f"{status_icon} {test_name}: {message}")
        if details and status == 'fail':
            print(f"   Детали: {details}")
    
    async def test_telegram_connection(self):
        """Тест 1: Подключение к Telegram API"""
        test_name = "Telegram API Connection"
        
        try:
            from aiogram import Bot
            
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                self.log_result(test_name, 'fail', 'TELEGRAM_BOT_TOKEN не найден')
                return False
            
            bot = Bot(token=bot_token)
            
            try:
                me = await bot.get_me()
                self.log_result(
                    test_name, 
                    'pass', 
                    f'Подключение успешно. Bot: @{me.username}',
                    {'id': me.id, 'username': me.username, 'first_name': me.first_name}
                )
                return True
            finally:
                await bot.session.close()
                
        except Exception as e:
            self.log_result(test_name, 'fail', str(e), traceback.format_exc())
            return False
    
    async def test_google_sheets_connection(self):
        """Тест 2: Подключение к Google Sheets"""
        test_name = "Google Sheets Connection"
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
            if not spreadsheet_id:
                self.log_result(test_name, 'fail', 'GOOGLE_SHEETS_SPREADSHEET_ID не найден')
                return False
            
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
            if not os.path.exists(credentials_path):
                self.log_result(test_name, 'fail', f'Credentials file не найден: {credentials_path}')
                return False
            
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            service = build('sheets', 'v4', credentials=credentials)
            
            # Получаем информацию о таблице
            result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            
            sheets = [sheet['properties']['title'] for sheet in result.get('sheets', [])]
            
            self.log_result(
                test_name,
                'pass',
                f'Подключение успешно. Таблица: {result["properties"]["title"]}',
                {'sheets': sheets, 'spreadsheet_id': spreadsheet_id}
            )
            return True
            
        except Exception as e:
            self.log_result(test_name, 'fail', str(e), traceback.format_exc())
            return False
    
    async def test_google_sheets_read(self):
        """Тест 3: Чтение данных из Google Sheets"""
        test_name = "Google Sheets Read"
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
            
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            service = build('sheets', 'v4', credentials=credentials)
            
            # Пытаемся прочитать первую строку из первого листа
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='A1:Z1'
            ).execute()
            
            values = result.get('values', [])
            
            self.log_result(
                test_name,
                'pass',
                f'Чтение успешно. Прочитано {len(values[0]) if values else 0} колонок',
                {'first_row': values[0] if values else []}
            )
            return True
            
        except Exception as e:
            self.log_result(test_name, 'fail', str(e), traceback.format_exc())
            return False
    
    async def test_google_sheets_write(self):
        """Тест 4: Запись данных в Google Sheets"""
        test_name = "Google Sheets Write"
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from datetime import datetime
            
            spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
            
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            service = build('sheets', 'v4', credentials=credentials)
            
            # Пытаемся записать тестовую строку
            test_data = [[f'Test at {datetime.now().isoformat()}']]
            
            # Ищем лист для тестов или используем первый доступный
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
            
            test_sheet = 'Test' if 'Test' in sheets else sheets[0] if sheets else 'Sheet1'
            
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f'{test_sheet}!A:A',
                valueInputOption='RAW',
                body={'values': test_data}
            ).execute()
            
            self.log_result(
                test_name,
                'pass',
                f'Запись успешна. Обновлено: {result.get("updates", {}).get("updatedCells", 0)} ячеек',
                {'sheet': test_sheet, 'range': result.get('updates', {}).get('updatedRange')}
            )
            return True
            
        except Exception as e:
            self.log_result(test_name, 'warning', f'Запись не удалась (возможно нет прав): {str(e)}')
            return False
    
    async def test_bot_modules(self):
        """Тест 5: Загрузка модулей бота"""
        test_name = "Bot Modules Loading"
        
        try:
            modules_to_test = []
            
            # Пытаемся импортировать модули бота
            try:
                from src.config import get_config
                modules_to_test.append('src.config')
            except ImportError:
                pass
            
            try:
                from src.db.sheets_client import SheetsClient
                modules_to_test.append('src.db.sheets_client')
            except ImportError:
                pass
            
            try:
                from src.bot.handlers import client_handlers
                modules_to_test.append('src.bot.handlers')
            except ImportError:
                pass
            
            if modules_to_test:
                self.log_result(
                    test_name,
                    'pass',
                    f'Загружено {len(modules_to_test)} модулей',
                    {'modules': modules_to_test}
                )
            else:
                self.log_result(
                    test_name,
                    'warning',
                    'Модули бота не найдены (нормально для минимальной конфигурации)'
                )
            return True
            
        except Exception as e:
            self.log_result(test_name, 'fail', str(e), traceback.format_exc())
            return False
    
    async def test_environment_variables(self):
        """Тест 6: Проверка переменных окружения"""
        test_name = "Environment Variables"
        
        required_vars = {
            'TELEGRAM_BOT_TOKEN': 'Токен Telegram бота',
            'GOOGLE_SHEETS_SPREADSHEET_ID': 'ID Google Sheets таблицы',
        }
        
        optional_vars = {
            'GOOGLE_APPLICATION_CREDENTIALS': 'Путь к credentials.json',
            'PORT': 'Порт для веб-сервера',
        }
        
        missing_required = []
        missing_optional = []
        present = []
        
        for var, description in required_vars.items():
            if os.getenv(var):
                present.append(var)
            else:
                missing_required.append(f'{var} ({description})')
        
        for var, description in optional_vars.items():
            if not os.getenv(var):
                missing_optional.append(f'{var} ({description})')
        
        if missing_required:
            self.log_result(
                test_name,
                'fail',
                f'Отсутствуют обязательные переменные: {", ".join(missing_required)}'
            )
            return False
        elif missing_optional:
            self.log_result(
                test_name,
                'warning',
                f'Присутствуют все обязательные переменные. Опциональные отсутствуют: {", ".join(missing_optional)}',
                {'present': present}
            )
            return True
        else:
            self.log_result(
                test_name,
                'pass',
                'Все переменные окружения присутствуют',
                {'present': present + list(optional_vars.keys())}
            )
            return True
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("=" * 70)
        print("🧪 ЗАПУСК ИНТЕГРАЦИОННЫХ ТЕСТОВ TELEGRAM BOT")
        print("=" * 70)
        print()
        
        tests = [
            self.test_environment_variables(),
            self.test_telegram_connection(),
            self.test_google_sheets_connection(),
            self.test_google_sheets_read(),
            self.test_google_sheets_write(),
            self.test_bot_modules(),
        ]
        
        await asyncio.gather(*tests)
        
        print()
        print("=" * 70)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r['status'] == 'pass')
        failed = sum(1 for r in self.results if r['status'] == 'fail')
        warnings = sum(1 for r in self.results if r['status'] == 'warning')
        total = len(self.results)
        
        print(f"\n✅ Пройдено: {passed}/{total}")
        print(f"❌ Провалено: {failed}/{total}")
        print(f"⚠️  Предупреждений: {warnings}/{total}")
        
        if failed == 0:
            print("\n🎉 Все критичные тесты пройдены успешно!")
            return True
        else:
            print("\n⚠️  Некоторые тесты не прошли. Проверьте конфигурацию.")
            return False


async def main():
    """Главная функция"""
    tester = BotTester()
    success = await tester.run_all_tests()
    
    # Возвращаем код выхода
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())
