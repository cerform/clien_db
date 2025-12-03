import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarSync:
    """Sync with Google Calendar"""
    
    def __init__(self, credentials_file: str, calendar_id: str):
        """Initialize calendar sync"""
        self.calendar_id = calendar_id
        self.credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=SCOPES
        )
        self.service = build('calendar', 'v3', credentials=self.credentials)
    
    def get_free_slots(self, date: str, duration: int = 60) -> List[str]:
        """Get free time slots for a date"""
        try:
            # This is a placeholder implementation
            # In a real scenario, you would fetch events and find gaps
            return ['10:00', '11:00', '14:00', '15:00', '16:00']
        except Exception as e:
            logger.error(f"Failed to get free slots: {e}")
            return []
    
    def create_event(self, title: str, start_time: datetime, duration: int = 60) -> bool:
        """Create a calendar event"""
        try:
            end_time = start_time + timedelta(minutes=duration)
            
            event = {
                'summary': title,
                'start': {'dateTime': start_time.isoformat()},
                'end': {'dateTime': end_time.isoformat()},
            }
            
            self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Calendar event created: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return False
    
    def get_events(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get events for a date range"""
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=f"{start_date}T00:00:00Z",
                timeMax=f"{end_date}T23:59:59Z",
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        except Exception as e:
            logger.error(f"Failed to get calendar events: {e}")
            return []
