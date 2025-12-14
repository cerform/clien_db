#!/usr/bin/env python3
import os
import argparse
from src.config.env_loader import load_env
from src.db.sheets_client import SheetsClient

def main():
    load_env()
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
    parser = argparse.ArgumentParser(description="Create Google Sheets structure for TattooStudio Bot.")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm sheet creation")
    parser.add_argument("--skip", action="store_true", help="Skip sheet creation")
    parser.add_argument("--use-existing", action="store_true", help="Ensure format on existing SPREADSHEET_ID instead of creating a new one")
    args = parser.parse_args()

    if args.skip:
        print("Skipping Google Sheets creation as requested.")
        return

    sc = SheetsClient(creds_path=creds_path, token_path=token_path)

    if not args.yes:
        confirm = input("Create Google Sheets spreadsheet from template now? Y/n: ")
        if confirm and confirm.lower().startswith("n"):
            print("Aborting sheet creation.")
            return

    try:
        if args.use_existing:
            sid = os.getenv('SPREADSHEET_ID')
            if not sid:
                raise ValueError('SPREADSHEET_ID must be set in env when using --use-existing')
            print(f"Ensuring format for existing spreadsheet {sid}")
            summary = sc.ensure_sheet_format(sid, overwrite_headers=False)
            print(f"Completed: {summary}")
            spreadsheet_id = sid
        else:
            spreadsheet_id = sc.create_spreadsheet_template(title="TattooStudio_DB")
        print(f"Created spreadsheet: {spreadsheet_id}")
        print("Set SPREADSHEET_ID in .env")
    except Exception as e:
        print("Failed to create spreadsheet. See logs above for details.")
        print("Tips: If you're using a service account, ensure the Google Sheets API & Drive API are enabled in your project and the service account has permissions. Alternatively, create a spreadsheet manually and set SPREADSHEET_ID in .env.")
        raise

if __name__ == "__main__":
    main()
