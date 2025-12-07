#!/usr/bin/env python3
"""Share Google Sheet and Calendar with Cloud Run Service Account"""

from google.auth import default
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем credentials
credentials, project = default()

# Service Account который используется Cloud Run
service_account_email = "tattoo-bot-sa@tattoo-480007.iam.gserviceaccount.com"

# Sheet ID
sheet_id = "17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ"

# Calendar ID
calendar_id = "google@tattoo.me"

# Делимся Google Sheet
try:
    drive_service = build('drive', 'v3', credentials=credentials)
    
    logger.info(f"Sharing Google Sheet {sheet_id} with {service_account_email}...")
    
    permission = {
        'type': 'user',
        'role': 'editor',
        'emailAddress': service_account_email
    }
    
    result = drive_service.permissions().create(
        fileId=sheet_id,
        body=permission,
        fields='id'
    ).execute()
    
    logger.info(f"✅ Sheet shared successfully: {result}")
except Exception as e:
    logger.error(f"❌ Failed to share sheet: {e}")

# Делимся Google Calendar
try:
    calendar_service = build('calendar', 'v3', credentials=credentials)
    
    logger.info(f"Sharing Google Calendar {calendar_id} with {service_account_email}...")
    
    rule = {
        'scope': {
            'type': 'user',
            'value': service_account_email
        },
        'role': 'editor'
    }
    
    result = calendar_service.acl().insert(
        calendarId=calendar_id,
        body=rule
    ).execute()
    
    logger.info(f"✅ Calendar shared successfully: {result}")
except Exception as e:
    logger.error(f"❌ Failed to share calendar: {e}")

logger.info("Done!")
