#!/usr/bin/env python3
"""
Test unified data sync system
Tests integration between:
- Google Sheets (masters, services, schedule, bookings)
- Google Calendar (events)
- INKA (with data sync)
"""

import sys
from datetime import datetime, timedelta

from src.db.sheets_client import GoogleSheetsClient
from src.calendars.calendar_init import get_calendar_service
from src.services.data_sync import get_data_sync_service, DataSyncService
from src.config import get_config
from src.ai.advanced_inka import get_advanced_inka


def test_unified_system():
    """Test the unified data sync system"""
    
    print("\n" + "="*80)
    print("🔄 UNIFIED DATA SYNC SYSTEM TEST")
    print("="*80)
    
    try:
        # Initialize components
        config = get_config()
        
        print("\n1️⃣  Initializing components...")
        sheets_client = GoogleSheetsClient(
            config.google_credentials_json,
            config.google_spreadsheet_id
        )
        print("   ✅ Google Sheets client")
        
        calendar_service = get_calendar_service(config.google_credentials_json)
        if calendar_service:
            print("   ✅ Google Calendar service")
        else:
            print("   ⚠️  Google Calendar not available")
        
        # Create data sync service
        print("\n2️⃣  Creating DataSyncService...")
        data_sync = DataSyncService(sheets_client, calendar_service, sync_interval=60)
        print("   ✅ DataSyncService created")
        
        # Sync all data
        print("\n3️⃣  Performing full sync...")
        stats = data_sync.sync_all()
        
        print(f"   ✅ Sync completed")
        print(f"      Tables synced: {', '.join(stats.tables_synced)}")
        print(f"      Masters: {stats.masters_cached}")
        print(f"      Services: {stats.services_cached}")
        print(f"      Calendar events: {stats.events_synced}")
        if stats.errors:
            print(f"      ⚠️  Errors: {stats.errors}")
        
        # Test INKA with data sync
        print("\n4️⃣  Initializing INKA with data sync...")
        inka = get_advanced_inka(
            api_key=config.openai_api_key,
            assistant_id=config.openai_assistant_id,
            sheets_client=sheets_client,
            calendar_service=calendar_service,
            data_sync=data_sync
        )
        print("   ✅ INKA initialized")
        
        # Test search masters
        print("\n5️⃣  Testing master search...")
        keywords = ["реализм", "минимализм", "пирсинг"]
        
        for keyword in keywords:
            masters = inka.search_masters_unified(keyword)
            print(f"   🔍 Search '{keyword}': {len(masters)} results")
            for master in masters:
                print(f"      - {master.get('name')} ({master.get('specialization')})")
        
        # Test services
        print("\n6️⃣  Testing services...")
        services = inka.get_services_unified()
        print(f"   ✅ Total services: {len(services)}")
        for service in services[:3]:
            print(f"      - {service.get('name')}: ₪{service.get('price_from')}-{service.get('price_to')}")
        
        # Test available slots
        print("\n7️⃣  Testing available slots...")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        masters = inka.get_masters_unified()
        if masters:
            master_id = masters[0].get('id')
            print(f"   Master: {masters[0].get('name')} ({master_id})")
            
            slots = inka.get_available_slots_unified(master_id, tomorrow, 60)
            print(f"   ✅ Available slots on {tomorrow}: {len(slots)}")
            for slot in slots[:3]:
                print(f"      - {slot.get('time')}-{slot.get('end_time')}")
        
        # Test sync status
        print("\n8️⃣  Testing sync status...")
        sync_result = inka.sync_all_data()
        print(f"   Status: {sync_result.get('status')}")
        print(f"   Tables: {', '.join(sync_result.get('tables_synced', []))}")
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_unified_system()
    sys.exit(0 if success else 1)
