#!/usr/bin/env python3
"""Generate or refresh Google OAuth token (token.json) in project root.

This script will use `GOOGLE_CREDENTIALS_PATH` and `GOOGLE_TOKEN_PATH` from
the environment (or defaults `credentials.json` / `token.json`) and trigger
the installed-app OAuth flow (opens a browser) if no valid token exists.

Usage:
  python tools/generate_google_token.py

Notes:
 - Do NOT commit `token.json` to git. It's added to `.gitignore` already.
 - If you're using a service account, you do not need this token; instead
   provide `credentials.json` with `type: service_account` and the app will
   use ADC/service account credentials.
"""
import os
import sys
import logging

# Ensure project root is on PYTHONPATH so `src` package is importable when run
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config.env_loader import load_env

load_env()
logger = logging.getLogger(__name__)

def main():
    creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    token_path = os.getenv('GOOGLE_TOKEN_PATH', 'token.json')
    print(f"Using credentials: {creds_path}")
    print(f"Token will be stored at: {token_path}")

    try:
        # Import here so the module-level logic doesn't run during tests
        from src.db.sheets_client import SheetsClient
        sc = SheetsClient(creds_path=creds_path, token_path=token_path)
        print(f"✅ Token is present or was created at: {sc.token_path}")
    except FileNotFoundError as e:
        print("❌ Credentials not found or ADC failed:")
        print(e)
        sys.exit(1)
    except Exception as e:
        print("❌ Failed to generate token:")
        print(e)
        sys.exit(2)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
