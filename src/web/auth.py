"""Authentication module for web interface"""

import hashlib
import os
from typing import Optional

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = os.getenv('ADMIN_PASSWORD_SALT', 'default_salt_change_in_production')
    return hashlib.sha256((password + salt).encode()).hexdigest()

def check_admin_password(provided_password: str, stored_hash: Optional[str] = None) -> bool:
    """Check if provided password matches admin password"""
    # Get admin password from env or use default
    admin_password = os.getenv('ADMIN_WEB_PASSWORD', 'admin123')
    
    provided_hash = hash_password(provided_password)
    
    if stored_hash:
        return provided_hash == stored_hash
    else:
        return provided_password == admin_password

def get_admin_password_hash() -> str:
    """Get hashed admin password for storage"""
    admin_password = os.getenv('ADMIN_WEB_PASSWORD', 'admin123')
    return hash_password(admin_password)
