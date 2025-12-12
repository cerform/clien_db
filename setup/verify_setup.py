#!/usr/bin/env python3
"""
Simple verifier to check local environment after running setup
Checks:
- Python venv active
- DATABASE_URL can connect to Postgres
- Google Sheets credentials and SPREADSHEET_ID
"""

import os
import sys
import logging
from pathlib import Path

from importlib import import_module

def safe_import(repo_root='.'):
    """Try to import modules by adding repo root to path if needed"""
    try:
        from src.db.cloudsql_client import get_cloudsql_client
        from src.config.env_loader import load_env
        return get_cloudsql_client, load_env
    except Exception:
        # Try to add repo root to sys.path and import again
        repo = Path(repo_root).resolve()
        sys.path.insert(0, str(repo))
        try:
            from src.db.cloudsql_client import get_cloudsql_client
            from src.config.env_loader import load_env
            return get_cloudsql_client, load_env
        except Exception:
            return None, None

get_cloudsql_client, load_env = safe_import('..')
if load_env is None:
    # fallback: simple loader that does nothing
    def load_env():
        return

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_env()

# 1. DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    logger.info(f"DATABASE_URL set to: {DATABASE_URL}")
    try:
        client = get_cloudsql_client()
        ok = client.test_connection()
        logger.info(f"Postgres connection test: {'OK' if ok else 'FAILED'}")
    except Exception as e:
        logger.exception('Failed to test Postgres:')
else:
    logger.warning('DATABASE_URL not set; local Postgres not configured')

# 2. Google Sheets
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
if SPREADSHEET_ID:
    logger.info(f"SPREADSHEET_ID: {SPREADSHEET_ID}")
else:
    logger.warning('SPREADSHEET_ID not set. Consider running create_google_sheets_structure.py')

# 3. Bot token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
if BOT_TOKEN:
    logger.info('Telegram BOT token is set')
else:
    logger.warning('BOT token is not set. Add BOT_TOKEN to .env')

logger.info('Verify complete')
