#!/usr/bin/env python3
"""Test script for empty calendar with INKA"""
import asyncio
import sys
from datetime import datetime, timedelta
from src.ai.advanced_inka import get_advanced_inka

async def test_empty_calendar():
    """Test getting slots from empty calendar"""
    try:
        inka = await get_advanced_inka()
        
        # Даты для проверки
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        print(f"\n🧪 Testing INKA with empty calendar")
        print(f"Period: {start_date} to {end_date}")
        print("=" * 50)
        
        # Получаем слоты
        result = inka.get_calendar_slots(start_date, end_date)
        
        print("\n📊 Result:")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            slots = result.get('available_slots', [])
            print(f"✅ Found {len(slots)} free slots")
            
            # Показываем первые 5 слотов
            if slots:
                print("\n📅 First 5 slots:")
                for i, slot in enumerate(slots[:5], 1):
                    print(f"   {i}. {slot.get('date')} {slot.get('start')} - {slot.get('end')}")
                
                if len(slots) > 5:
                    print(f"   ... and {len(slots) - 5} more slots")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_empty_calendar())
