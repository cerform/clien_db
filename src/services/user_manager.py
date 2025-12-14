"""
User Manager for creating and managing users (Masters, Admins, Super Admins).
Handles authentication, role assignment, and password management.
"""

import os
import secrets
import hashlib
from typing import Dict, Optional, List
from datetime import datetime, timezone

from src.db.cloudsql_client import CloudSQLClient
from src.auth.roles import Role, Permission, has_permission


class UserManager:
    """Manages user creation, authentication, and role management."""

    def __init__(self):
        """Initialize UserManager with CloudSQL client."""
        self.sql_client = CloudSQLClient()

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def _generate_username(self, name: str) -> str:
        """Generate username from name (lowercase, spaces to underscores)."""
        if not name:
            raise ValueError("Name is required to generate username")

        username = name.lower().strip()
        username = username.replace(" ", "_")
        username = ''.join(c for c in username if c.isalnum() or c == '_')

        # Check if username exists, append number if needed
        counter = 1
        original_username = username
        while self._username_exists(username):
            username = f"{original_username}{counter}"
            counter += 1

        return username

    def _username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        result = self.sql_client.execute_query(
            "SELECT COUNT(*) as count FROM masters WHERE username = %s",
            (username,)
        )
        return result and result[0]['count'] > 0

    def _generate_master_id(self) -> str:
        """Generate unique master ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def create_master(
        self,
        name: str,
        phone: str,
        telegram_id: Optional[str] = None,
        role: Role = Role.MASTER,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict:
        """
        Create a new user (master, admin, or super admin).

        Args:
            name: Full name
            phone: Phone number
            telegram_id: Telegram ID (required for super_admin)
            role: User role (default: MASTER)
            username: Username for web access (auto-generated if not provided)
            password: Password for web access (auto-generated if not provided)

        Returns:
            Dict with success status, username, and password (plain text, shown only once)
        """
        try:
            # Validate inputs
            if not name or not phone:
                return {
                    "success": False,
                    "message": "Имя и телефон обязательны"
                }

            if role == Role.SUPER_ADMIN and not telegram_id:
                return {
                    "success": False,
                    "message": "Telegram ID обязателен для СуперАдмина"
                }

            # Generate username if not provided
            if not username:
                username = self._generate_username(name)

            # Generate secure password if not provided
            if not password:
                password = secrets.token_urlsafe(12)

            # Hash password
            password_hash = self._hash_password(password)

            # Generate master ID
            master_id = self._generate_master_id()

            # Insert into database
            query = """
                INSERT INTO masters (
                    id, name, phone, telegram_id, role, username, password_hash,
                    is_active, calendar_link, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id, name, username, role
            """

            calendar_link = f"https://example.com/calendar/{master_id}"  # Placeholder

            result = self.sql_client.execute_query(
                query,
                (
                    master_id,
                    name,
                    phone,
                    telegram_id,
                    role.value,
                    username,
                    password_hash,
                    True,  # is_active
                    calendar_link,
                    datetime.now(timezone.utc)
                )
            )

            if result:
                role_names = {
                    Role.SUPER_ADMIN: "СуперАдмин",
                    Role.ADMIN: "Админ",
                    Role.MASTER: "Мастер"
                }

                return {
                    "success": True,
                    "master_id": master_id,
                    "username": username,
                    "password": password,  # Plain text, shown only once!
                    "message": f"✅ {role_names.get(role, 'Пользователь')} '{name}' создан успешно!\n"
                              f"Username: {username}\n"
                              f"Password: {password}\n"
                              f"⚠️ Сохраните пароль - он больше не будет показан!"
                }
            else:
                return {
                    "success": False,
                    "message": "Ошибка при создании пользователя"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка: {str(e)}"
            }

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user by username and password.

        Returns:
            User data if authenticated, None otherwise
        """
        try:
            password_hash = self._hash_password(password)

            query = """
                SELECT id, name, phone, telegram_id, role, username, is_active
                FROM masters
                WHERE username = %s AND password_hash = %s AND is_active = TRUE
            """

            result = self.sql_client.execute_query(query, (username, password_hash))

            if result and len(result) > 0:
                return result[0]
            else:
                return None

        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    def get_user_by_telegram_id(self, telegram_id: str) -> Optional[Dict]:
        """Get user by Telegram ID."""
        try:
            query = """
                SELECT id, name, phone, telegram_id, role, username, is_active
                FROM masters
                WHERE telegram_id = %s AND is_active = TRUE
            """

            result = self.sql_client.execute_query(query, (telegram_id,))

            if result and len(result) > 0:
                return result[0]
            else:
                return None

        except Exception as e:
            print(f"Error getting user by telegram_id: {e}")
            return None

    def get_user_by_id(self, master_id: str) -> Optional[Dict]:
        """Get user by ID."""
        try:
            query = """
                SELECT id, name, phone, telegram_id, role, username, is_active
                FROM masters
                WHERE id = %s
            """

            result = self.sql_client.execute_query(query, (master_id,))

            if result and len(result) > 0:
                return result[0]
            else:
                return None

        except Exception as e:
            print(f"Error getting user by id: {e}")
            return None

    def list_all_users(self) -> List[Dict]:
        """List all users."""
        try:
            query = """
                SELECT id, name, phone, telegram_id, role, username, is_active, created_at
                FROM masters
                ORDER BY role, name
            """

            result = self.sql_client.execute_query(query)
            return result if result else []

        except Exception as e:
            print(f"Error listing users: {e}")
            return []

    def update_role(self, master_id: str, new_role: Role) -> Dict:
        """Update user role."""
        try:
            query = """
                UPDATE masters
                SET role = %s
                WHERE id = %s
                RETURNING id, name, role
            """

            result = self.sql_client.execute_query(query, (new_role.value, master_id))

            if result:
                return {
                    "success": True,
                    "message": f"✅ Роль пользователя обновлена на {new_role.value}"
                }
            else:
                return {
                    "success": False,
                    "message": "Пользователь не найден"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка: {str(e)}"
            }

    def change_password(self, master_id: str, new_password: str) -> Dict:
        """Change user password."""
        try:
            password_hash = self._hash_password(new_password)

            query = """
                UPDATE masters
                SET password_hash = %s
                WHERE id = %s
                RETURNING id, name
            """

            result = self.sql_client.execute_query(query, (password_hash, master_id))

            if result:
                return {
                    "success": True,
                    "message": "✅ Пароль успешно изменен"
                }
            else:
                return {
                    "success": False,
                    "message": "Пользователь не найден"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка: {str(e)}"
            }

    def deactivate_user(self, master_id: str) -> Dict:
        """Deactivate (fire) a user."""
        try:
            query = """
                UPDATE masters
                SET is_active = FALSE
                WHERE id = %s
                RETURNING id, name
            """

            result = self.sql_client.execute_query(query, (master_id,))

            if result:
                return {
                    "success": True,
                    "message": f"✅ Пользователь '{result[0]['name']}' уволен (деактивирован)"
                }
            else:
                return {
                    "success": False,
                    "message": "Пользователь не найден"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка: {str(e)}"
            }

    def activate_user(self, master_id: str) -> Dict:
        """Activate (hire back) a user."""
        try:
            query = """
                UPDATE masters
                SET is_active = TRUE
                WHERE id = %s
                RETURNING id, name
            """

            result = self.sql_client.execute_query(query, (master_id,))

            if result:
                return {
                    "success": True,
                    "message": f"✅ Пользователь '{result[0]['name']}' нанят обратно (активирован)"
                }
            else:
                return {
                    "success": False,
                    "message": "Пользователь не найден"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка: {str(e)}"
            }
