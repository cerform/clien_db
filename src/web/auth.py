"""Authentication module for web interface"""

import hashlib
import os
import json
import uuid
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# File to store admin users (in production, use a database)
ADMINS_FILE = Path(__file__).parent.parent.parent / "data" / "admins.json"


def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = os.getenv('ADMIN_PASSWORD_SALT', 'default_salt_change_in_production')
    return hashlib.sha256((password + salt).encode()).hexdigest()


def _ensure_data_dir():
    """Ensure data directory exists"""
    data_dir = ADMINS_FILE.parent
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)


def _load_admins() -> List[Dict[str, Any]]:
    """Load admin users from file"""
    _ensure_data_dir()
    
    if ADMINS_FILE.exists():
        try:
            with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading admins: {e}")
    
    # Return default admin if file doesn't exist
    default_password = os.getenv('ADMIN_WEB_PASSWORD', 'admin123')
    default_admin = {
        "id": "admin_default",
        "username": "admin",
        "password_hash": hash_password(default_password),
        "role": "superadmin",
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "telegram_id": None,
        "is_active": True
    }
    
    # Save default admin
    _save_admins([default_admin])
    return [default_admin]


def _save_admins(admins: List[Dict[str, Any]]) -> bool:
    """Save admin users to file"""
    _ensure_data_dir()
    
    try:
        with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
            json.dump(admins, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving admins: {e}")
        return False


def get_admin_users() -> List[Dict[str, Any]]:
    """Get all admin users"""
    return _load_admins()


def add_admin_user(username: str, password: str, role: str = "admin", 
                   telegram_id: Optional[str] = None) -> Tuple[bool, str]:
    """Add new admin user"""
    admins = _load_admins()
    
    # Check if username exists
    if any(a["username"].lower() == username.lower() for a in admins):
        return False, f"Пользователь '{username}' уже существует"
    
    new_admin = {
        "id": f"admin_{uuid.uuid4().hex[:8]}",
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "telegram_id": telegram_id,
        "is_active": True
    }
    
    admins.append(new_admin)
    
    if _save_admins(admins):
        return True, f"Админ '{username}' создан"
    return False, "Ошибка сохранения"


def update_admin_user(admin_id: str, data: Dict[str, Any]) -> Tuple[bool, str]:
    """Update admin user"""
    admins = _load_admins()
    
    for i, admin in enumerate(admins):
        if admin["id"] == admin_id:
            # Update allowed fields
            if "username" in data:
                # Check if new username already exists
                new_username = data["username"].strip()
                if any(a["username"].lower() == new_username.lower() and a["id"] != admin_id for a in admins):
                    return False, f"Пользователь '{new_username}' уже существует"
                admins[i]["username"] = new_username
            
            if "role" in data:
                admins[i]["role"] = data["role"]
            
            if "telegram_id" in data:
                admins[i]["telegram_id"] = data["telegram_id"]
            
            if "is_active" in data:
                admins[i]["is_active"] = data["is_active"]
            
            if _save_admins(admins):
                return True, "Админ обновлен"
            return False, "Ошибка сохранения"
    
    return False, "Админ не найден"


def delete_admin_user(admin_id: str) -> Tuple[bool, str]:
    """Delete admin user"""
    admins = _load_admins()
    
    # Prevent deleting the last superadmin
    superadmins = [a for a in admins if a.get("role") == "superadmin" and a.get("is_active", True)]
    admin_to_delete = next((a for a in admins if a["id"] == admin_id), None)
    
    if not admin_to_delete:
        return False, "Админ не найден"
    
    if admin_to_delete.get("role") == "superadmin" and len(superadmins) <= 1:
        return False, "Нельзя удалить последнего суперадмина"
    
    admins = [a for a in admins if a["id"] != admin_id]
    
    if _save_admins(admins):
        return True, "Админ удален"
    return False, "Ошибка сохранения"


def change_admin_password(admin_id: str, new_password: str, 
                          current_password: Optional[str] = None) -> Tuple[bool, str]:
    """Change admin password"""
    admins = _load_admins()
    
    for i, admin in enumerate(admins):
        if admin["id"] == admin_id:
            # If current password provided, verify it
            if current_password:
                if admin["password_hash"] != hash_password(current_password):
                    return False, "Неверный текущий пароль"
            
            admins[i]["password_hash"] = hash_password(new_password)
            
            if _save_admins(admins):
                return True, "Пароль изменен"
            return False, "Ошибка сохранения"
    
    return False, "Админ не найден"


def toggle_admin_status(admin_id: str) -> Tuple[bool, str, bool]:
    """Toggle admin active status"""
    admins = _load_admins()
    
    for i, admin in enumerate(admins):
        if admin["id"] == admin_id:
            # Prevent deactivating the last superadmin
            if admin.get("is_active", True) and admin.get("role") == "superadmin":
                active_superadmins = [a for a in admins if a.get("role") == "superadmin" and a.get("is_active", True)]
                if len(active_superadmins) <= 1:
                    return False, "Нельзя деактивировать последнего суперадмина", True
            
            new_status = not admin.get("is_active", True)
            admins[i]["is_active"] = new_status
            
            if _save_admins(admins):
                status_text = "активирован" if new_status else "деактивирован"
                return True, f"Админ {status_text}", new_status
            return False, "Ошибка сохранения", admin.get("is_active", True)
    
    return False, "Админ не найден", False


def check_admin_password(provided_password: str, stored_hash: Optional[str] = None) -> bool:
    """Check if provided password matches any admin password"""
    admins = _load_admins()
    provided_hash = hash_password(provided_password)
    
    # Check against all active admins
    for admin in admins:
        if admin.get("is_active", True):
            if admin.get("password_hash") == provided_hash:
                # Update last login
                admin["last_login"] = datetime.now().isoformat()
                _save_admins(admins)
                return True
    
    # Fallback: check against env password for backward compatibility
    admin_password = os.getenv('ADMIN_WEB_PASSWORD', 'admin123')
    if provided_password == admin_password:
        return True
    
    return False


def authenticate_admin(username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Authenticate admin by username and password"""
    admins = _load_admins()
    password_hash = hash_password(password)
    
    for admin in admins:
        if admin["username"].lower() == username.lower() and admin.get("is_active", True):
            if admin.get("password_hash") == password_hash:
                # Update last login
                admin["last_login"] = datetime.now().isoformat()
                _save_admins(admins)
                
                # Return admin info (without password)
                return True, {
                    "id": admin["id"],
                    "username": admin["username"],
                    "role": admin.get("role", "admin")
                }
    
    return False, None


def validate_admin_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate a bearer token such as 'admin_token_{id}' and return admin info if valid."""
    if not token:
        return None
    # allow both raw token or 'Bearer ' prefix
    if token.startswith('Bearer '):
        token = token.split(' ', 1)[1]
    # Token format: admin_token_{id} or admin_token_123
    if not token.startswith('admin_token_'):
        return None

    admin_id = token[len('admin_token_'):]

    # Special case: the compatibility token 'admin_token_123' doesn't encode an id
    if admin_id == '123':
        # return a fallback superadmin user info
        admins = _load_admins()
        # return the first active admin
        for a in admins:
            if a.get('is_active', True):
                return { 'id': a['id'], 'username': a['username'], 'role': a.get('role', 'admin') }
        return None

    # Match admin id directly - token may include full id (admin_default) or short suffix
    admins = _load_admins()
    for a in admins:
        if (a['id'] == admin_id or a['id'].endswith(admin_id)) and a.get('is_active', True):
            return { 'id': a['id'], 'username': a['username'], 'role': a.get('role', 'admin') }
    return None


def get_admin_password_hash() -> str:
    """Get hashed admin password for storage"""
    admin_password = os.getenv('ADMIN_WEB_PASSWORD', 'admin123')
    return hash_password(admin_password)
