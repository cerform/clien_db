"""Share a Google Spreadsheet with a service account using Drive API.

Usage:
    python3 scripts/share_sheet_with_service_account.py --spreadsheet-id SPREADSHEET_ID --service-account EMAIL

This script uses OAuth2 user credentials (installed app flow). You can use the `credentials.json` file placed in project root (OAuth client credentials).

It will open a browser to authorize if needed.
"""
import argparse
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/drive'
]

TOKEN_PATH = os.path.expanduser('~/.config/clien_db_drive_token.json')
CRED_PATHS = [
    os.path.join(os.getcwd(), 'credentials.json'),
    os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
]


def get_credentials():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            cred_file = None
            for p in CRED_PATHS:
                if os.path.exists(p):
                    cred_file = p
                    break
            if not cred_file:
                print("No credentials.json found in project root. Place OAuth 2.0 client credentials as credentials.json.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, 'w') as fh:
            fh.write(creds.to_json())
    return creds


def share_sheet(spreadsheet_id: str, service_account_email: str, role: str = 'writer'):
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)

    body = {
        'type': 'user',
        'role': role,
        'emailAddress': service_account_email,
    }

    try:
        res = service.permissions().create(fileId=spreadsheet_id, body=body, sendNotificationEmail=False).execute()
        print('Permission created:', res)
    except Exception as e:
        print('Error creating permission:', e)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spreadsheet-id', required=True)
    parser.add_argument('--service-account', required=True)
    parser.add_argument('--role', default='writer', choices=['reader', 'commenter', 'writer', 'owner'])
    args = parser.parse_args()

    share_sheet(args.spreadsheet_id, args.service_account, args.role)


if __name__ == '__main__':
    main()
