import re
from typing import Optional

def phone_normalize(phone: str) -> str:
    """Normalize phone to digits and + only"""
    return re.sub(r"[^\d+]", "", phone or "")

def is_valid_phone(phone: str) -> bool:
    """Check if phone is valid (min 7 digits)"""
    p = phone_normalize(phone)
    return len(p) >= 7

def is_valid_email(email: str) -> bool:
    """Check if email format is valid"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize_name(name: str) -> str:
    """Sanitize user name (allow Latin, Hebrew, spaces, numbers)"""
    return re.sub(r'[^a-zA-Z0-9\s\u0590-\u05FF]', '', name).strip()

def validate_date_format(date_str: str) -> bool:
    """Check if date is in YYYY-MM-DD format"""
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, date_str))

def validate_time_format(time_str: str) -> bool:
    """Check if time is in HH:MM format"""
    pattern = r'^\d{2}:\d{2}$'
    if not re.match(pattern, time_str):
        return False
    h, m = map(int, time_str.split(':'))
    return 0 <= h < 24 and 0 <= m < 60
