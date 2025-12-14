#!/usr/bin/env python3
"""
Run calendar sync to normalize events in the DB.
Usage: PYTHONPATH=$PWD python3 scripts/sync_calendars.py
"""
from datetime import datetime, timedelta, timezone
from src.services.calendar_sync import sync_all_calendars

if __name__ == '__main__':
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=7)
    count = sync_all_calendars(now, until)
    print(f"Synced {count} events from calendars")
