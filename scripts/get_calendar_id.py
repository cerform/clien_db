#!/usr/bin/env python3
"""Get Google Calendar ID for the service account"""

import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_id():
    """Get the primary calendar ID for the service account"""
    
    # Try to get credentials from different sources
    creds_path = None
    
    # Check if running in Cloud Run
    if os.getenv("K_SERVICE"):
        print("Running in Cloud Run - using default credentials")
        from google.auth import default
        credentials, _ = default(scopes=SCOPES)
    else:
        # Local development - look for credentials.json
        possible_paths = [
            "credentials.json",
            "/app/credentials.json"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                creds_path = path
                break
        
        if not creds_path:
            print("❌ credentials.json not found!")
            print("Please place credentials.json in the project root")
            return
        
        print(f"Using credentials from: {creds_path}")
        credentials = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    
    try:
        # Build Calendar API
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get the primary calendar (which is the service account email)
        calendar = service.calendars().get(calendarId='primary').execute()
        
        calendar_id = calendar.get('id')
        print(f"\n✅ Google Calendar ID: {calendar_id}")
        print(f"   Summary: {calendar.get('summary', 'N/A')}")
        print(f"   Timezone: {calendar.get('timeZone', 'N/A')}")
        
        print("\n📝 Add this to your .env file:")
        print(f"   GOOGLE_CALENDAR_ID={calendar_id}")
        
        return calendar_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    get_calendar_id()
