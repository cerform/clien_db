"""
Repository for admin_messages stored in Cloud SQL
Handles CRUD operations for admin chat messages
"""
import sqlalchemy
from sqlalchemy import text
from datetime import datetime
from typing import List, Optional, Dict
import json


class AdminMessagesRepo:
    """Repository for admin messages in Cloud SQL"""

    def __init__(self, db_engine):
        """
        Initialize repository with SQLAlchemy engine

        Args:
            db_engine: SQLAlchemy engine connected to Cloud SQL
        """
        self.engine = db_engine
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Create admin_messages table if it doesn't exist"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS admin_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp VARCHAR(32),
                    user_id VARCHAR(32),
                    username VARCHAR(64),
                    message TEXT,
                    category VARCHAR(64),
                    data JSON,
                    inka_category VARCHAR(64),
                    sheet_row INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_user_id (user_id),
                    INDEX idx_category (category)
                )
            """))
            conn.commit()

    def save_message(self, message: Dict) -> int:
        """
        Save admin message to Cloud SQL

        Args:
            message: dict with keys: timestamp, user_id, username, message,
                    category, data, inka_category

        Returns:
            int: ID of inserted message
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO admin_messages
                (timestamp, user_id, username, message, category, data, inka_category, sheet_row)
                VALUES (:timestamp, :user_id, :username, :message, :category, :data, :inka_category, :sheet_row)
            """), {
                "timestamp": message.get("timestamp", datetime.now().isoformat()),
                "user_id": message.get("user_id", ""),
                "username": message.get("username", ""),
                "message": message.get("message", ""),
                "category": message.get("category", "Other"),
                "data": json.dumps(message.get("data", {})),
                "inka_category": message.get("inka_category", ""),
                "sheet_row": message.get("sheet_row", 0)
            })
            conn.commit()
            return result.lastrowid

    def get_messages(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get admin messages with pagination

        Args:
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of message dicts
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, timestamp, user_id, username, message, category,
                       data, inka_category, sheet_row, created_at
                FROM admin_messages
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})

            messages = []
            for row in result:
                msg = {
                    "id": row[0],
                    "timestamp": row[1],
                    "user_id": row[2],
                    "username": row[3],
                    "message": row[4],
                    "category": row[5],
                    "data": json.loads(row[6]) if row[6] else {},
                    "inka_category": row[7],
                    "sheet_row": row[8],
                    "created_at": row[9].isoformat() if row[9] else None
                }
                messages.append(msg)

            return messages

    def get_messages_by_user(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get messages for specific user

        Args:
            user_id: User ID to filter by
            limit: Maximum number of messages

        Returns:
            List of message dicts
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, timestamp, user_id, username, message, category,
                       data, inka_category, sheet_row, created_at
                FROM admin_messages
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"user_id": user_id, "limit": limit})

            messages = []
            for row in result:
                msg = {
                    "id": row[0],
                    "timestamp": row[1],
                    "user_id": row[2],
                    "username": row[3],
                    "message": row[4],
                    "category": row[5],
                    "data": json.loads(row[6]) if row[6] else {},
                    "inka_category": row[7],
                    "sheet_row": row[8],
                    "created_at": row[9].isoformat() if row[9] else None
                }
                messages.append(msg)

            return messages

    def get_messages_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """Get messages by category"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, timestamp, user_id, username, message, category,
                       data, inka_category, sheet_row, created_at
                FROM admin_messages
                WHERE category = :category
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"category": category, "limit": limit})

            messages = []
            for row in result:
                msg = {
                    "id": row[0],
                    "timestamp": row[1],
                    "user_id": row[2],
                    "username": row[3],
                    "message": row[4],
                    "category": row[5],
                    "data": json.loads(row[6]) if row[6] else {},
                    "inka_category": row[7],
                    "sheet_row": row[8],
                    "created_at": row[9].isoformat() if row[9] else None
                }
                messages.append(msg)

            return messages

    def delete_old_messages(self, months: int = 12) -> int:
        """
        Delete messages older than N months

        Args:
            months: Number of months to keep (default: 12)

        Returns:
            Number of deleted messages
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                DELETE FROM admin_messages
                WHERE created_at < DATE_SUB(NOW(), INTERVAL :months MONTH)
            """), {"months": months})
            conn.commit()
            return result.rowcount

    def redact_pii(self, message_id: int) -> bool:
        """
        Redact PII fields for specific message

        Args:
            message_id: ID of message to redact

        Returns:
            True if successful
        """
        with self.engine.connect() as conn:
            conn.execute(text("""
                UPDATE admin_messages
                SET user_id = NULL, username = '[REDACTED]', message = '[REDACTED]'
                WHERE id = :message_id
            """), {"message_id": message_id})
            conn.commit()
            return True

    def redact_pii_by_user(self, user_id: str) -> int:
        """
        Redact all PII for specific user

        Args:
            user_id: User ID to redact

        Returns:
            Number of messages redacted
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE admin_messages
                SET user_id = NULL, username = '[REDACTED]', message = '[REDACTED]'
                WHERE user_id = :user_id
            """), {"user_id": user_id})
            conn.commit()
            return result.rowcount

    def count_messages(self) -> int:
        """Get total count of messages"""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM admin_messages"))
            return result.scalar()

    def get_categories_stats(self) -> List[Dict]:
        """Get message count by category"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT category, COUNT(*) as count
                FROM admin_messages
                GROUP BY category
                ORDER BY count DESC
            """))

            stats = []
            for row in result:
                stats.append({"category": row[0], "count": row[1]})

            return stats
