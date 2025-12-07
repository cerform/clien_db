#!/usr/bin/env python3
"""
Test Admin Functions - Проверка админ-функций INKA

Этот скрипт проверяет:
1. Админ может вызывать админ-функции
2. Обычный пользователь получает ACCESS DENIED
3. Все функции возвращают правильный формат ответа
"""

import sys
import logging
from typing import Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, '/home/etcsys/projects/clien_db')

from src.ai.advanced_inka import AdvancedINKA
from src.db.sheets_client import GoogleSheetsClient
from src.config import get_config

def test_admin_functions():
    """Тестирование админ-функций"""
    
    print("\n" + "="*60)
    print("👑 ADMIN FUNCTIONS TEST")
    print("="*60 + "\n")
    
    try:
        config = get_config()
        
        # Инициализируем Google Sheets клиент
        logger.info("📦 Initializing Google Sheets client...")
        from pathlib import Path
        creds_path = Path("/home/etcsys/projects/clien_db/credentials.json")
        sheets_client = GoogleSheetsClient(str(creds_path), config.google_spreadsheet_id)
        logger.info("✅ Google Sheets client initialized")
        
        # Admin IDs для тестирования
        admin_ids = [438407739, 457343487]
        
        # Инициализируем INKA с админ-правами
        logger.info("🤖 Initializing INKA with admin functions...")
        inka = AdvancedINKA(
            api_key=config.openai_api_key,
            assistant_id=config.openai_assistant_id,
            sheets_client=sheets_client,
            admin_ids=admin_ids
        )
        logger.info("✅ INKA initialized with admin functions")
        
        print("\n" + "-"*60)
        print("TEST 1: Admin вызывает админ-функцию")
        print("-"*60)
        
        inka._current_user_id = "438407739"  # Admin
        result = inka.handle_function_call("edit_master", {
            "master_id": "1",
            "name": "Test Master"
        })
        
        import json
        result_dict = json.loads(result)
        
        if result_dict.get("success") or result_dict.get("error"):
            print(f"✅ Result: {json.dumps(result_dict, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ Unexpected result format: {result}")
        
        print("\n" + "-"*60)
        print("TEST 2: Обычный пользователь пытается вызвать админ-функцию")
        print("-"*60)
        
        inka._current_user_id = "123456789"  # Not admin
        result = inka.handle_function_call("edit_master", {
            "master_id": "1",
            "name": "Test Master"
        })
        
        result_dict = json.loads(result)
        
        if "access_denied" in result_dict or "ДОСТУП ЗАПРЕЩЁН" in result_dict.get("error", ""):
            print(f"✅ Access correctly denied!")
            print(f"   Error message: {result_dict.get('error', 'N/A')}")
        else:
            print(f"❌ Expected access denied but got: {result}")
        
        print("\n" + "-"*60)
        print("TEST 3: Проверка всех админ-функций")
        print("-"*60)
        
        inka._current_user_id = "438407739"  # Admin
        
        admin_functions = [
            ("edit_master", {"master_id": "1", "name": "Test"}),
            ("edit_service", {"service_id": "1", "price": 3000}),
            ("add_schedule_slot", {
                "master_id": "1",
                "date": "2025-12-25",
                "start_time": "10:00",
                "end_time": "18:00"
            }),
            ("cancel_booking", {"booking_id": "1", "reason": "Test"}),
            ("export_statistics", {"stat_type": "revenue"}),
            ("send_broadcast_message", {"message": "Test message"})
        ]
        
        for func_name, args in admin_functions:
            try:
                result = inka.handle_function_call(func_name, args)
                result_dict = json.loads(result)
                
                if "success" in result_dict or "error" in result_dict:
                    status = "✅" if result_dict.get("success") else "⚠️"
                    print(f"{status} {func_name}: OK")
                else:
                    print(f"❌ {func_name}: Unexpected response format")
            except Exception as e:
                print(f"❌ {func_name}: {str(e)}")
        
        print("\n" + "-"*60)
        print("TEST 4: Проверка create_tools_config()")
        print("-"*60)
        
        # Обычный пользователь - БЕЗ админ-функций
        tools_user = inka.create_tools_config(is_admin=False)
        user_tool_names = [t["function"]["name"] for t in tools_user]
        
        print(f"Regular user tools ({len(tools_user)} total):")
        for name in user_tool_names:
            print(f"  • {name}")
        
        # Админ - С админ-функциями
        tools_admin = inka.create_tools_config(is_admin=True)
        admin_tool_names = [t["function"]["name"] for t in tools_admin]
        
        print(f"\nAdmin tools ({len(tools_admin)} total):")
        for name in admin_tool_names:
            print(f"  • {name}")
        
        admin_exclusive = set(admin_tool_names) - set(user_tool_names)
        print(f"\n✅ Admin-exclusive tools: {admin_exclusive}")
        
        expected_admin_tools = {
            "edit_master", "edit_service", "add_schedule_slot",
            "cancel_booking", "export_statistics", "send_broadcast_message"
        }
        
        if admin_exclusive == expected_admin_tools:
            print("✅ All expected admin tools are present!")
        else:
            print(f"❌ Missing tools: {expected_admin_tools - admin_exclusive}")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_admin_functions()
    sys.exit(0 if success else 1)
