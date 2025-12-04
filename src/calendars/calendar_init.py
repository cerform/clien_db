"""Initialize Google Calendar service for INKA"""

import logging
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service(credentials_file: str):
    """
    Create Google Calendar service using service account credentials
    
    Args:
        credentials_file: Path to credentials JSON file
        
    Returns:
        Google Calendar API service object or None if failed
    """
    try:
        credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=credentials)
        logger.info("✅ Google Calendar service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to initialize Google Calendar service: {e}")
        return None
