"""
PostgreSQL repository for masters
"""
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class MastersRepoPG:
    """PostgreSQL-based masters repository"""

    def __init__(self, db_engine):
        self.engine = db_engine

    def list_masters(self, active_only: bool = True) -> List[Dict]:
        """Get all masters"""
        query = """
            SELECT id, name, specialization, rating, experience_years,
                   instagram, status, telegram_id, calendar_id, notes,
                   phone, email, created_at
            FROM masters
        """
        if active_only:
            query += " WHERE status = 'active'"
        query += " ORDER BY name"

        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            masters = []
            for row in result:
                masters.append({
                    "id": str(row[0]),
                    "name": row[1],
                    "specialization": row[2] or "",
                    "rating": float(row[3]) if row[3] else 0.0,
                    "experience_years": row[4] or 0,
                    "instagram": row[5] or "",
                    "status": row[6] or "active",
                    "telegram_id": row[7],
                    "calendar_id": row[8] or "",
                    "notes": row[9] or "",
                    "phone": row[10] or "",
                    "email": row[11] or "",
                    "created_at": row[12].isoformat() if row[12] else ""
                })
            return masters

    def create_master(self, name: str, calendar_id: str = "", specialization: str = "",
                     telegram_id: Optional[int] = None, status: str = "active") -> Dict:
        """Create a new master"""
        master_id = str(uuid.uuid4())

        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO masters (id, name, specialization, calendar_id, status, telegram_id, created_at)
                VALUES (:id, :name, :specialization, :calendar_id, :status, :telegram_id, :created_at)
            """), {
                "id": master_id,
                "name": name,
                "specialization": specialization,
                "calendar_id": calendar_id,
                "status": status,
                "telegram_id": telegram_id,
                "created_at": datetime.utcnow()
            })
            conn.commit()

        logger.info(f"Created master {master_id}: {name}")
        return {"id": master_id, "name": name, "calendar_id": calendar_id}

    def get_master_by_id(self, master_id: str) -> Optional[Dict]:
        """Get master by UUID"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, specialization, rating, experience_years,
                       instagram, status, telegram_id, calendar_id, notes,
                       phone, email, created_at
                FROM masters
                WHERE id = :master_id::uuid
            """), {"master_id": master_id})

            row = result.fetchone()
            if not row:
                return None

            return {
                "id": str(row[0]),
                "name": row[1],
                "specialization": row[2] or "",
                "rating": float(row[3]) if row[3] else 0.0,
                "experience_years": row[4] or 0,
                "instagram": row[5] or "",
                "status": row[6] or "active",
                "telegram_id": row[7],
                "calendar_id": row[8] or "",
                "notes": row[9] or "",
                "phone": row[10] or "",
                "email": row[11] or "",
                "created_at": row[12].isoformat() if row[12] else ""
            }

    def update_master(self, master_id: str, data: Dict) -> bool:
        """Update master by UUID"""
        fields = []
        params = {"master_id": master_id}

        for field in ["name", "specialization", "rating", "experience_years",
                     "instagram", "status", "telegram_id", "calendar_id",
                     "notes", "phone", "email"]:
            if field in data:
                fields.append(f"{field} = :{field}")
                params[field] = data[field]

        if not fields:
            return False

        query = f"UPDATE masters SET {', '.join(fields)} WHERE id = :master_id::uuid"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            conn.commit()
            return result.rowcount > 0

    def update_master_calendar(self, master_id: str, calendar_id: str) -> bool:
        """Update the calendar_id for a master"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE masters
                SET calendar_id = :calendar_id
                WHERE id = :master_id::uuid
            """), {
                "master_id": master_id,
                "calendar_id": calendar_id
            })
            conn.commit()
            return result.rowcount > 0

    def delete_master(self, master_id: str) -> bool:
        """Soft delete - mark as inactive"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE masters SET status = 'inactive' WHERE id = :master_id::uuid
            """), {"master_id": master_id})
            conn.commit()
            return result.rowcount > 0

    def get_masters_with_calendar(self) -> List[Dict]:
        """Get all masters that have calendar_id set"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, calendar_id, status
                FROM masters
                WHERE calendar_id IS NOT NULL AND calendar_id != ''
                AND status = 'active'
            """))

            masters = []
            for row in result:
                masters.append({
                    "id": str(row[0]),
                    "name": row[1],
                    "calendar_id": row[2],
                    "status": row[3]
                })
            return masters
