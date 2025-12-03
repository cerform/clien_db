import logging
from typing import List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SlotsFinder:
    """Find available time slots"""
    
    WORK_HOURS_START = 10  # 10:00
    WORK_HOURS_END = 22    # 22:00
    SLOT_DURATION = 60     # minutes
    
    @staticmethod
    def get_available_slots(occupied_slots: List[str]) -> List[str]:
        """Get available slots based on occupied slots"""
        available = []
        
        for hour in range(SlotsFinder.WORK_HOURS_START, SlotsFinder.WORK_HOURS_END):
            for minute in [0, 30]:
                slot = f"{hour:02d}:{minute:02d}"
                if slot not in occupied_slots:
                    available.append(slot)
        
        return available
    
    @staticmethod
    def get_next_available_day() -> str:
        """Get next available day (skip weekends)"""
        today = datetime.now().date()
        next_day = today + timedelta(days=1)
        
        # Skip weekends (5=Saturday, 6=Sunday)
        while next_day.weekday() in [5, 6]:
            next_day += timedelta(days=1)
        
        return next_day.strftime("%d.%m.%Y")
    
    @staticmethod
    def get_next_n_available_days(n: int = 7) -> List[str]:
        """Get next N available days"""
        days = []
        current_day = datetime.now().date() + timedelta(days=1)
        
        while len(days) < n:
            if current_day.weekday() not in [5, 6]:  # Skip weekends
                days.append(current_day.strftime("%d.%m.%Y"))
            current_day += timedelta(days=1)
        
        return days
