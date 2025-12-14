"""
PostgreSQL repository for bookings
"""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class BookingsRepoPG:
    """PostgreSQL-based bookings repository"""

    def __init__(self, db_engine):
        self.engine = db_engine

    def list_bookings(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all bookings with pagination"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, client_id, master_id, service_id, datetime_start, datetime_end,
                       status, price, comment_client, comment_master, source,
                       created_at, updated_at, google_event_id
                FROM bookings
                ORDER BY datetime_start DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})

            bookings = []
            for row in result:
                bookings.append({
                    "id": str(row[0]),
                    "client_id": str(row[1]) if row[1] else "",
                    "master_id": str(row[2]) if row[2] else "",
                    "service_id": str(row[3]) if row[3] else "",
                    "datetime_start": row[4].isoformat() if row[4] else "",
                    "datetime_end": row[5].isoformat() if row[5] else "",
                    "status": row[6] or "pending",
                    "price": float(row[7]) if row[7] else 0.0,
                    "comment_client": row[8] or "",
                    "comment_master": row[9] or "",
                    "source": row[10] or "telegram",
                    "created_at": row[11].isoformat() if row[11] else "",
                    "updated_at": row[12].isoformat() if row[12] else "",
                    "google_event_id": row[13] or ""
                })
            return bookings

    def create_booking(self, client_id: str, master_id: str, service_id: str,
                      datetime_start: datetime, datetime_end: datetime,
                      status: str = "pending", google_event_id: str = "") -> Dict:
        """Create a new booking"""
        booking_id = str(uuid.uuid4())

        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO bookings (id, client_id, master_id, service_id,
                                    datetime_start, datetime_end, status,
                                    google_event_id, created_at, updated_at)
                VALUES (:id, :client_id::uuid, :master_id::uuid, :service_id::uuid,
                        :datetime_start, :datetime_end, :status,
                        :google_event_id, :created_at, :updated_at)
            """), {
                "id": booking_id,
                "client_id": client_id,
                "master_id": master_id,
                "service_id": service_id,
                "datetime_start": datetime_start,
                "datetime_end": datetime_end,
                "status": status,
                "google_event_id": google_event_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            conn.commit()

        logger.info(f"Created booking {booking_id}")
        return {"id": booking_id}

    def get_booking_by_id(self, booking_id: str) -> Optional[Dict]:
        """Get booking by UUID"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, client_id, master_id, service_id, datetime_start, datetime_end,
                       status, price, comment_client, comment_master, source,
                       created_at, updated_at, google_event_id
                FROM bookings
                WHERE id = :booking_id::uuid
            """), {"booking_id": booking_id})

            row = result.fetchone()
            if not row:
                return None

            return {
                "id": str(row[0]),
                "client_id": str(row[1]) if row[1] else "",
                "master_id": str(row[2]) if row[2] else "",
                "service_id": str(row[3]) if row[3] else "",
                "datetime_start": row[4].isoformat() if row[4] else "",
                "datetime_end": row[5].isoformat() if row[5] else "",
                "status": row[6] or "pending",
                "price": float(row[7]) if row[7] else 0.0,
                "comment_client": row[8] or "",
                "comment_master": row[9] or "",
                "source": row[10] or "telegram",
                "created_at": row[11].isoformat() if row[11] else "",
                "updated_at": row[12].isoformat() if row[12] else "",
                "google_event_id": row[13] or ""
            }

    def get_bookings_by_client(self, client_id: str) -> List[Dict]:
        """Get all bookings for a specific client"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, client_id, master_id, service_id, datetime_start, datetime_end,
                       status, price, created_at, google_event_id
                FROM bookings
                WHERE client_id = :client_id::uuid
                ORDER BY datetime_start DESC
            """), {"client_id": client_id})

            bookings = []
            for row in result:
                bookings.append({
                    "id": str(row[0]),
                    "client_id": str(row[1]) if row[1] else "",
                    "master_id": str(row[2]) if row[2] else "",
                    "service_id": str(row[3]) if row[3] else "",
                    "datetime_start": row[4].isoformat() if row[4] else "",
                    "datetime_end": row[5].isoformat() if row[5] else "",
                    "status": row[6] or "pending",
                    "price": float(row[7]) if row[7] else 0.0,
                    "created_at": row[8].isoformat() if row[8] else "",
                    "google_event_id": row[9] or ""
                })
            return bookings

    def update_booking(self, booking_id: str, data: Dict) -> bool:
        """Update booking"""
        fields = []
        params = {"booking_id": booking_id, "updated_at": datetime.now(timezone.utc)}

        for field in ["status", "price", "comment_client", "comment_master", "google_event_id"]:
            if field in data:
                fields.append(f"{field} = :{field}")
                params[field] = data[field]

        if not fields:
            return False

        fields.append("updated_at = :updated_at")
        query = f"UPDATE bookings SET {', '.join(fields)} WHERE id = :booking_id::uuid"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            conn.commit()
            return result.rowcount > 0

    def cancel_booking(self, booking_id: str, reason: str = "") -> bool:
        """Cancel a booking"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE bookings
                SET status = 'cancelled',
                    comment_master = CONCAT(COALESCE(comment_master, ''), ' | Cancelled: ', :reason),
                    updated_at = :updated_at
                WHERE id = :booking_id::uuid
            """), {
                "booking_id": booking_id,
                "reason": reason,
                "updated_at": datetime.now(timezone.utc)
            })
            conn.commit()
            return result.rowcount > 0

    def delete_booking(self, booking_id: str) -> bool:
        """Hard delete booking"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                DELETE FROM bookings WHERE id = :booking_id::uuid
            """), {"booking_id": booking_id})
            conn.commit()
            return result.rowcount > 0
