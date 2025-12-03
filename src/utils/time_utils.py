from datetime import datetime, timedelta
import pytz
from typing import List, Tuple

def now(tz_name: str = "Asia/Jerusalem") -> datetime:
    """Get current time in specified timezone"""
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)

def to_datetime(date_str: str, time_str: str, tz_name: str = "Asia/Jerusalem") -> datetime:
    """Convert date and time strings to datetime with timezone"""
    tz = pytz.timezone(tz_name)
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    return tz.localize(dt)

def to_iso_format(dt: datetime) -> str:
    """Convert datetime to ISO format for Google Calendar"""
    return dt.isoformat()

def generate_time_slots(start_hour: int, end_hour: int, slot_minutes: int = 60) -> List[Tuple[str, str]]:
    """Generate daily time slots between two hours (e.g., 09:00 to 18:00)"""
    slots = []
    curr = start_hour * 60
    end = end_hour * 60
    while curr < end:
        s = (curr // 60, curr % 60)
        e_min = curr + slot_minutes
        e = (e_min // 60, e_min % 60)
        slots.append((f"{s[0]:02d}:{s[1]:02d}", f"{e[0]:02d}:{e[1]:02d}"))
        curr += slot_minutes
    return slots

def get_next_business_days(days: int = 7, tz_name: str = "Asia/Jerusalem") -> List[str]:
    """Get next N business days (excludes Fridays/Saturdays for Israel)"""
    tz = pytz.timezone(tz_name)
    result = []
    current = datetime.now(tz).date()
    while len(result) < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # 0-4 = Mon-Fri
            result.append(current.strftime("%Y-%m-%d"))
    return result
