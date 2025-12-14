"""
Calendar sync worker: syncs Google Calendar events into `calendar_events` table
- Supports run-once (cron) and webhook-driven syncing
- Normalizes events to only store start/end and metadata
"""
import logging
import os
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from src.db.db_client import get_db, get_db_for_role
#from googleapiclient.discovery import build
#from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


def sync_calendar_source(calendar_id: str, source_type: str, source_db_id: int, from_ts: datetime, to_ts: datetime) -> int:
    """Sync a single calendar into `calendar_events`. Returns count of events synced."""
    # Placeholder: The real implementation uses Google API to fetch events
    # and writes/updates them in calendar_events table.
    db = get_db_for_role('calendar_sync') if os.getenv('DATABASE_URL_CALENDAR_SYNC') else get_db()
    conn = db.get_connection()
    cur = conn.cursor()

    # TODO: fetch events via Google API
    events = []  # List[dict] with start, end, external_event_id

    # Upsert logic: update last_synced_at and create missing event records
    count = 0
    for ev in events:
        try:
            cur.execute(
                "INSERT INTO calendar_events (source_id, start_time, end_time, status, external_event_id, last_synced_at) VALUES (%s, %s, %s, 'busy', %s, now()) ON CONFLICT (source_id, external_event_id) DO UPDATE SET start_time = EXCLUDED.start_time, end_time = EXCLUDED.end_time, last_synced_at = EXCLUDED.last_synced_at",
                (source_db_id, ev['start'], ev['end'], ev['id'])
            )
            count += 1
        except Exception as e:
            logger.debug(f"Failed to upsert event {ev}: {e}")
            continue
    conn.commit()
    cur.close()
    logger.info(f"Synced {count} events for {calendar_id}")
    return count


def webhook_notify_calendar_change(calendar_id: str):
    """Shortcut for webhooks: called by /api/webhooks/calendar_change to sync events for a calendar.
    This will find the calendar_sources row and call sync_calendar_source for recent range.
    """
    db = get_db_for_role('calendar_sync') if os.getenv('DATABASE_URL_CALENDAR_SYNC') else get_db()
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, calendar_id, source_type FROM calendar_sources WHERE calendar_id = %s", (calendar_id,))
    rows = cur.fetchall()
    cur.close()
    total = 0
    now = datetime.now(timezone.utc)
    try:
        for rid, cid, source_type in rows:
            # sync last 7 days for safety
            total += sync_calendar_source(cid, source_type, rid, now - timedelta(days=7), now + timedelta(days=30))
    except Exception as e:
        logger.exception(f"Webhook sync failed for calendar {calendar_id}: {e}")
    return total


def sync_all_calendars(from_ts: datetime, to_ts: datetime) -> int:
    """Sync all calendar sources into DB"""
    db = get_db()
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, calendar_id, source_type FROM calendar_sources WHERE active = true")
    rows = cur.fetchall()
    total = 0
    for rid, calendar_id, source_type in rows:
        total += sync_calendar_source(calendar_id, source_type, rid, from_ts, to_ts)
    cur.close()
    return total
