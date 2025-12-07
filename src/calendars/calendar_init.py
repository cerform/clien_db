"""Initialize Google Calendar service for INKA"""

import logging
import os
from googleapiclient.discovery import build
from google.auth import default as google_default

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service(credentials_file: str = ""):
    """
    Create Google Calendar service using Cloud Run's native Service Account
    
    Args:
        credentials_file: Ignored - using google.auth.default() which handles Cloud Run Service Account
        
    Returns:
        Google Calendar API service object or None if failed
    """
    try:
        logger.info("🔄 Initializing Google Calendar using google.auth.default()...")
        credentials, project_id = google_default(scopes=SCOPES)
        service = build('calendar', 'v3', credentials=credentials)
        logger.info(f"✅ Google Calendar service initialized (Project: {project_id})")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to initialize Google Calendar service: {e}")
        return None

