#!/usr/bin/env python3
"""
Test create_client function directly without webhook
"""
import sys
import os
import asyncio
import logging
from datetime import datetime

sys.path.insert(0, '/home/etcsys/projects/clien_db')

from src.utils.env_loader import setup_environment
from src.config import get_config
from src.db.sheets_client import GoogleSheetsClient
from src.calendars.google_calendar_sync import GoogleCalendarSync
from src.services.data_sync import DataSyncService
from src.ai.advanced_inka import AdvancedINKA

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_create_client():
    """Test creating a client directly"""
    
    try:
        # Load environment
        setup_environment()
        config = get_config()
        
        logger.info("=" * 80)
        logger.info("🧪 Testing create_client() directly")
        logger.info("=" * 80)
        
        # Initialize clients
        logger.info("📋 Initializing Google Sheets client...")
        sheets_client = GoogleSheetsClient(
            credentials_file="credentials.json",
            spreadsheet_id=config.google_spreadsheet_id
        )
        
        logger.info("📅 Initializing Google Calendar sync...")
        calendar_sync = GoogleCalendarSync(
            credentials_file="credentials.json",
            calendar_id=config.google_calendar_id
        )
        
        logger.info("🔄 Initializing Data Sync service...")
        data_sync = DataSyncService(
            sheets_client=sheets_client,
            calendar_service=calendar_sync
        )
        
        logger.info("🤖 Initializing AdvancedINKA...")
        inka = AdvancedINKA(
            api_key=config.openai_api_key,
            assistant_id=config.openai_assistant_id,
            sheets_client=sheets_client,
            calendar_service=calendar_sync,
            data_sync=data_sync
        )
        
        logger.info("✅ All clients initialized successfully")
        logger.info("")
        
        # Now test create_client
        test_telegram_id = 9999999
        test_name = "Test User"
        test_phone = "+1234567890"
        test_email = "test@example.com"
        test_notes = f"Test at {datetime.now().isoformat()}"
        
        logger.info(f"📝 Creating test client:")
        logger.info(f"   telegram_id: {test_telegram_id}")
        logger.info(f"   name: {test_name}")
        logger.info(f"   phone: {test_phone}")
        logger.info(f"   email: {test_email}")
        logger.info(f"   notes: {test_notes}")
        logger.info("")
        
        # Call create_client
        result = inka.create_client(
            telegram_id=test_telegram_id,
            name=test_name,
            phone=test_phone,
            email=test_email,
            notes=test_notes
        )
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"🎉 Result: {result}")
        logger.info("=" * 80)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    result = asyncio.run(test_create_client())
    sys.exit(0 if result else 1)
