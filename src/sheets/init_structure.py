from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def init_sheets(spreadsheet_id, creds_json):
    creds = Credentials.from_service_account_file(creds_json, scopes=[
        "https://www.googleapis.com/auth/spreadsheets"
    ])
    service = build('sheets', 'v4', credentials=creds)
    sheets = service.spreadsheets()
    structure = {
        "clients": ["id", "telegram_id", "name", "phone", "email", "notes", "tags", "created_at", "last_visit"],
        "masters": ["id", "name", "specialization", "rating", "experience_years", "instagram", "status", "telegram_id", "calendar_id", "notes"],
        "services": ["id", "name", "description", "duration_min", "price_from", "price_to", "category", "active"],
        "bookings": ["id", "client_id", "master_id", "service_id", "datetime_start", "datetime_end", "status", "price", "comment_client", "comment_master", "source", "created_at", "updated_at"],
        "config": ["key", "value"]
    }
    for sheet, headers in structure.items():
        try:
            sheets.batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": sheet}}}]}
            ).execute()
        except Exception:
            pass  # already exists
        sheets.values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet}!A1:{chr(65+len(headers)-1)}1",
            valueInputOption="RAW",
            body={"values": [headers]}
        ).execute()
