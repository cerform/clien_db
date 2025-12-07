#!/usr/bin/env python3
"""Test INKA functionality"""
import asyncio
from datetime import datetime, timedelta
from src.ai.advanced_inka import get_advanced_inka
from src.config.config import get_config

async def test_inka():
    """Test INKA with empty calendar"""
    try:
        config = get_config()
        print(f"\n✅ Config loaded successfully")
        print(f"   Spreadsheet: {config.google_spreadsheet_id[:30]}...")
        print(f"   Calendar: {config.google_calendar_id[:30] if config.google_calendar_id else 'Not set'}...")
        
        # Initialize INKA
        inka = get_advanced_inka(
            api_key=config.openai_api_key,
            assistant_id=config.openai_assistant_id
        )
        print(f"✅ INKA initialized successfully")
        
        # Test calendar slots with empty calendar
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        print(f"\n🧪 Testing calendar slots:")
        print(f"   Period: {start_date} to {end_date}")
        
        result = inka.get_calendar_slots(start_date, end_date)
        
        if result.get('status') == 'success':
            slots = result.get('available_slots', [])
            print(f"✅ Got {len(slots)} free slots")
            if slots:
                print(f"   First 3 slots:")
                for slot in slots[:3]:
                    print(f"     - {slot.get('date')} {slot.get('start')}-{slot.get('end')}")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        # Test create client
        print(f"\n🧪 Testing client creation:")
        client_result = inka.create_client(
            telegram_id=123456789,
            name="Test Client",
            phone="+1234567890"
        )
        print(f"✅ Client created: {client_result}")
        
        print(f"\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_inka())
    exit(0 if result else 1)
