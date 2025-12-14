#!/usr/bin/env python3
"""Ensure Google Sheets contains expected structure and header rows.

Usage:
  ./scripts/ensure_sheet_format.py --id <SPREADSHEET_ID> [--overwrite]
  or
  ./scripts/ensure_sheet_format.py

If SPREADSHEET_ID is missing, the script will read env SPREADSHEET_ID.
"""
import os
import argparse
from src.config.env_loader import load_env
from src.db.sheets_client import SheetsClient


def main():
    load_env()
    parser = argparse.ArgumentParser(description="Ensure Google Sheets format")
    parser.add_argument('--id', '-i', help='Spreadsheet ID')
    parser.add_argument('--overwrite', '-o', action='store_true', help='Overwrite header rows')
    args = parser.parse_args()

    sid = args.id or os.getenv('SPREADSHEET_ID')
    if not sid:
        print('SPREADSHEET_ID is not set. Provide --id or set SPREADSHEET_ID in environment')
        return

    sc = SheetsClient()
    try:
        summary = sc.ensure_sheet_format(sid, overwrite_headers=args.overwrite)
        print('Done. Summary:', summary)
    except Exception as e:
        print('Failed to ensure spreadsheet format:', e)
        raise


if __name__ == '__main__':
    main()



