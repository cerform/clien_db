import re
from typing import Optional
from datetime import datetime

def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    # Remove spaces and hyphens
    phone_cleaned = re.sub(r'[\s\-\(\)]+', '', phone)
    # Check if it contains only digits and starts with + or digit
    return bool(re.match(r'^\+?[0-9]{10,15}$', phone_cleaned))

def validate_email(email: str) -> bool:
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_name(name: str) -> bool:
    """Validate name (at least 2 characters)"""
    return len(name.strip()) >= 2 and len(name.strip()) <= 100

def validate_time_slot(time_str: str) -> bool:
    """Validate time slot format HH:MM"""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def validate_positive_integer(value: str) -> bool:
    """Validate positive integer"""
    try:
        return int(value) > 0
    except ValueError:
        return False
