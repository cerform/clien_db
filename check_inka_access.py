#!/usr/bin/env python3
"""
Comprehensive INKA Access Rights Checker
Проверяет доступ INKA ко всем требуемым ресурсам:
- Google Sheets (read/write)
- Google Calendar (read/write)
- Database tables (structure check)
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.END}\n")

def print_ok(text: str):
    print(f"{Colors.OK}✅ {text}{Colors.END}")

def print_fail(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.END}")

def print_warn(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

class INKAAccessChecker:
    def __init__(self):
        self.results = []
        self.spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        
    def check_environment(self) -> bool:
        """Check required environment variables"""
        print_header("1. Environment Variables Check")
        
        required_vars = {
            "GOOGLE_SPREADSHEET_ID": "Google Sheets ID",
            "GOOGLE_CALENDAR_ID": "Google Calendar ID",
            "OPENAI_API_KEY": "OpenAI API Key",
            "OPENAI_ASSISTANT_ID": "OpenAI Assistant ID",
            "TELEGRAM_BOT_TOKEN": "Telegram Bot Token"
        }
        
        all_present = True
        for var, desc in required_vars.items():
            value = os.getenv(var)
            if value:
                print_ok(f"{desc}: {var[:20]}... set")
            else:
                print_fail(f"{desc}: {var} NOT SET")
                all_present = False
        
        return all_present
    
    def check_google_sheets_read(self) -> Tuple[bool, str]:
        """Check Google Sheets read access"""
        print_header("2. Google Sheets - Read Access Check")
        
        try:
            from src.db.sheets_client import GoogleSheetsClient
            
            print_info(f"Connecting to Sheets: {self.spreadsheet_id[:30]}...")
            client = GoogleSheetsClient("", self.spreadsheet_id)
            print_ok("✓ Authenticated with Cloud Run Service Account")
            
            # Check required sheets
            required_sheets = ["clients", "masters", "bookings", "services"]
            
            for sheet_name in required_sheets:
                try:
                    values = client.get_sheet_values(sheet_name, "A1:A1")
                    print_ok(f"✓ Can read '{sheet_name}' sheet")
                    
                    if values and len(values) > 0:
                        print_info(f"  Sheet has {len(values)} rows (header row visible)")
                    else:
                        print_warn(f"  '{sheet_name}' sheet is empty or not found")
                        
                except Exception as e:
                    print_fail(f"✗ Cannot read '{sheet_name}': {str(e)[:100]}")
                    return False, str(e)
            
            print_ok("All required sheets are readable")
            return True, "All sheets readable"
            
        except Exception as e:
            print_fail(f"Google Sheets access failed: {str(e)[:100]}")
            logger.exception("Sheets error:")
            return False, str(e)
    
    def check_google_sheets_write(self) -> Tuple[bool, str]:
        """Check Google Sheets write access"""
        print_header("3. Google Sheets - Write Access Check")
        
        try:
            from src.db.sheets_client import GoogleSheetsClient
            import uuid
            
            client = GoogleSheetsClient("", self.spreadsheet_id)
            
            # Create a test row to append
            test_id = f"test_{uuid.uuid4().hex[:8]}"
            test_row = [
                test_id,
                "438407739",
                f"TEST_USER_{datetime.now().strftime('%H%M%S')}",
                "+1234567890",
                "test@example.com",
                f"Access check at {datetime.now().isoformat()}",
                datetime.now().isoformat(),
                ""
            ]
            
            print_info(f"Attempting to write test row to 'clients' sheet...")
            print_info(f"Test ID: {test_id}")
            
            success = client.append_row("clients", test_row)
            
            if success:
                print_ok("✓ Successfully wrote test row to 'clients'")
                
                # Verify the write
                print_info("Verifying write...")
                all_rows = client.get_sheet_values("clients")
                
                # Find our test row
                found = False
                for row in all_rows:
                    if len(row) > 0 and row[0] == test_id:
                        found = True
                        print_ok(f"✓ Test row verified in sheet: {row[:3]}")
                        break
                
                if not found:
                    print_warn("⚠️  Test row written but not found in verification (data may be cached)")
                
                return True, "Write access confirmed"
            else:
                print_fail("✗ Write failed - append_row returned False")
                return False, "append_row returned False"
                
        except Exception as e:
            print_fail(f"Google Sheets write access failed: {str(e)[:100]}")
            logger.exception("Write error:")
            return False, str(e)
    
    def check_google_calendar(self) -> Tuple[bool, str]:
        """Check Google Calendar access"""
        print_header("4. Google Calendar - Access Check")
        
        try:
            from src.calendars.calendar_init import get_calendar_service
            
            print_info(f"Connecting to Calendar: {self.calendar_id}...")
            calendar_service = get_calendar_service("")
            
            if calendar_service is None:
                print_fail("✗ Calendar service is None")
                return False, "Calendar service initialization failed"
            
            print_ok("✓ Calendar service initialized")
            
            # Try to read calendar
            print_info("Attempting to read calendar events...")
            events = calendar_service.events().list(
                calendarId=self.calendar_id,
                maxResults=1,
                showDeleted=False
            ).execute()
            
            item_count = len(events.get('items', []))
            print_ok(f"✓ Can read calendar (found {item_count} event(s))")
            
            # Try to create a test event
            print_info("Attempting to create test event...")
            test_event = {
                'summary': '[TEST] INKA Access Check',
                'description': f'Access verification at {datetime.now().isoformat()}',
                'start': {
                    'dateTime': (datetime.now() + timedelta(hours=1)).isoformat(),
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': (datetime.now() + timedelta(hours=2)).isoformat(),
                    'timeZone': 'UTC'
                }
            }
            
            result = calendar_service.events().insert(
                calendarId=self.calendar_id,
                body=test_event
            ).execute()
            
            print_ok(f"✓ Successfully created test event: {result.get('id')}")
            
            return True, "Calendar access confirmed"
            
        except Exception as e:
            print_fail(f"Google Calendar access failed: {str(e)[:100]}")
            logger.exception("Calendar error:")
            return False, str(e)
    
    def check_database_structure(self) -> Tuple[bool, str]:
        """Check database structure and required columns"""
        print_header("5. Database Structure Check")
        
        try:
            from src.db.sheets_client import GoogleSheetsClient
            
            client = GoogleSheetsClient("", self.spreadsheet_id)
            
            # Expected schema
            expected_schema = {
                "clients": ["id", "telegram_id", "name", "phone", "email", "notes", "created_at", "last_visit"],
                "masters": ["id", "name", "phone", "email", "specialty", "rating"],
                "bookings": ["id", "client_id", "master_id", "service_id", "date", "time", "duration_min", "price", "status", "notes", "created_at"],
                "services": ["id", "name", "price", "duration_min", "description"]
            }
            
            all_good = True
            for sheet_name, expected_cols in expected_schema.items():
                try:
                    rows = client.get_sheet_values(sheet_name)
                    
                    if not rows or len(rows) == 0:
                        print_warn(f"✗ '{sheet_name}' sheet is empty")
                        continue
                    
                    header_row = rows[0]
                    print_info(f"\n  Sheet: '{sheet_name}'")
                    print_info(f"  Expected columns: {expected_cols}")
                    print_info(f"  Actual columns: {header_row}")
                    
                    # Check if all expected columns are present
                    missing = [col for col in expected_cols if col not in header_row]
                    extra = [col for col in header_row if col not in expected_cols]
                    
                    if missing:
                        print_warn(f"  ⚠️  Missing columns: {missing}")
                        all_good = False
                    
                    if extra:
                        print_info(f"  ℹ️  Extra columns: {extra}")
                    
                    if not missing:
                        print_ok(f"  ✓ All required columns present ({len(header_row)} total)")
                    
                    # Count data rows
                    data_rows = len(rows) - 1  # Exclude header
                    print_info(f"  Data rows: {data_rows}")
                    
                except Exception as e:
                    print_fail(f"  ✗ Error reading '{sheet_name}': {str(e)[:80]}")
                    all_good = False
            
            if all_good:
                print_ok("\n✓ Database structure check passed")
            
            return all_good, "Structure check complete"
            
        except Exception as e:
            print_fail(f"Database structure check failed: {str(e)[:100]}")
            logger.exception("Structure check error:")
            return False, str(e)
    
    def check_inka_functions(self) -> Tuple[bool, str]:
        """Check INKA AI functions can be called"""
        print_header("6. INKA AI - Functions Check")
        
        try:
            from src.ai.advanced_inka import AdvancedINKA
            from src.db.sheets_client import GoogleSheetsClient
            
            sheets = GoogleSheetsClient("", self.spreadsheet_id)
            print_ok("✓ GoogleSheetsClient initialized")
            
            inka = AdvancedINKA(
                api_key=os.getenv("OPENAI_API_KEY"),
                assistant_id=os.getenv("OPENAI_ASSISTANT_ID"),
                sheets_client=sheets,
                calendar_service=None
            )
            print_ok("✓ INKA instance created")
            
            # Check tools configuration
            tools = inka.create_tools_config()
            print_ok(f"✓ Tools configured: {len(tools)} tools available")
            
            for tool in tools:
                func_name = tool['function']['name']
                print_info(f"  - {func_name}")
            
            # Test get_database_info
            print_info("\nTesting get_database_info function...")
            result = inka.get_database_info("masters", "id", "anna", limit=1)
            if "data" in result:
                print_ok(f"✓ get_database_info works (found {len(result['data'])} results)")
            else:
                print_warn(f"⚠️  get_database_info returned: {result}")
            
            # Test create_client function
            print_info("\nTesting create_client function...")
            result = inka.create_client(
                telegram_id="999999999",
                name="Test User",
                phone="+1234567890"
            )
            if result.get("success"):
                print_ok(f"✓ create_client works: {result.get('message')}")
            else:
                print_fail(f"✗ create_client failed: {result.get('error')}")
                return False, f"create_client error: {result.get('error')}"
            
            print_ok("\n✓ INKA functions check passed")
            return True, "INKA functions working"
            
        except Exception as e:
            print_fail(f"INKA functions check failed: {str(e)[:100]}")
            logger.exception("INKA error:")
            return False, str(e)
    
    def run_all_checks(self):
        """Run all checks"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("╔" + "="*68 + "╗")
        print("║" + " "*15 + "INKA ACCESS RIGHTS CHECKER" + " "*27 + "║")
        print("║" + " "*68 + "║")
        print("║  Checking permissions for Google Sheets, Calendar, and INKA functions" + " "*3 + "║")
        print("╚" + "="*68 + "╝")
        print(Colors.END)
        
        checks = [
            ("Environment Variables", self.check_environment),
            ("Google Sheets Read", self.check_google_sheets_read),
            ("Google Sheets Write", self.check_google_sheets_write),
            ("Google Calendar", self.check_google_calendar),
            ("Database Structure", self.check_database_structure),
            ("INKA Functions", self.check_inka_functions),
        ]
        
        results = {}
        for check_name, check_func in checks:
            try:
                if check_name == "Environment Variables":
                    success = check_func()
                    results[check_name] = (success, "")
                else:
                    success, message = check_func()
                    results[check_name] = (success, message)
            except Exception as e:
                logger.exception(f"Check '{check_name}' failed with exception:")
                results[check_name] = (False, str(e))
        
        # Summary
        print_header("SUMMARY")
        
        all_passed = True
        for check_name, (success, message) in results.items():
            if success:
                print_ok(f"{check_name}")
            else:
                print_fail(f"{check_name}")
                if message:
                    print(f"         Error: {message[:100]}")
                all_passed = False
        
        print()
        if all_passed:
            print(f"{Colors.OK}{Colors.BOLD}🎉 ALL CHECKS PASSED! INKA has full access to all resources.{Colors.END}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}⚠️  SOME CHECKS FAILED! Please fix the issues above.{Colors.END}")
        
        return all_passed

def main():
    checker = INKAAccessChecker()
    all_passed = checker.run_all_checks()
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
