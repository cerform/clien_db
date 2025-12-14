import os
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
import jwt

JWT_SECRET = os.getenv('JWT_SECRET', '')
if not JWT_SECRET:
    # For development fallback, but in production set JWT_SECRET env
    JWT_SECRET = os.getenv('JWT_SECRET', None) or 'dev-secret-please-change'


def create_jwt_for_admin(admin_id: int, expires_minutes: int = 60*24) -> str:
    payload = {
        'sub': str(admin_id),
        'role': 'admin',
        'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token


def verify_jwt(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        admin_id = payload.get('sub')
        return int(admin_id) if admin_id else None
    except Exception:
        return None


def authenticate_admin(username, password) -> Tuple[bool, dict]:
    # Simple placeholder to authenticate admin by username/password — can be replaced with real check.
    if username and password:
        return True, {'username': username, 'id': 1}
    return False, {}


def check_admin_password(password) -> bool:
    # Simple fallback password check
    return password == os.getenv('ADMIN_PASSWORD', 'admin')
