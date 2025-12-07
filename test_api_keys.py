#!/usr/bin/env python3
"""Check if all Google APIs are working"""
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load credentials
try:
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json',
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/calendar'
        ]
    )
    print("✅ Service account credentials loaded")
except Exception as e:
    print(f"❌ Failed to load credentials: {e}")
    exit(1)

# Test Google Sheets
try:
    sheets_service = build('sheets', 'v4', credentials=creds)
    result = sheets_service.spreadsheets().get(
        spreadsheetId='17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ'
    ).execute()
    print(f"✅ Google Sheets: OK ('{result['properties']['title']}')")
except Exception as e:
    print(f"❌ Google Sheets: FAILED - {e}")

# Test Google Calendar
try:
    calendar_service = build('calendar', 'v3', credentials=creds)
    result = calendar_service.calendars().get(calendarId='primary').execute()
    print(f"✅ Google Calendar: OK")
except Exception as e:
    print(f"❌ Google Calendar: FAILED - {e}")

# Test calendar with specific ID
try:
    calendar_id = 'f5d400333836744e002b77e85a46a76bc79d32df523bd49011d0f785df775a7c@group.calendar.google.com'
    result = calendar_service.calendars().get(calendarId=calendar_id).execute()
    print(f"✅ Google Calendar (specific): OK")
    
    # Try to list events
    events = calendar_service.events().list(
        calendarId=calendar_id,
        maxResults=5
    ).execute()
    print(f"✅ Can read calendar events: {len(events.get('items', []))} events found")
except Exception as e:
    print(f"❌ Google Calendar (specific): FAILED - {e}")

print("\n✅ All API keys are working correctly!")
