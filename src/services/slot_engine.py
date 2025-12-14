"""
Slot Engine service: calculate available slots based on calendar events and pending/confirmed bookings.
- Uses normalized `calendar_events` table and `bookings` / `bookings_pending`.
- Provides functions:
  - `get_available_slots(master_id, service_duration, start_range, end_range)`
  - `lock_slot` (atomically insert in slot_locks)
  - `create_pending_booking` (insert into bookings_pending, with TTL)

This service does not directly confirm bookings; it only creates pending_bookings.
"""

from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional

from src.db.db_client import get_db
from src.security.inka_acl import can_write as can_inka_write, can_read as can_inka_read

logger = logging.getLogger(__name__)

# A simple default: 2 minutes lock TTL, can be configured
DEFAULT_LOCK_TTL_SECONDS = 120


def _round_dt_to_minutes(dt: datetime, minute_step: int = 15) -> datetime:
    # Round down to nearest step
    new_minute = (dt.minute // minute_step) * minute_step
    return dt.replace(minute=new_minute, second=0, microsecond=0)


def get_available_slots(master_id: str, service_duration_min: int,
                        start_range: datetime, end_range: datetime, caller_role: str = '') -> List[Dict]:
    """Return available slots for a master between start_range and end_range
    Each slot is a dict with start, end, master_id.
    This implementation queries normalized calendar_events and excludes confirmed bookings and pending locks.
    """
    # Role check for read permission
    if caller_role and not can_inka_read(caller_role, 'availability_view'):
        logger.warning(f"get_available_slots forbidden for role {caller_role}")
        return []
    db = get_db()
    conn = db.get_connection()
    # Normalize in SQL using windowing and generate_series
    # For simplicity we implement a conservative algorithm here in Python

    cur = conn.cursor()

    # 1. Fetch all busy intervals from calendar_events for the master
    cur.execute(
        """
        SELECT ce.start_time, ce.end_time FROM calendar_events ce
        JOIN calendar_sources cs ON cs.id = ce.source_id
        WHERE cs.master_id = %s AND ce.status = 'busy'
        AND ce.end_time > %s AND ce.start_time < %s
        ORDER BY ce.start_time
        """, (master_id, start_range, end_range)
    )
    busy_intervals = cur.fetchall()

    # 2. Fetch bookings that block slots
    cur.execute(
        """
        SELECT b.start_time, b.end_time FROM bookings b
        WHERE b.master_id = %s
        AND b.status = 'confirmed'
        AND b.end_time > %s AND b.start_time < %s
        UNION
        SELECT p.start_time, p.end_time FROM bookings_pending p
        WHERE p.master_id = %s
        AND p.status = 'pending'
        AND p.expires_at > now() AND p.end_time > %s AND p.start_time < %s
        ORDER BY start_time
        """, (master_id, start_range, end_range, master_id, start_range, end_range)
    )
    blocked_intervals = cur.fetchall()

    # 3. Merge busy and blocked intervals
    merged = []
    for start, end in list(busy_intervals) + list(blocked_intervals):
        if not merged:
            merged.append((start, end))
        else:
            last_s, last_e = merged[-1]
            if start <= last_e:
                merged[-1] = (last_s, max(last_e, end))
            else:
                merged.append((start, end))

    # 4. Build a timeline of available intervals by subtracting merged from working range
    # For now we assume master working day is entire range; future: consider working hours table
    avail_intervals = []
    pointer = start_range
    for s, e in merged:
        if pointer < s:
            avail_intervals.append((pointer, s))
        pointer = max(pointer, e)
    if pointer < end_range:
        avail_intervals.append((pointer, end_range))

    # 5. Slice avail_intervals into slots by service_duration_min
    slots = []
    for a_start, a_end in avail_intervals:
        cur_start = _round_dt_to_minutes(a_start)
        while True:
            cur_end = cur_start + timedelta(minutes=service_duration_min)
            if cur_end > a_end:
                break
            slots.append({
                'slot_id': f"{master_id}-{cur_start.isoformat()}",
                'master_id': master_id,
                'start': cur_start,
                'end': cur_end
            })
            cur_start = cur_start + timedelta(minutes=service_duration_min)

    cur.close()
    return slots


def lock_slot(master_id: str, start: datetime, lock_holder: str, ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS, caller_role: str = '') -> bool:
    """Try to lock slot via atomic insert into slot_locks. Return True if succeeded."""
    db = get_db()
    conn = db.get_connection()
    cur = conn.cursor()
    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    # Role check: only booking agent may lock slots
    if caller_role and not can_inka_write(caller_role, 'slot_locks'):
        logger.warning(f"lock_slot forbidden for role {caller_role}")
        return False
    try:
        cur.execute(
            "INSERT INTO slot_locks (master_id, start_time, locked_by, locked_at, expires_at) VALUES (%s, %s, %s, now(), %s)",
            (master_id, start, lock_holder, expires_at)
        )
        conn.commit()
        cur.close()
        logger.info(f"Locked slot {master_id}@{start} by {lock_holder}")
        return True
    except Exception as e:
        conn.rollback()
        logger.debug(f"Failed to lock slot {master_id}@{start}: {e}")
        cur.close()
        return False


def create_pending_booking(user_id: int, master_id: str, service_id: str, start: datetime, end: datetime, lock_holder: str, ttl_seconds: int = 120, caller_role: str = '') -> Optional[str]:
    """Create a pending booking and return the pending_id on success.
    This does a lock + insert into bookings_pending.
    """
    db = get_db()
    conn = db.get_connection()
    cur = conn.cursor()

    # Permission check
    if caller_role and not can_inka_write(caller_role, 'bookings_pending'):
        logger.warning(f"create_pending_booking forbidden for role {caller_role}")
        return None
    # Lock first
    if not lock_slot(master_id, start, lock_holder, ttl_seconds, caller_role=caller_role):
        return None

    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    try:
        cur.execute(
            "INSERT INTO bookings_pending (user_id, master_id, service_id, start_time, end_time, status, expires_at, locked_by) VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s) RETURNING id",
            (user_id, master_id, service_id, start, end, expires_at, lock_holder)
        )
        pending_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return str(pending_id)
    except Exception as e:
        conn.rollback()
        logger.exception(f"Failed to create pending booking: {e}")
        cur.close()
        return None
