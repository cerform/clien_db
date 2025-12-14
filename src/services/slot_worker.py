"""
Slot worker: compute slots per master using `calendar_busy_intervals` and populate `calculated_slots`.
This worker is meant to run periodically (cron) or on-demand (changes in calendar events notification).
"""
from datetime import datetime, timedelta, timezone
import logging
from typing import List

from src.db.db_client import get_db_for_role, get_db
import os
from src.services.slot_engine import get_available_slots

logger = logging.getLogger(__name__)


def compute_and_upsert_slots(master_id: str, start: datetime, end: datetime, service_duration_min: int = 120):
    db = get_db_for_role('inka_booking_agent')
    conn = db.get_connection()
    cur = conn.cursor()

    slots = get_available_slots(master_id, service_duration_min, start, end, caller_role='inka_booking_agent')

    # Upsert slots into calculated_slots (replace existing intervals)
    # First remove existing slots for this master/time range
    cur.execute("DELETE FROM calculated_slots WHERE master_id = %s AND slot_start >= %s AND slot_start < %s", (master_id, start, end))

    for s in slots:
        cur.execute(
            "INSERT INTO calculated_slots (id, master_id, slot_start, slot_end, slot_id, is_available) VALUES (gen_random_uuid(), %s, %s, %s, %s, true)",
            (master_id, s['start'], s['end'], s['slot_id'])
        )
    conn.commit()
    cur.close()
    logger.info(f"Upserted {len(slots)} slots for master {master_id}")
    return len(slots)


def compute_slots_for_all_masters(start: datetime, end: datetime, duration: int = 120):
    db = get_db()
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT id FROM calendar_sources WHERE source_type = 'master' AND active = true")
    masters = [r[0] for r in cur.fetchall()]
    cur.close()

    total = 0
    for master_id in masters:
        total += compute_and_upsert_slots(master_id, start, end, service_duration_min=duration)
    return total


def refresh_availability_materialized_view():
    # Prefer DB for calendar sync role, else booking agent, else default
    if os.getenv('DATABASE_URL_CALENDAR_SYNC'):
        db = get_db_for_role('calendar_sync')
    elif os.getenv('DATABASE_URL_INKA_BOOKING_AGENT'):
        db = get_db_for_role('inka_booking_agent')
    else:
        db = get_db()
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY availability_view')
        conn.commit()
    except Exception:
        # Fallback to non-concurrent refresh if not supported
        conn.rollback()
        cur.execute('REFRESH MATERIALIZED VIEW availability_view')
        conn.commit()
    cur.close()
    logger.info('Refreshed materialized view availability_view')


if __name__ == '__main__':
    # Run daily for next 7 days
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=7)
    total = compute_slots_for_all_masters(now, until, duration=120)
    print(f"Computed {total} slots")
