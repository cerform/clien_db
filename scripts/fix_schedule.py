#!/usr/bin/env python3
"""Clean and fix schedule table to match current masters"""

import sys
from src.db.sheets_client import GoogleSheetsClient
from src.config import get_config

def fix_schedule_table():
    """Remove schedule entries for non-existent masters"""
    
    config = get_config()
    client = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    
    print("📋 SCHEDULE TABLE CLEANUP")
    print("="*80)
    
    # Get current masters
    masters = client.get_all_rows("masters")
    master_ids = {m[0] for m in masters[1:]}
    print(f"✅ Valid master IDs: {master_ids}\n")
    
    # Get schedule
    schedule_all = client.get_all_rows("schedule")
    headers = schedule_all[0]
    
    print(f"Schedule entries before: {len(schedule_all) - 1}")
    
    # Filter valid entries
    valid_rows = [headers]  # Start with headers
    invalid_count = 0
    
    for row in schedule_all[1:]:
        master_id = row[1]  # Column B: master_id
        if master_id in master_ids:
            valid_rows.append(row)
        else:
            print(f"❌ Removing invalid entry: {row[0]} (master: {master_id})")
            invalid_count += 1
    
    print(f"\nRemoving {invalid_count} invalid entries...")
    
    # Write back only valid rows
    try:
        # Clear the sheet
        client.service.spreadsheets().values().clear(
            spreadsheetId=client.spreadsheet_id,
            range="schedule"
        ).execute()
        
        # Write valid rows back
        client.service.spreadsheets().values().update(
            spreadsheetId=client.spreadsheet_id,
            range="schedule!A1",
            valueInputOption="RAW",
            body={"values": valid_rows}
        ).execute()
        
        print(f"✅ Schedule updated!")
        print(f"   Valid entries: {len(valid_rows) - 1}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating schedule: {e}")
        return False


if __name__ == "__main__":
    success = fix_schedule_table()
    sys.exit(0 if success else 1)
