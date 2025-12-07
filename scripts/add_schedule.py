#!/usr/bin/env python3
"""Add schedule for new masters"""

import sys
from src.db.sheets_client import GoogleSheetsClient
from src.config import get_config

def add_schedule():
    """Add schedule for Platon and Sarah (Moshe)"""
    
    config = get_config()
    client = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    
    print("📋 ADDING SCHEDULE FOR NEW MASTERS")
    print("="*80)
    
    # New schedule entries
    new_schedules = [
        # Платон Сосницкий
        ["sch_platon_mon", "m_platon_sosnitsky", "0", "10:00", "19:00", "TRUE", "Обеденный перерыв 13:00-14:00"],
        ["sch_platon_tue", "m_platon_sosnitsky", "1", "10:00", "19:00", "TRUE", "Обеденный перерыв 13:00-14:00"],
        ["sch_platon_wed", "m_platon_sosnitsky", "2", "10:00", "19:00", "TRUE", "Обеденный перерыв 13:00-14:00"],
        ["sch_platon_thu", "m_platon_sosnitsky", "3", "10:00", "19:00", "TRUE", "Обеденный перерыв 13:00-14:00"],
        ["sch_platon_fri", "m_platon_sosnitsky", "4", "10:00", "19:00", "TRUE", "Обеденный перерыв 13:00-14:00"],
        ["sch_platon_sat", "m_platon_sosnitsky", "5", "12:00", "17:00", "TRUE", "Субботний график"],
        ["sch_platon_sun", "m_platon_sosnitsky", "6", "0:00", "0:00", "FALSE", "Выходной"],
        
        # Мойше (пирсинг)
        ["sch_moshe_mon", "m_sarah_moshe", "0", "10:00", "18:00", "TRUE", "Пирсинг"],
        ["sch_moshe_tue", "m_sarah_moshe", "1", "10:00", "18:00", "TRUE", "Пирсинг"],
        ["sch_moshe_wed", "m_sarah_moshe", "2", "10:00", "18:00", "TRUE", "Пирсинг"],
        ["sch_moshe_thu", "m_sarah_moshe", "3", "10:00", "18:00", "TRUE", "Пирсинг"],
        ["sch_moshe_fri", "m_sarah_moshe", "4", "10:00", "18:00", "TRUE", "Пирсинг"],
        ["sch_moshe_sat", "m_sarah_moshe", "5", "10:00", "14:00", "TRUE", "Субботний график"],
        ["sch_moshe_sun", "m_sarah_moshe", "6", "0:00", "0:00", "FALSE", "Выходной"],
    ]
    
    # Get current schedule
    schedule_all = client.get_all_rows("schedule")
    
    print(f"Current schedule entries: {len(schedule_all) - 1}")
    
    # Add new entries
    new_rows = schedule_all + new_schedules
    
    print(f"Adding {len(new_schedules)} new entries...")
    
    try:
        # Clear and rewrite
        client.service.spreadsheets().values().clear(
            spreadsheetId=client.spreadsheet_id,
            range="schedule"
        ).execute()
        
        client.service.spreadsheets().values().update(
            spreadsheetId=client.spreadsheet_id,
            range="schedule!A1",
            valueInputOption="RAW",
            body={"values": new_rows}
        ).execute()
        
        print(f"✅ Schedule updated!")
        print(f"   Total entries: {len(new_rows) - 1}")
        print(f"   - Анна: 7 days")
        print(f"   - Платон: 7 days")
        print(f"   - Мойше: 7 days")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating schedule: {e}")
        return False


if __name__ == "__main__":
    success = add_schedule()
    sys.exit(0 if success else 1)
