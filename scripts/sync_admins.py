#!/usr/bin/env python3
"""Sync admin IDs from Cloud SQL into the Google Sheets config sheet."""
import argparse
from src.services.admin_sync import sync_admins_to_sheet
from src.config.env_loader import load_env


def main():
    load_env()
    parser = argparse.ArgumentParser(description="Sync admin IDs from Cloud SQL masters table into Google Sheets config")
    parser.add_argument('--id', '-i', help='Spreadsheet ID', required=True)
    parser.add_argument('--dry-run', action='store_true', help='Do not write to sheet, just print result')
    args = parser.parse_args()

    result = sync_admins_to_sheet(args.id)
    print('Result:', result)
    if args.dry_run:
        print('Dry run; no changes written to sheet')


if __name__ == '__main__':
    main()
