"""Client keyboards - DEPRECATED

All keyboard UI has been removed from the bot. These helper functions now
return None to ensure no keyboards are included in messages and the chat is
pure conversational.
"""
from typing import List, Dict, Optional


def get_main_menu(lang: str = "en") -> Optional[dict]:
    """Return None to avoid sending ReplyKeyboard markup."""
    return None


def get_language_keyboard() -> Optional[dict]:
    """Return None so language selection via inline keyboard is disabled."""
    return None


def get_calendar_keyboard() -> Optional[dict]:
    """Return None: Calendar UI via inline keyboard disabled."""
    return None


def get_time_slots_keyboard() -> Optional[dict]:
    """Return None: time slots inline keyboard disabled."""
    return None


def slots_keyboard(slots: List[Dict]) -> Optional[dict]:
    return None


def masters_keyboard(masters: List[Dict]) -> Optional[dict]:
    return None


def dates_keyboard(dates: List[str]) -> Optional[dict]:
    return None


def confirm_kb() -> Optional[dict]:
    return None
