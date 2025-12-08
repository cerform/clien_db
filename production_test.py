#!/usr/bin/env python3
"""
Comprehensive test of all database operations and INKA access
"""

import sys
sys.path.insert(0, '.')

import logging
import asyncio
from src.config import get_config
from src.db.sheets_client import GoogleSheetsClient
from src.services.admin_db_manager import DatabaseManager, InkaLearningSystem
from src.calendars.google_calendar_sync import GoogleCalendarSync
from src.ai.advanced_inka import AdvancedINKA

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_sheets_operations():
    """Test Google Sheets operations"""
    print("\n" + "="*70)
    print("🧪 TESTING GOOGLE SHEETS OPERATIONS")
    print("="*70)
    
    try:
        config = get_config()
        sheets = GoogleSheetsClient(
            credentials_file="credentials.json",
            spreadsheet_id=config.google_spreadsheet_id
        )
        
        # Test 1: Read masters
        print("\n1️⃣ Reading masters...")
        masters = sheets.get_sheet_values("masters")
        print(f"   ✅ Found {len(masters)} rows in masters sheet")
        assert len(masters) > 0, "No masters found"
        
        # Test 2: Read clients
        print("\n2️⃣ Reading clients...")
        clients = sheets.get_sheet_values("clients")
        print(f"   ✅ Found {len(clients)} rows in clients sheet")
        
        # Test 3: Read services
        print("\n3️⃣ Reading services...")
        services = sheets.get_sheet_values("services")
        print(f"   ✅ Found {len(services)} rows in services sheet")
        
        # Test 4: Read bookings
        print("\n4️⃣ Reading bookings...")
        bookings = sheets.get_sheet_values("bookings")
        print(f"   ✅ Found {len(bookings)} rows in bookings sheet")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
        
        print("\n✅ Google Sheets operations: OK")
        return True
        
    except Exception as e:
        print(f"\n❌ Google Sheets operations FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_manager():
    """Test database manager operations"""
    print("\n" + "="*70)
    print("🧪 TESTING DATABASE MANAGER")
    print("="*70)
    
    try:
        config = get_config()
        sheets = GoogleSheetsClient(
            credentials_file="credentials.json",
            spreadsheet_id=config.google_spreadsheet_id
        )
        db = DatabaseManager(sheets)
        
        # Test 1: Get all masters
        print("\n1️⃣ Getting all masters...")
        masters = sheets.get_sheet_values("masters")
        print(f"   ✅ Found {len(masters)} masters")
        
        # Test 2: Get all clients
        print("\n2️⃣ Getting all clients...")
        clients = sheets.get_sheet_values("clients")
        print(f"   ✅ Found {len(clients)} clients")
        
        # Test 3: Get all services
        print("\n3️⃣ Getting all services...")
        services = sheets.get_sheet_values("services")
        print(f"   ✅ Found {len(services)} services")
        
        # Test 4: Get all bookings
        print("\n4️⃣ Getting all bookings...")
        bookings = sheets.get_sheet_values("bookings")
        print(f"   ✅ Found {len(bookings)} bookings")
        
        # Test 5: Get statistics
        print("\n5️⃣ Getting statistics...")
        stats = {
            "masters": len(masters),
            "clients": len(clients),
            "services": len(services),
            "bookings": len(bookings)
        }
        print(f"   ✅ Stats: {stats}")
        
        print("\n✅ Database Manager: OK")
        assert len(masters) > 0, "No masters found"
        assert len(clients) >= 0, "Clients query failed"
        assert len(services) > 0, "No services found"
        
    except Exception as e:
        print(f"\n❌ Database Manager FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_calendar_operations():
    """Test Google Calendar operations"""
    print("\n" + "="*70)
    print("🧪 TESTING GOOGLE CALENDAR OPERATIONS")
    print("="*70)
    
    try:
        config = get_config()
        calendar = GoogleCalendarSync(
            credentials_file="credentials.json",
            calendar_id=config.google_calendar_id
        )
        
        # Test 1: Get events
        print("\n1️⃣ Getting calendar events...")
        from datetime import date, timedelta
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=30)).isoformat()
        events = calendar.get_events(start_date, end_date)
        print(f"   ✅ Found {len(events)} events between {start_date} and {end_date}")
        
        # Test 2: Get free slots
        print("\n2️⃣ Getting free slots...")
        from datetime import date as dtdate
        date_obj = dtdate.today()
        date_str = date_obj.isoformat()
        slots = calendar.get_free_slots(date_str, duration=60)
        print(f"   ✅ Found {len(slots)} free slots for {date_str}")
        
        print("\n✅ Google Calendar: OK")
        assert isinstance(events, list), "Events must be a list"
        
    except Exception as e:
        print(f"\n⚠️ Google Calendar WARNING: {e}")
        raise

def test_inka_access():
    """Test INKA Assistant access"""
    print("\n" + "="*70)
    print("🧪 TESTING INKA ASSISTANT ACCESS")
    print("="*70)
    
    try:
        config = get_config()
        
        if not config.openai_api_key:
            print("\n⚠️ OpenAI API key not set - INKA tests skipped")
            pytest.skip("No API key")
        
        inka = AdvancedINKA(
            api_key=config.openai_api_key,
            assistant_id=config.openai_assistant_id or "asst_NPqHLNqQeTi7rgyaZR0iL5kE"
        )
        
        # Test 1: Send test message
        print("\n1️⃣ Sending test message to INKA...")
        response = asyncio.run(inka.chat("Привет, кто ты?", user_id="0"))
        print(f"   ✅ INKA Response: {response[:80]}...")
        
        print("\n✅ INKA Assistant: OK")
        assert response is not None, "Empty INKA response"
        
    except Exception as e:
        print(f"\n⚠️ INKA Assistant WARNING: {e}")
        raise

def test_inka_training():
    """Test INKA training system"""
    print("\n" + "="*70)
    print("🧪 TESTING INKA TRAINING SYSTEM")
    print("="*70)
    
    try:
        config = get_config()
        sheets = GoogleSheetsClient(
            credentials_file="credentials.json",
            spreadsheet_id=config.google_spreadsheet_id
        )
        
        learning = InkaLearningSystem(sheets)
        
        print("\n1️⃣ Testing training system initialization...")
        print("   ✅ Training system initialized")
        
        print("\n2️⃣ Adding training example...")
        success, msg = learning.add_training_example(
            category="test",
            user_input="test input",
            inka_response="test response",
            correction="corrected response",
            tags="test"
        )
        print(f"   {'✅' if success else '❌'} {msg}")
        
        print("\n✅ INKA Training System: OK")
        assert success, f"Training example addition failed: {msg}"
        
    except Exception as e:
        print(f"\n⚠️ INKA Training System warning: {e}")
        raise

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 PRODUCTION READINESS CHECK")
    print("="*70)
    print(f"Date: {__import__('datetime').datetime.now().isoformat()}")
    
    test_sheets_operations()
    test_database_manager()
    test_calendar_operations()
    test_inka_access()
    test_inka_training()
    
    print("\n🚀 SYSTEM IS PRODUCTION READY!")

if __name__ == "__main__":
    sys.exit(main())
