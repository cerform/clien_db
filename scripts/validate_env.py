#!/usr/bin/env python3
"""Validate required environment variables for Tattoo Bot
This script checks that required env vars are present and optionally tests DB connectivity.
"""
import os
import sys
import logging

# Ensure repo root is importable as 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUIRED_VARS = [
    'TELEGRAM_BOT_TOKEN',
    'OPENAI_API_KEY',
    'SPREADSHEET_ID',
    'GOOGLE_CREDENTIALS_PATH',
]

def check_env_vars():
    missing = []
    for v in REQUIRED_VARS:
        if not os.getenv(v):
            missing.append(v)
    return missing

def test_db_connection():
    try:
        from src.db.cloudsql_client import init_cloudsql_client
        client = init_cloudsql_client()
        ok = client.test_connection()
        return ok
    except Exception as e:
        logger.warning(f"DB test failed: {e}")
        return False

def main():
    cfg = Config.from_env()
    print("Config:")
    print(f"  BOT_TOKEN: {'set' if cfg.BOT_TOKEN else 'not set'}")
    print(f"  OPENAI_API_KEY: {'set' if cfg.OPENAI_API_KEY else 'not set'}")
    print(f"  SPREADSHEET_ID: {cfg.SPREADSHEET_ID or 'not set'}")
    print(f"  ADMIN_USER_IDS: {cfg.ADMIN_USER_IDS}")

    missing = check_env_vars()
    if missing:
        logger.error("Missing required env vars: %s", ', '.join(missing))
        print("Please set these env vars or add to .env and re-run.")
        sys.exit(1)

    print("Basic env vars OK")

    print("Checking database connectivity...")
    if test_db_connection():
        print("✅ Database connected")
    else:
        print("⚠️ Database connection failed or not configured")
        sys.exit(2)

    print("All checks OK")

if __name__ == '__main__':
    main()
