#!/usr/bin/env python3
import os
from src.config.env_loader import load_env
from src.db.sheets_client import SheetsClient

def main():
    load_env()
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
    sc = SheetsClient(creds_path=creds_path, token_path=token_path)
    spreadsheet_id = sc.create_spreadsheet_template(title="TattooStudio_DB")
    print(f"Created spreadsheet: {spreadsheet_id}")
    print("Set SPREADSHEET_ID in .env")

if __name__ == "__main__":
    main()
