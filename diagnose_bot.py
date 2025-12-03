#!/usr/bin/env python3
"""
Скрипт диагностики бота - проверяет все функции
Запуск: python3 diagnose_bot.py
"""
import sys
import os
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from unittest.mock import Mock, AsyncMock
from aiogram import types
from aiogram.fsm.context import FSMContext

# Импорты обработчиков
from src.bot.handlers.client_handlers import (
    cmd_start, cmd_book, cmd_my_bookings, cmd_help,
    process_name, process_phone, ClientStates
)
from src.config.env_loader import load_env
from src.config.config import Config


class BotDiagnostics:
    """Класс для диагностики функций бота"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def log_result(self, test_name: str, passed: bool, error: str = None):
        """Логировать результат теста"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "passed": passed,
            "error": error
        })
        
        if passed:
            self.passed += 1
            print(f"{status} - {test_name}")
        else:
            self.failed += 1
            print(f"{status} - {test_name}")
            if error:
                print(f"   Error: {error}")
    
    async def check_environment(self):
        """Проверка конфигурации окружения"""
        print("\n🔍 Checking Environment Configuration...")
        
        try:
            load_env()
            cfg = Config.from_env()
            
            # Проверка BOT_TOKEN
            if cfg.BOT_TOKEN:
                self.log_result("BOT_TOKEN configured", True)
            else:
                self.log_result("BOT_TOKEN configured", False, "BOT_TOKEN not set in .env")
            
            # Проверка SPREADSHEET_ID
            if cfg.SPREADSHEET_ID:
                self.log_result("SPREADSHEET_ID configured", True)
            else:
                self.log_result("SPREADSHEET_ID configured", False, "SPREADSHEET_ID not set in .env")
            
            # Проверка Google credentials
            creds_path = Path(cfg.GOOGLE_CREDENTIALS_PATH)
            if creds_path.exists():
                self.log_result("Google credentials file exists", True)
            else:
                self.log_result("Google credentials file exists", False, f"File not found: {creds_path}")
            
            # Проверка Admin IDs
            if cfg.ADMIN_USER_IDS:
                self.log_result("Admin users configured", True)
            else:
                self.log_result("Admin users configured", False, "No admin users set")
                
        except Exception as e:
            self.log_result("Environment configuration", False, str(e))
    
    async def test_handler_functions(self):
        """Тестирование функций-обработчиков"""
        print("\n🧪 Testing Handler Functions...")
        
        # Создаем моки
        mock_message = Mock(spec=types.Message)
        mock_message.from_user = Mock()
        mock_message.from_user.id = 123456789
        mock_message.from_user.first_name = "Test"
        mock_message.from_user.full_name = "Test User"
        mock_message.answer = AsyncMock()
        
        mock_state = AsyncMock(spec=FSMContext)
        mock_state.clear = AsyncMock()
        mock_state.set_state = AsyncMock()
        mock_state.update_data = AsyncMock()
        mock_state.get_data = AsyncMock(return_value={})
        
        # Test 1: /start command
        try:
            await cmd_start(mock_message, mock_state)
            if mock_message.answer.called and mock_state.clear.called:
                self.log_result("cmd_start function", True)
            else:
                self.log_result("cmd_start function", False, "Function did not execute properly")
        except Exception as e:
            self.log_result("cmd_start function", False, str(e))
        
        # Test 2: /help command
        try:
            mock_message.answer.reset_mock()
            await cmd_help(mock_message)
            if mock_message.answer.called:
                self.log_result("cmd_help function", True)
            else:
                self.log_result("cmd_help function", False, "Help message not sent")
        except Exception as e:
            self.log_result("cmd_help function", False, str(e))
        
        # Test 3: process_name with valid name
        try:
            mock_message.text = "John Doe"
            mock_message.answer.reset_mock()
            mock_state.update_data.reset_mock()
            mock_state.set_state.reset_mock()
            
            await process_name(mock_message, mock_state)
            
            if mock_state.update_data.called and mock_state.set_state.called:
                self.log_result("process_name (valid)", True)
            else:
                self.log_result("process_name (valid)", False, "Name not processed")
        except Exception as e:
            self.log_result("process_name (valid)", False, str(e))
        
        # Test 4: process_name with invalid name
        try:
            mock_message.text = "A"
            mock_message.answer.reset_mock()
            mock_state.update_data.reset_mock()
            mock_state.set_state.reset_mock()
            
            await process_name(mock_message, mock_state)
            
            # Should show error, not update state
            if mock_message.answer.called and not mock_state.set_state.called:
                self.log_result("process_name (invalid/short)", True)
            else:
                self.log_result("process_name (invalid/short)", False, "Validation not working")
        except Exception as e:
            self.log_result("process_name (invalid/short)", False, str(e))
        
        # Test 5: process_phone with valid phone
        try:
            mock_message.text = "+972501234567"
            mock_message.answer.reset_mock()
            mock_state.update_data.reset_mock()
            mock_state.set_state.reset_mock()
            
            await process_phone(mock_message, mock_state)
            
            if mock_state.update_data.called and mock_state.set_state.called:
                self.log_result("process_phone (valid)", True)
            else:
                self.log_result("process_phone (valid)", False, "Phone not processed")
        except Exception as e:
            self.log_result("process_phone (valid)", False, str(e))
        
        # Test 6: process_phone with invalid phone
        try:
            mock_message.text = "123"
            mock_message.answer.reset_mock()
            mock_state.update_data.reset_mock()
            mock_state.set_state.reset_mock()
            
            await process_phone(mock_message, mock_state)
            
            # Should show error, not update state
            if mock_message.answer.called and not mock_state.set_state.called:
                self.log_result("process_phone (invalid)", True)
            else:
                self.log_result("process_phone (invalid)", False, "Phone validation not working")
        except Exception as e:
            self.log_result("process_phone (invalid)", False, str(e))
    
    async def test_import_modules(self):
        """Проверка импортов всех модулей"""
        print("\n📦 Testing Module Imports...")
        
        modules = [
            ("src.bot.handlers.client_handlers", "Client handlers"),
            ("src.bot.handlers.admin_handlers", "Admin handlers"),
            ("src.services.booking_service", "Booking service"),
            ("src.services.calendar_service", "Calendar service"),
            ("src.services.sync_service", "Sync service"),
            ("src.db.sheets_client", "Sheets client"),
            ("src.config.config", "Config"),
            ("src.utils.validation", "Validation utils"),
            ("src.utils.time_utils", "Time utils"),
        ]
        
        for module_name, description in modules:
            try:
                __import__(module_name)
                self.log_result(f"Import {description}", True)
            except Exception as e:
                self.log_result(f"Import {description}", False, str(e))
    
    async def run_all_diagnostics(self):
        """Запустить все проверки"""
        print("=" * 60)
        print("🔍 BOT DIAGNOSTICS - CHECKING ALL FUNCTIONS")
        print("=" * 60)
        
        await self.check_environment()
        await self.test_import_modules()
        await self.test_handler_functions()
        
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTICS SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        print("=" * 60)
        
        if self.failed > 0:
            print("\n⚠️  Some tests failed. Check details above.")
            print("\n💡 Common fixes:")
            print("   1. Make sure .env file is configured")
            print("   2. Check BOT_TOKEN and SPREADSHEET_ID are set")
            print("   3. Verify credentials.json exists")
            print("   4. Run: python3 create_google_sheets_structure.py")
            return False
        else:
            print("\n✅ All diagnostics passed! Bot functions are working correctly.")
            return True


async def main():
    """Главная функция"""
    diagnostics = BotDiagnostics()
    success = await diagnostics.run_all_diagnostics()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
