import logging
logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, sheets_client):
        self.sc = sheets_client

    def push_booking_to_calendar(self, calendar_id: str, start_iso: str, end_iso: str, summary: str, description: str = ""):
        return self.sc.create_calendar_event(calendar_id, start_iso, end_iso, summary, description)

    def remove_booking_from_calendar(self, calendar_id: str, event_id: str):
        return self.sc.delete_calendar_event(calendar_id, event_id)
