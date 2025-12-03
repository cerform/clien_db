#!/usr/bin/env python3
"""
Database initialization script
Creates Google Sheets with necessary tabs and headers
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.db.sheets_client import GoogleSheetsClient
from src.config import get_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'clients': [
        'user_id',
        'name',
        'phone',
        'email',
        'created_at',
        'status'
    ],
    'masters': [
        'id',
        'name',
        'specialization',
        'phone',
        'calendar_id',
        'created_at',
        'status'
    ],
    'calendar': [
        'master_id',
        'date',
        'start_time',
        'end_time',
        'status',
        'notes'
    ],
    'bookings': [
        'user_id',
        'master_id',
        'date',
        'time',
        'service',
        'created_at',
        'status',
        'notes'
    ]
}

def init_database():
    """Initialize database"""
    try:
        config = get_config()
        sheets = GoogleSheetsClient(
            config.google_credentials_json,
            config.google_spreadsheet_id
        )
        
        logger.info(f"Spreadsheet ID: {config.google_spreadsheet_id}")
        
        # Initialize each sheet with headers
        for sheet_name, headers in HEADERS.items():
            logger.info(f"Initializing sheet: {sheet_name}")
            sheets.append_row(sheet_name, headers)
            logger.info(f"✅ Sheet '{sheet_name}' initialized")
        
        logger.info("\n✅ Database initialized successfully!")
        logger.info(f"Spreadsheet: https://docs.google.com/spreadsheets/d/{config.google_spreadsheet_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
