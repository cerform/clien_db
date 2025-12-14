"""
PostgreSQL repository for calendar slots
"""
import uuid
from datetime import date, time, datetime
from typing import List, Dict, Optional
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class CalendarRepoPG:
    """PostgreSQL-based calendar repository"""

    def __init__(self, db_engine):
        self.engine = db_engine

    def get_available_slots(self, master_id: str, date_from: date, date_to: date) -> List[Dict]:
        """Get available slots for a master in date range"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, date, master_id, slot_start, slot_end, available, note
                FROM calendar
                WHERE master_id = :master_id::uuid
                  AND date BETWEEN :date_from AND :date_to
                  AND available = TRUE
                ORDER BY date, slot_start
            """), {
                "master_id": master_id,
                "date_from": date_from,
                "date_to": date_to
            })

            slots = []
            for row in result:
                slots.append({
                    "id": str(row[0]),
                    "date": row[1].isoformat(),
                    "master_id": str(row[2]) if row[2] else "",
                    "slot_start": str(row[3]),
                    "slot_end": str(row[4]),
                    "available": row[5],
                    "note": row[6] or ""
                })
            return slots

    def create_slot(self, master_id: str, slot_date: date, slot_start: time,
                   slot_end: time, available: bool = True, note: str = "") -> Dict:
        """Create a calendar slot"""
        slot_id = str(uuid.uuid4())

        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO calendar (id, date, master_id, slot_start, slot_end, available, note)
                VALUES (:id, :date, :master_id::uuid, :slot_start, :slot_end, :available, :note)
            """), {
                "id": slot_id,
                "date": slot_date,
                "master_id": master_id,
                "slot_start": slot_start,
                "slot_end": slot_end,
                "available": available,
                "note": note
            })
            conn.commit()

        logger.info(f"Created slot {slot_id} for master {master_id}")
        return {"id": slot_id}

    def mark_slot_unavailable(self, slot_id: str) -> bool:
        """Mark slot as unavailable"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE calendar SET available = FALSE WHERE id = :slot_id::uuid
            """), {"slot_id": slot_id})
            conn.commit()
            return result.rowcount > 0

    def mark_slot_available(self, slot_id: str) -> bool:
        """Mark slot as available"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE calendar SET available = TRUE WHERE id = :slot_id::uuid
            """), {"slot_id": slot_id})
            conn.commit()
            return result.rowcount > 0

    def delete_slot(self, slot_id: str) -> bool:
        """Delete calendar slot"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                DELETE FROM calendar WHERE id = :slot_id::uuid
            """), {"slot_id": slot_id})
            conn.commit()
            return result.rowcount > 0
