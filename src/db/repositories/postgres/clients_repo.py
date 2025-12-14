"""
PostgreSQL repository for clients
Implements full CRUD operations with proper UUID support
"""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class ClientsRepoPG:
    """PostgreSQL-based clients repository"""

    def __init__(self, db_engine):
        """
        Initialize repository with SQLAlchemy engine

        Args:
            db_engine: SQLAlchemy engine instance
        """
        self.engine = db_engine

    def list_clients(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all clients with pagination"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, telegram_id, name, phone, email, notes, tags,
                       created_at, last_visit, language, preferences
                FROM clients
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})

            clients = []
            for row in result:
                clients.append({
                    "id": str(row[0]),
                    "telegram_id": row[1],
                    "name": row[2],
                    "phone": row[3] or "",
                    "email": row[4] or "",
                    "notes": row[5] or "",
                    "tags": row[6] or "",
                    "created_at": row[7].isoformat() if row[7] else "",
                    "last_visit": row[8].isoformat() if row[8] else "",
                    "language": row[9] or "ru",
                    "preferences": row[10] or {}
                })

            return clients

    def create_client(self, telegram_id: int, name: str, phone: str = "",
                     email: str = "", notes: str = "", language: str = "ru") -> Dict:
        """Create a new client"""
        client_id = str(uuid.uuid4())

        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO clients (id, telegram_id, name, phone, email, notes, language, created_at)
                VALUES (:id, :telegram_id, :name, :phone, :email, :notes, :language, :created_at)
            """), {
                "id": client_id,
                "telegram_id": telegram_id,
                "name": name,
                "phone": phone,
                "email": email,
                "notes": notes,
                "language": language,
                "created_at": datetime.now(timezone.utc)
            })
            conn.commit()

        logger.info(f"Created client {client_id} for telegram_id {telegram_id}")
        return {
            "id": client_id,
            "telegram_id": telegram_id,
            "name": name,
            "phone": phone,
            "email": email,
            "language": language
        }

    def get_client_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Get client by Telegram ID"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, telegram_id, name, phone, email, notes, tags,
                       created_at, last_visit, language, preferences
                FROM clients
                WHERE telegram_id = :telegram_id
            """), {"telegram_id": telegram_id})

            row = result.fetchone()
            if not row:
                return None

            return {
                "id": str(row[0]),
                "telegram_id": row[1],
                "name": row[2],
                "phone": row[3] or "",
                "email": row[4] or "",
                "notes": row[5] or "",
                "tags": row[6] or "",
                "created_at": row[7].isoformat() if row[7] else "",
                "last_visit": row[8].isoformat() if row[8] else "",
                "language": row[9] or "ru",
                "preferences": row[10] or {}
            }

    def get_client_by_id(self, client_id: str) -> Optional[Dict]:
        """Get client by UUID"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, telegram_id, name, phone, email, notes, tags,
                       created_at, last_visit, language, preferences
                FROM clients
                WHERE id = :client_id::uuid
            """), {"client_id": client_id})

            row = result.fetchone()
            if not row:
                return None

            return {
                "id": str(row[0]),
                "telegram_id": row[1],
                "name": row[2],
                "phone": row[3] or "",
                "email": row[4] or "",
                "notes": row[5] or "",
                "tags": row[6] or "",
                "created_at": row[7].isoformat() if row[7] else "",
                "last_visit": row[8].isoformat() if row[8] else "",
                "language": row[9] or "ru",
                "preferences": row[10] or {}
            }

    def update_client(self, client_id: str, data: Dict) -> bool:
        """Update client by UUID"""
        # Build dynamic UPDATE query based on provided fields
        fields = []
        params = {"client_id": client_id}

        if "name" in data:
            fields.append("name = :name")
            params["name"] = data["name"]
        if "phone" in data:
            fields.append("phone = :phone")
            params["phone"] = data["phone"]
        if "email" in data:
            fields.append("email = :email")
            params["email"] = data["email"]
        if "notes" in data:
            fields.append("notes = :notes")
            params["notes"] = data["notes"]
        if "tags" in data:
            fields.append("tags = :tags")
            params["tags"] = data["tags"]
        if "language" in data:
            fields.append("language = :language")
            params["language"] = data["language"]
        if "preferences" in data:
            fields.append("preferences = :preferences::jsonb")
            import json
            params["preferences"] = json.dumps(data["preferences"])

        if not fields:
            return False

        query = f"UPDATE clients SET {', '.join(fields)} WHERE id = :client_id::uuid"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            conn.commit()
            return result.rowcount > 0

    def update_last_interaction(self, telegram_id: int) -> bool:
        """Update last interaction timestamp"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE clients
                SET last_visit = :now
                WHERE telegram_id = :telegram_id
            """), {
                "telegram_id": telegram_id,
                "now": datetime.now(timezone.utc)
            })
            conn.commit()
            return result.rowcount > 0

    def delete_client(self, client_id: str) -> bool:
        """Delete client by UUID (hard delete)"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                DELETE FROM clients WHERE id = :client_id::uuid
            """), {"client_id": client_id})
            conn.commit()
            return result.rowcount > 0

    def count_clients(self) -> int:
        """Get total count of clients"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM clients"))
            return result.scalar()
