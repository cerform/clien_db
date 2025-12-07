import pytz
from datetime import datetime
from typing import Optional

def get_current_time(timezone: str = "Europe/Moscow") -> datetime:
    """Get current time in specified timezone"""
    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        tz = pytz.timezone("Europe/Moscow")
    
    return datetime.now(tz)

def convert_to_timezone(dt: datetime, timezone: str = "Europe/Moscow") -> datetime:
    """Convert datetime to specified timezone"""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        tz = pytz.timezone("Europe/Moscow")
    
    return dt.astimezone(tz)

def format_datetime(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """Format datetime to string"""
    return dt.strftime(format_str)

def parse_datetime(date_str: str, format_str: str = "%d.%m.%Y %H:%M") -> Optional[datetime]:
    """Parse datetime from string"""
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None
