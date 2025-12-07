#!/usr/bin/env python3
"""
Test append_row function directly
"""
import sys
import logging
from datetime import datetime
sys.path.insert(0, '/home/etcsys/projects/clien_db')

from src.db.sheets_client import GoogleSheetsClient
from src.utils.env_loader import setup_environment

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
setup_environment()

SPREADSHEET_ID = "17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ"

try:
    logger.info("=" * 60)
    logger.info("🧪 Testing append_row() function")
    logger.info("=" * 60)
    
    # Initialize sheets client with credentials.json
    logger.info("📋 Initializing GoogleSheetsClient...")
    sheets_client = GoogleSheetsClient(credentials_path="credentials.json", spreadsheet_id=SPREADSHEET_ID)
    
    logger.info("✅ GoogleSheetsClient initialized successfully")
    
    # Try to append a test row
    test_values = [
        f"test-{datetime.now().isoformat()}",  # id
        "9999999999",  # telegram_id
        "Test User",  # name
        "+1234567890",  # phone
        "test@example.com",  # email
        "Test client - auto cleanup",  # notes
        datetime.now().isoformat(),  # created_at
        ""  # last_visit
    ]
    
    logger.info(f"📝 Appending test row to 'clients' sheet:")
    logger.info(f"   Values: {test_values}")
    
    result = sheets_client.append_row("clients", [test_values])
    
    if result:
        logger.info(f"✅ SUCCESS! Row appended: {result}")
    else:
        logger.error(f"❌ FAILED! append_row returned False")
        
except Exception as e:
    logger.error(f"❌ ERROR: {e}", exc_info=True)
    sys.exit(1)
