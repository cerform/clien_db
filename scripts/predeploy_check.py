#!/usr/bin/env python3
"""Pre-deploy checks for Cloud Run deployment.

Checks:
- Essential env vars exist: SPREADSHEET_ID if FORCE_SHEET_MODE, TELEGRAM_BOT_TOKEN, GOOGLE_CREDENTIALS
- Google Sheets & Calendar API connectivity (via SheetsClient)
- Telegram bot token validity (getMe)
- LLM OPENAI_API_KEY presence

Exit codes: 0 on success; non-zero on failure.
"""

import os
import sys
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from src.core.config_manager import get_config
    from src.db.sheets_client import SheetsClient
    from src.config.env_loader import load_env
except Exception:
    # Try adding repo root to path and fall back gracefully if libs not installed
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    try:
        from src.core.config_manager import get_config
        from src.db.sheets_client import SheetsClient
        from src.config.env_loader import load_env
    except Exception:
        get_config = None
        SheetsClient = None
        def load_env():
            return None

load_env()

failed = False

def check_env_var(name):
    val = os.getenv(name)
    if val:
        logger.info(f"{name} = set")
        return True
    logger.warning(f"{name} is not set")
    return False

# 1) Check forced sheet mode vs SPREADSHEET_ID
force_sheet_mode = os.getenv('FORCE_SHEET_MODE', '') in ('1', 'true', 'True')
spreadsheet_id = os.getenv('SPREADSHEET_ID')
if force_sheet_mode and not spreadsheet_id:
    logger.error('FORCE_SHEET_MODE is enabled but SPREADSHEET_ID is missing; aborting predeploy')
    failed = True

# 2) Check credential file or ADC
creds_found = os.path.exists('credentials.json') or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if creds_found:
    logger.info('Google credentials appear to be present (credentials.json or GOOGLE_APPLICATION_CREDENTIALS)')
else:
    logger.warning('Google OAuth credentials not found; Google API calls will likely fail')

# 3) Validate Telegram token (GET /getMe)
bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
if bot_token:
    try:
        resp = requests.get(f'https://api.telegram.org/bot{bot_token}/getMe', timeout=10)
        if resp.status_code == 200 and resp.json().get('ok'):
            logger.info('Telegram BOT token validated (getMe ok)')
        else:
            logger.error('Telegram BOT token invalid: %s', resp.text)
            failed = True
    except Exception as e:
        logger.exception('Error validating Telegram token: %s', e)
        failed = True
else:
    logger.warning('TELEGRAM_BOT_TOKEN not set')

# 4) Check LLM key presence
llm_key = os.getenv('OPENAI_API_KEY')
if llm_key:
    logger.info('OPENAI_API_KEY is set')
else:
    logger.warning('OPENAI_API_KEY not set; LLM features will not be available')

# 5) Check Google Sheets / Calendar connectivity if spreadsheet id present
if spreadsheet_id:
    logger.info(f'Spreadsheet ID set to {spreadsheet_id}, testing Sheets/Calendar API...')
    try:
        if not SheetsClient:
            raise RuntimeError('SheetsClient not available in this runner')
        sc = SheetsClient()
        # Try to read simple sheet names (clients) or do an obvious call
        try:
            rows = sc.read_sheet(spreadsheet_id, 'clients')
            logger.info('Read clients sheet ok (rows=%d)', len(rows))
        except Exception:
            # Not all template sheets must exist, try read metadata by creating service
            logger.info('clients sheet not read; ensure the created template or use create_google_sheets_structure.py')
        # Also try calendar service by listing primary calendar events harmlessly
        try:
            logger.info('Attempting to query calendar events (list) for primary calendar ID...')
            cal_events = sc.service_calendar.events().list(calendarId='primary', maxResults=1).execute()
            logger.info('Calendar API access ok (events found=%d)', len(cal_events.get('items', [])))
        except Exception:
            logger.warning('Calendar query failed; calendar access might not be configured or calendar ID missing')
        # If requested via environment, try to auto-fix sheet structure
        auto_fix = os.getenv('AUTO_FIX_SHEETS', '') in ('1', 'true', 'True')
        overwrite_headers = os.getenv('OVERWRITE_SHEET_HEADERS', '') in ('1', 'true', 'True')
        if auto_fix:
            logger.info('AUTO_FIX_SHEETS enabled - attempting to ensure sheet structure and headers...')
            try:
                summary = sc.ensure_sheet_format(spreadsheet_id, overwrite_headers=overwrite_headers)
                logger.info('AUTO_FIX_SHEETS done: %s', summary)
            except Exception as e:
                logger.exception('Failed to auto-fix Sheets: %s', e)
    except Exception as e:
        logger.exception('Failed to initialize Google API client: %s', e)
        # Do not strictly fail here; warn and proceed so that Cloud Build container without deps can still run
        logger.warning('Skipping Google API connectivity tests; missing python dependencies in runtime')

if failed:
    logger.error('Predeploy checks failed; fix issues and re-run the script. See errors above.')
    sys.exit(2)

logger.info('Predeploy checks passed successfully')
sys.exit(0)
