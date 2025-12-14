"""
PostgreSQL repository for services
"""
import uuid
from typing import List, Dict, Optional
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class ServicesRepoPG:
    """PostgreSQL-based services repository"""

    def __init__(self, db_engine):
        self.engine = db_engine

    def list_services(self, active_only: bool = True) -> List[Dict]:
        """Get all services"""
        query = """
            SELECT id, name, description, duration_min, price_from, price_to, category, active
            FROM services
        """
        if active_only:
            query += " WHERE active = TRUE"
        query += " ORDER BY category, name"

        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            services = []
            for row in result:
                services.append({
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2] or "",
                    "duration_min": row[3] or 0,
                    "price_from": float(row[4]) if row[4] else 0.0,
                    "price_to": float(row[5]) if row[5] else 0.0,
                    "category": row[6] or "",
                    "active": row[7]
                })
            return services

    def get_service_by_id(self, service_id: str) -> Optional[Dict]:
        """Get service by UUID"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, description, duration_min, price_from, price_to, category, active
                FROM services
                WHERE id = :service_id::uuid
            """), {"service_id": service_id})

            row = result.fetchone()
            if not row:
                return None

            return {
                "id": str(row[0]),
                "name": row[1],
                "description": row[2] or "",
                "duration_min": row[3] or 0,
                "price_from": float(row[4]) if row[4] else 0.0,
                "price_to": float(row[5]) if row[5] else 0.0,
                "category": row[6] or "",
                "active": row[7]
            }

    def create_service(self, name: str, description: str = "", duration_min: int = 60,
                      price_from: float = 0.0, price_to: float = 0.0,
                      category: str = "", active: bool = True) -> Dict:
        """Create a new service"""
        service_id = str(uuid.uuid4())

        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO services (id, name, description, duration_min,
                                    price_from, price_to, category, active)
                VALUES (:id, :name, :description, :duration_min,
                        :price_from, :price_to, :category, :active)
            """), {
                "id": service_id,
                "name": name,
                "description": description,
                "duration_min": duration_min,
                "price_from": price_from,
                "price_to": price_to,
                "category": category,
                "active": active
            })
            conn.commit()

        logger.info(f"Created service {service_id}: {name}")
        return {"id": service_id, "name": name}

    def update_service(self, service_id: str, data: Dict) -> bool:
        """Update service"""
        fields = []
        params = {"service_id": service_id}

        for field in ["name", "description", "duration_min", "price_from",
                     "price_to", "category", "active"]:
            if field in data:
                fields.append(f"{field} = :{field}")
                params[field] = data[field]

        if not fields:
            return False

        query = f"UPDATE services SET {', '.join(fields)} WHERE id = :service_id::uuid"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            conn.commit()
            return result.rowcount > 0

    def delete_service(self, service_id: str) -> bool:
        """Soft delete - mark as inactive"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE services SET active = FALSE WHERE id = :service_id::uuid
            """), {"service_id": service_id})
            conn.commit()
            return result.rowcount > 0
