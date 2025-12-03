import os
import logging
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/calendar"]
logger = logging.getLogger(__name__)

class SheetsClient:
    def __init__(self, creds_path="credentials.json", token_path="token.json"):
        # Convert to absolute paths if relative
        if not os.path.isabs(creds_path):
            # Get project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.creds_path = os.path.join(project_root, creds_path)
        else:
            self.creds_path = creds_path
            
        if not os.path.isabs(token_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.token_path = os.path.join(project_root, token_path)
        else:
            self.token_path = token_path
            
        self.creds = None
        self.service_sheets = None
        self.service_calendar = None
        self._ensure_credentials()

    def _ensure_credentials(self):
        logger.info(f"Looking for credentials at: {self.creds_path}")
        logger.info(f"Looking for token at: {self.token_path}")
        
        if os.path.exists(self.token_path):
            logger.info(f"Found token file, loading...")
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    logger.info("Refreshing expired credentials...")
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.warning("Failed to refresh: %s", e)
            else:
                if not os.path.exists(self.creds_path):
                    raise FileNotFoundError(
                        f"OAuth credentials not found at {self.creds_path}\n"
                        f"Current working directory: {os.getcwd()}\n"
                        f"Please ensure credentials.json is in the project root."
                    )
                logger.info("Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
                logger.info(f"Saving token to {self.token_path}")
                with open(self.token_path, "w", encoding="utf-8") as f:
                    f.write(self.creds.to_json())
        
        logger.info("Building Google API services...")
        self.service_sheets = build("sheets", "v4", credentials=self.creds)
        self.service_calendar = build("calendar", "v3", credentials=self.creds)
        logger.info("✅ Google API services ready")

    def create_spreadsheet_template(self, title="TattooStudio_DB") -> str:
        spreadsheet = {
            "properties": {"title": title},
            "sheets": [
                {"properties": {"title": "clients"}},
                {"properties": {"title": "masters"}},
                {"properties": {"title": "calendar"}},
                {"properties": {"title": "bookings"}},
            ]
        }
        try:
            result = self.service_sheets.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result["spreadsheetId"]
            headers = {
                "clients": [["id","telegram_id","name","phone","email","notes","created_at"]],
                "masters": [["id","name","calendar_id","specialties","active","created_at"]],
                "calendar": [["date","master_id","slot_start","slot_end","available","note"]],
                "bookings": [["id","client_id","master_id","date","slot_start","slot_end","status","created_at","google_event_id"]],
            }
            for sheet, h in headers.items():
                self.service_sheets.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id, range=f"{sheet}!A1:Z1",
                    valueInputOption="RAW", body={"values": h}
                ).execute()
            return spreadsheet_id
        except HttpError as e:
            logger.exception("Failed to create spreadsheet: %s", e)
            raise

    def read_sheet(self, spreadsheet_id: str, sheet_name: str) -> List[Dict[str, Any]]:
        resp = self.service_sheets.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=sheet_name
        ).execute()
        values = resp.get("values", [])
        if not values:
            return []
        headers = values[0]
        rows = []
        for row in values[1:]:
            d = {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
            rows.append(d)
        return rows

    def append_row(self, spreadsheet_id: str, sheet_name: str, row: List[Any]):
        body = {"values": [row]}
        return self.service_sheets.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=sheet_name,
            valueInputOption="RAW", body=body
        ).execute()

    def update_row(self, spreadsheet_id: str, sheet_name: str, row_index: int, row: List[Any]):
        range_a1 = f"{sheet_name}!A{row_index+1}"
        body = {"values": [row]}
        return self.service_sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_a1,
            valueInputOption="RAW", body=body
        ).execute()

    def create_calendar_event(self, calendar_id: str, start_iso: str, end_iso: str, summary: str, description: str="") -> str:
        event = {"summary": summary, "description": description, "start": {"dateTime": start_iso}, "end": {"dateTime": end_iso}}
        created = self.service_calendar.events().insert(calendarId=calendar_id, body=event).execute()
        return created.get("id")

    def delete_calendar_event(self, calendar_id: str, event_id: str):
        return self.service_calendar.events().delete(calendarId=calendar_id, eventId=event_id).execute()
