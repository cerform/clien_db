#!/usr/bin/env python3
"""Simple CLI to run Google Sheets migration for a spreadsheet ID."""
import argparse
import logging
from src.db.sheets_client import SheetsClient
from src.services.sheets_migrator import migrate_spreadsheet

def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Run Google Sheets schema migration')
    parser.add_argument('--spreadsheet', '-s', required=True, help='Spreadsheet ID to migrate')
    args = parser.parse_args()
    sheets = SheetsClient()
    result = migrate_spreadsheet(sheets, args.spreadsheet)
    print('Migration result:')
    for k, v in result.items():
        print(f" - {k}: {v}")

if __name__ == '__main__':
    main()
