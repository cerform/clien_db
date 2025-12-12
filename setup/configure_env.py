#!/usr/bin/env python3
"""
Utility to generate `.env` from CLI parameters for the project.

Usage:
    python configure_env.py --bot-token ... --openai-key ... --spreadsheet-id ... --google-creds credentials.json --out .env

Supports writing to .env and printing to STDOUT for CI usage.
"""

import argparse
import os
from pathlib import Path

DEFAULT_TEMPLATE = \
"""TELEGRAM_BOT_TOKEN={bot_token}
OPENAI_API_KEY={openai_key}
SPREADSHEET_ID={spreadsheet_id}
GOOGLE_CREDENTIALS_PATH={google_creds}
GOOGLE_TOKEN_PATH={google_token}
DEFAULT_TIMEZONE={timezone}
ADMIN_USER_IDS={admin_ids}
ENV={env}
USE_WEBHOOK={use_webhook}
WEBHOOK_URL={webhook_url}
PORT={port}
CLOUDSQL_USER={cloudsql_user}
CLOUDSQL_PASSWORD={cloudsql_password}
CLOUDSQL_DB={cloudsql_db}
DATABASE_URL={database_url}
"""


def parse_args():
    p = argparse.ArgumentParser(description='Create .env from CLI args')
    p.add_argument('--bot-token', default='', help='Telegram Bot token')
    p.add_argument('--openai-key', default='', help='OpenAI API key')
    p.add_argument('--spreadsheet-id', default='', help='Google Sheets ID')
    p.add_argument('--google-creds', default='credentials.json', help='Google credentials file path')
    p.add_argument('--google-token', default='token.json', help='Google token path')
    p.add_argument('--timezone', default='Asia/Jerusalem', help='Default timezone')
    p.add_argument('--admin-ids', default='', help='Comma separated admin user ids')
    p.add_argument('--env', default='development', help='ENV')
    p.add_argument('--use-webhook', action='store_true')
    p.add_argument('--webhook-url', default='', help='Webhook URL (if use_webhook)')
    p.add_argument('--port', default='8081', help='Port to bind')
    p.add_argument('--cloudsql-user', default='postgres')
    p.add_argument('--cloudsql-password', default='password')
    p.add_argument('--cloudsql-db', default='admin_messages')
    p.add_argument('--database-url', default='')
    p.add_argument('--out', default='.env', help='Output file path')
    p.add_argument('--force', action='store_true', help='Overwrite existing .env')
    return p.parse_args()


def main():
    args = parse_args()
    out_path = Path(args.out)

    if out_path.exists() and not args.force:
        print(f"{out_path} already exists. Use --force to overwrite.")
        return 1

    # Expand and validate
    data = {
        'bot_token': args.bot_token or os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'openai_key': args.openai_key or os.getenv('OPENAI_API_KEY', ''),
        'spreadsheet_id': args.spreadsheet_id or os.getenv('SPREADSHEET_ID', ''),
        'google_creds': args.google_creds or os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json'),
        'google_token': args.google_token,
        'timezone': args.timezone,
        'admin_ids': args.admin_ids or os.getenv('ADMIN_USER_IDS', ''),
        'env': args.env,
        'use_webhook': 'true' if args.use_webhook else 'false',
        'webhook_url': args.webhook_url or os.getenv('WEBHOOK_URL', ''),
        'port': args.port,
        'cloudsql_user': args.cloudsql_user,
        'cloudsql_password': args.cloudsql_password,
        'cloudsql_db': args.cloudsql_db,
        'database_url': args.database_url or os.getenv('DATABASE_URL', '')
    }

    content = DEFAULT_TEMPLATE.format(**data)

    # Create the destination directory if needed
    if not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(content)
    print(f"Wrote {out_path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
