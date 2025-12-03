#!/usr/bin/env python3
"""Initialize admin_messages table in Google Sheets"""

import sys
sys.path.insert(0, '/Users/simanbekov/ttmanager/tattoo_appointment_bot')

from src.config.env_loader import load_env
from src.config.config import Config
from src.db.sheets_client import SheetsClient

def init_admin_messages_table():
    """Create admin_messages table in spreadsheet"""
    load_env()
    cfg = Config.from_env()
    
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        
        # Check if table exists
        try:
            sc.get_range("admin_messages", "A1:A1")
            print("✅ Table 'admin_messages' already exists")
            return True
        except:
            pass
        
        # Create table with headers
        headers = [
            "id",
            "admin_user_id", 
            "user_message",
            "ai_response",
            "categories",
            "has_contact_info",
            "has_date",
            "has_price",
            "timestamp"
        ]
        
        print("📝 Creating 'admin_messages' table...")
        sc.append_row("admin_messages", headers)
        
        print("✅ Table created successfully!")
        print("\nColumns:")
        for i, h in enumerate(headers, 1):
            print(f"  {i}. {h}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_admin_messages_table()
    sys.exit(0 if success else 1)
