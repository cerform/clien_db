#!/usr/bin/env python3
"""
🔍 DEBUG CONFIG CHECKER
Полная диагностика конфигурации, доступа к Google Sheets/Calendar и БД
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.db.sheets_client import GoogleSheetsClient
from src.calendars.google_calendar_sync import GoogleCalendarSync


class ConfigDebugger:
    """Comprehensive configuration debugger"""
    
    def __init__(self):
        self.issues: List[Tuple[str, str, str]] = []  # (severity, category, message)
        self.checks_passed = 0
        self.checks_failed = 0
    
    def add_issue(self, severity: str, category: str, message: str):
        """Add issue to report"""
        self.issues.append((severity, category, message))
        if severity == "ERROR":
            self.checks_failed += 1
        else:
            self.checks_passed += 1
    
    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{'='*70}")
        print(f"📋 {title}")
        print(f"{'='*70}")
    
    def print_result(self, status: str, message: str, details: str = ""):
        """Print single check result"""
        icon = "✅" if status == "OK" else "⚠️ " if status == "WARN" else "❌"
        print(f"{icon} {message}")
        if details:
            print(f"   └─ {details}")
    
    def check_config_loading(self):
        """Check if configuration loads without errors"""
        self.print_header("1. CONFIGURATION LOADING")
        
        try:
            config = get_config()
            self.print_result("OK", "Configuration loaded successfully")
            self.add_issue("OK", "config_loading", "Configuration loaded")
            return config
        except Exception as e:
            self.print_result("ERROR", f"Failed to load configuration: {e}")
            self.add_issue("ERROR", "config_loading", str(e))
            return None
    
    def check_env_variables(self, config):
        """Check environment variables"""
        self.print_header("2. ENVIRONMENT VARIABLES")
        
        if not config:
            self.print_result("ERROR", "Cannot check env - config not loaded")
            return
        
        checks = {
            "TELEGRAM_BOT_TOKEN": ("set", len(config.telegram_bot_token) > 0),
            "GOOGLE_SPREADSHEET_ID": ("valid length", len(config.google_spreadsheet_id) > 20),
            "GOOGLE_CALENDAR_ID": ("set", bool(config.google_calendar_id)),
            "OPENAI_API_KEY": ("set", bool(config.openai_api_key)),
            "TIMEZONE": ("valid", config.timezone in ["Europe/Moscow", "Asia/Jerusalem", "Europe/London", "America/New_York", "UTC"] or True),
            "ADMIN_IDS": ("parsed", len(config.admin_ids) > 0),
        }
        
        for var_name, (check_type, result) in checks.items():
            if result:
                self.print_result("OK", f"{var_name}: {check_type}")
                self.add_issue("OK", "env_vars", f"{var_name} ok")
            else:
                self.print_result("WARN", f"{var_name}: NOT {check_type}")
                self.add_issue("WARN", "env_vars", f"{var_name} missing or invalid")
        
        # Print parsed values
        print(f"\n📝 Parsed Configuration:")
        print(f"   • Telegram Token: {'●' * 10}... (hidden)")
        print(f"   • Spreadsheet ID: {config.google_spreadsheet_id[:20]}...")
        print(f"   • Calendar ID: {config.google_calendar_id or 'NOT SET'}")
        print(f"   • Timezone: {config.timezone}")
        print(f"   • Admin IDs: {config.admin_ids}")
        print(f"   • OpenAI API: {'SET' if config.openai_api_key else 'NOT SET'}")
        print(f"   • OpenAI Assistant: {config.openai_assistant_id or 'NOT SET'}")
    
    def check_credentials_file(self, config):
        """Check if credentials file exists and is readable"""
        self.print_header("3. CREDENTIALS FILE")
        
        if not config:
            self.print_result("ERROR", "Cannot check credentials - config not loaded")
            return
        
        # Try default locations
        possible_paths = [
            Path("credentials.json"),
            Path(__file__).parent.parent.parent / "credentials.json",
            Path(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")).expanduser(),
        ]
        
        found_path = None
        for path in possible_paths:
            if path.exists():
                found_path = path
                break
        
        if found_path:
            self.print_result("OK", f"Credentials file found: {found_path}")
            self.add_issue("OK", "credentials", f"Found at {found_path}")
            
            # Try to read and parse
            try:
                import json
                with open(found_path) as f:
                    creds_data = json.load(f)
                    print(f"\n📋 Credentials Details:")
                    print(f"   • Type: {creds_data.get('type')}")
                    print(f"   • Project: {creds_data.get('project_id')}")
                    print(f"   • Service Account: {creds_data.get('client_email')}")
                    self.print_result("OK", "Credentials file is valid JSON")
                    self.add_issue("OK", "credentials", "Valid JSON format")
            except Exception as e:
                self.print_result("ERROR", f"Credentials file is corrupted: {e}")
                self.add_issue("ERROR", "credentials", f"Parse error: {e}")
        else:
            self.print_result("WARN", "Credentials file NOT found in default locations")
            self.add_issue("WARN", "credentials", "File not found - will use Cloud Run Service Account")
            print(f"\n📍 Checked locations:")
            for path in possible_paths:
                status = "✓" if path.exists() else "✗"
                print(f"   {status} {path}")
    
    def check_google_sheets_access(self, config):
        """Test Google Sheets API access"""
        self.print_header("4. GOOGLE SHEETS ACCESS")
        
        if not config:
            self.print_result("ERROR", "Cannot check Sheets - config not loaded")
            return
        
        try:
            # Try to initialize client
            sheets_client = GoogleSheetsClient(
                credentials_file="credentials.json" if Path("credentials.json").exists() else None,
                spreadsheet_id=config.google_spreadsheet_id
            )
            self.print_result("OK", "Google Sheets client initialized")
            self.add_issue("OK", "sheets_init", "Client created")
            
            # Try to access spreadsheet metadata
            try:
                spreadsheet = sheets_client.service.spreadsheets().get(
                    spreadsheetId=config.google_spreadsheet_id
                ).execute()
                
                self.print_result("OK", "Spreadsheet accessible")
                self.add_issue("OK", "sheets_access", "Spreadsheet found")
                
                print(f"\n📊 Spreadsheet Info:")
                print(f"   • Title: {spreadsheet.get('properties', {}).get('title')}")
                print(f"   • Sheets: {len(spreadsheet.get('sheets', []))}")
                
                sheet_names = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
                print(f"\n📑 Available Sheets:")
                for name in sheet_names:
                    status = "✓" if name in ['clients', 'masters', 'services', 'bookings'] else "⚠️"
                    print(f"   {status} {name}")
                
                # Check for critical sheets
                required_sheets = {'clients', 'masters', 'services', 'bookings'}
                found_sheets = set(sheet_names)
                missing = required_sheets - found_sheets
                
                if missing:
                    self.print_result("WARN", f"Missing sheets: {', '.join(missing)}")
                    self.add_issue("WARN", "sheets_structure", f"Missing: {missing}")
                else:
                    self.print_result("OK", "All required sheets present")
                    self.add_issue("OK", "sheets_structure", "All sheets found")
                
            except Exception as e:
                self.print_result("ERROR", f"Cannot access spreadsheet: {e}")
                self.add_issue("ERROR", "sheets_access", f"Access denied: {e}")
        
        except Exception as e:
            self.print_result("ERROR", f"Google Sheets client failed: {e}")
            self.add_issue("ERROR", "sheets_init", f"Initialization failed: {e}")
    
    def check_google_calendar_access(self, config):
        """Test Google Calendar API access"""
        self.print_header("5. GOOGLE CALENDAR ACCESS")
        
        if not config or not config.google_calendar_id:
            self.print_result("WARN", "Google Calendar ID not configured")
            self.add_issue("WARN", "calendar", "Calendar ID not set")
            return
        
        try:
            # Try to initialize calendar client
            calendar_client = GoogleCalendarSync(
                credentials_file="credentials.json" if Path("credentials.json").exists() else None,
                calendar_id=config.google_calendar_id
            )
            self.print_result("OK", "Google Calendar client initialized")
            self.add_issue("OK", "calendar_init", "Client created")
            
            # Try to list events
            try:
                events_result = calendar_client.service.events().list(
                    calendarId=config.google_calendar_id,
                    maxResults=1,
                    orderBy='startTime',
                    singleEvents=True
                ).execute()
                
                events = events_result.get('items', [])
                self.print_result("OK", "Calendar accessible")
                self.add_issue("OK", "calendar_access", "Calendar found")
                
                print(f"\n📅 Calendar Info:")
                print(f"   • Calendar ID: {config.google_calendar_id}")
                print(f"   • Recent events: {len(events)}")
                
            except Exception as e:
                self.print_result("ERROR", f"Cannot access calendar: {e}")
                self.add_issue("ERROR", "calendar_access", f"Access error: {e}")
        
        except Exception as e:
            self.print_result("ERROR", f"Google Calendar client failed: {e}")
            self.add_issue("ERROR", "calendar_init", f"Initialization failed: {e}")
    
    def check_admin_ids(self, config):
        """Verify admin IDs configuration"""
        self.print_header("6. ADMIN IDS")
        
        if not config:
            self.print_result("ERROR", "Cannot check admin IDs - config not loaded")
            return
        
        if not config.admin_ids:
            self.print_result("WARN", "No admin IDs configured")
            self.add_issue("WARN", "admin_ids", "Empty list")
        else:
            self.print_result("OK", f"{len(config.admin_ids)} admin ID(s) configured")
            self.add_issue("OK", "admin_ids", f"Count: {len(config.admin_ids)}")
            
            print(f"\n👤 Admin IDs:")
            for admin_id in config.admin_ids:
                print(f"   • {admin_id} (type: {type(admin_id).__name__})")
            
            # Verify types
            all_int = all(isinstance(id, int) for id in config.admin_ids)
            if all_int:
                self.print_result("OK", "All admin IDs are integers")
                self.add_issue("OK", "admin_ids_types", "Correct type")
            else:
                self.print_result("ERROR", "Admin IDs have wrong types")
                self.add_issue("ERROR", "admin_ids_types", "Type mismatch")
    
    def print_summary(self):
        """Print final summary"""
        self.print_header("SUMMARY")
        
        total = self.checks_passed + self.checks_failed
        
        print(f"\n📊 Overall Status:")
        print(f"   ✅ Passed: {self.checks_passed}")
        print(f"   ❌ Failed: {self.checks_failed}")
        print(f"   Total:   {total}")
        
        if self.checks_failed == 0:
            print(f"\n🎉 All checks passed! Bot should work correctly.")
        else:
            print(f"\n⚠️  Fix the issues above before running the bot.")
        
        # Print issues by category
        print(f"\n📝 Issues by Category:")
        categories = {}
        for severity, category, message in self.issues:
            if category not in categories:
                categories[category] = []
            categories[category].append((severity, message))
        
        for category, items in sorted(categories.items()):
            errors = [m for s, m in items if s == "ERROR"]
            warnings = [m for s, m in items if s == "WARN"]
            
            if errors:
                print(f"\n   ❌ {category.upper()}:")
                for msg in errors:
                    print(f"      • {msg}")
            if warnings:
                print(f"\n   ⚠️  {category.upper()}:")
                for msg in warnings:
                    print(f"      • {msg}")
    
    def run_all_checks(self):
        """Run all diagnostics"""
        print("\n" + "="*70)
        print("🔍 INKA BOT - CONFIGURATION DEBUG CHECKER")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        print("="*70)
        
        config = self.check_config_loading()
        if config:
            self.check_env_variables(config)
            self.check_credentials_file(config)
            self.check_google_sheets_access(config)
            self.check_google_calendar_access(config)
            self.check_admin_ids(config)
        
        self.print_summary()
        print("\n" + "="*70 + "\n")
        
        return self.checks_failed == 0


if __name__ == "__main__":
    debugger = ConfigDebugger()
    success = debugger.run_all_checks()
    sys.exit(0 if success else 1)
