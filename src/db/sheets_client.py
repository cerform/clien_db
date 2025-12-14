import os
import logging
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.auth import default as google_auth_default

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    # Drive scope is required for creating spreadsheets and managing sharing
    "https://www.googleapis.com/auth/drive"
]
logger = logging.getLogger(__name__)

class SheetsClient:
    # Expose module-level SCOPES as a class attribute for tests and external usage
    SCOPES = SCOPES
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
                if os.path.exists(self.creds_path):
                    # Distinguish service account vs OAuth client secret JSON files
                    try:
                        import json
                        with open(self.creds_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        cred_type = data.get("type")
                    except Exception:
                        cred_type = None

                    if cred_type == "service_account":
                        # Use service account credentials for headless access
                        try:
                            logger.info("Using service account credentials from %s", self.creds_path)
                            self.creds = service_account.Credentials.from_service_account_file(
                                self.creds_path, scopes=SCOPES
                            )
                        except Exception as e:
                            logger.exception("Failed to load service account credentials: %s", e)
                            raise
                    else:
                        # Not a service account - fallback to OAuth installed flow
                        logger.info("Starting OAuth flow...")
                        flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
                        self.creds = flow.run_local_server(port=0)
                        logger.info(f"Saving token to {self.token_path}")
                        with open(self.token_path, "w", encoding="utf-8") as f:
                            f.write(self.creds.to_json())
                else:
                    # No creds file found; try Application Default Credentials (service account on GCP)
                    try:
                        creds, project = google_auth_default(scopes=SCOPES)
                        self.creds = creds
                        logger.info("Using Application Default Credentials for Google APIs")
                    except Exception:
                        raise FileNotFoundError(
                            f"OAuth credentials not found at {self.creds_path} and ADC failed.\n"
                            f"Current working directory: {os.getcwd()}\n"
                            f"Please ensure credentials.json is in the project root or configure GOOGLE_APPLICATION_CREDENTIALS."
                        )
        
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
                "clients": [["id","telegram_id","name","phone","email","notes","tags","created_at","last_visit"]],
                "masters": [["id","name","specialization","rating","experience_years","instagram","status","telegram_id","calendar_id","notes"]],
                "services": [["id","name","description","duration_min","price_from","price_to","category","active"]],
                "bookings": [["id","client_id","master_id","service_id","datetime_start","datetime_end","status","price","comment_client","comment_master","source","created_at","updated_at","google_event_id"]],
                "config": [["key","value","description"]],
                "conversations": [["id","client_id","message","assistant_reply","timestamp","source"]],
            }
            for sheet, h in headers.items():
                self.service_sheets.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id, range=f"{sheet}!A1:Z1",
                    valueInputOption="RAW", body={"values": h}
                ).execute()
            return spreadsheet_id
        except HttpError as e:
            # Provide additional hint for permission errors
            if hasattr(e, 'status_code') and e.status_code == 403:
                logger.error("Permission denied when creating spreadsheet (403). Ensure Google Sheets & Drive APIs are enabled and the credentials have proper access. If using a service account, consider sharing a template spreadsheet with the service account's email and set SPREADSHEET_ID in .env.")
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

    def ensure_sheet_format(self, spreadsheet_id: str, overwrite_headers: bool = False):
        """
        Ensure the spreadsheet contains the required sheets and header rows.
        If a sheet is missing, it will be added. If headers are missing or overwrite_headers=True,
        the header row will be set to the expected headers for that sheet.

        Args:
            spreadsheet_id: the ID of the Google Sheet
            overwrite_headers: if True, will overwrite the first row with the default headers
        Returns:
            dict: {'created_sheets': [...], 'updated_headers': [...]} - summary of changes made
        """
        logger.info(f"Ensuring sheet format for spreadsheet {spreadsheet_id}")

        # Expected sheet headers - should mirror create_spreadsheet_template headers
        headers = {
            "clients": ["id", "telegram_id", "name", "phone", "email", "notes", "tags", "created_at", "last_visit"],
            "masters": ["id", "name", "specialization", "rating", "experience_years", "instagram", "status", "telegram_id", "calendar_id", "notes"],
            "services": ["id", "name", "description", "duration_min", "price_from", "price_to", "category", "active"],
            "bookings": ["id", "client_id", "master_id", "service_id", "datetime_start", "datetime_end", "status", "price", "comment_client", "comment_master", "source", "created_at", "updated_at", "google_event_id"],
            "config": ["key", "value", "description"],
            "conversations": ["id", "client_id", "message", "assistant_reply", "timestamp", "source"],
            "calendar": ["date", "master_id", "slot_start", "slot_end", "available", "note"]
        }

        created_sheets = []
        updated_headers = []

        try:
            meta = self.service_sheets.spreadsheets().get(spreadsheetId=spreadsheet_id, fields="sheets.properties").execute()
            existing = {s['properties']['title']: s['properties'].get('sheetId') for s in meta.get('sheets', [])}
        except Exception as e:
            logger.exception(f"Failed to fetch spreadsheet metadata: {e}")
            raise

        requests = []
        # Add missing sheets
        for sheet_name in headers.keys():
            if sheet_name not in existing:
                logger.info(f"Sheet '{sheet_name}' not found; creating")
                created_sheets.append(sheet_name)
                requests.append({
                    "addSheet": {"properties": {"title": sheet_name}}
                })

        # If we need to add sheets, do it in batch
        if requests:
            try:
                self.service_sheets.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()
                logger.info("Created missing sheets successfully")
                # refresh metadata
                meta = self.service_sheets.spreadsheets().get(spreadsheetId=spreadsheet_id, fields="sheets.properties").execute()
                existing = {s['properties']['title']: s['properties'].get('sheetId') for s in meta.get('sheets', [])}
            except Exception as e:
                logger.exception(f"Failed creating missing sheets: {e}")
                raise

        # Ensure header rows
        for sheet_name, header_row in headers.items():
            try:
                # Read header row
                resp = self.service_sheets.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A1:Z1").execute()
                existing_vals = resp.get('values', [])
                if not existing_vals or overwrite_headers:
                    logger.info(f"Setting header row for '{sheet_name}'")
                    self.service_sheets.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=f"{sheet_name}!A1",
                        valueInputOption="RAW",
                        body={"values": [header_row]}
                    ).execute()
                    updated_headers.append(sheet_name)
                else:
                    # Validate header presence - if critical headers missing, patch them
                    current = existing_vals[0]
                    missing = [h for h in header_row if h not in current]
                    if missing:
                        # Append missing columns at the end
                        blended = current + missing
                        logger.info(f"Patching missing headers for '{sheet_name}': {missing}")
                        self.service_sheets.spreadsheets().values().update(
                            spreadsheetId=spreadsheet_id,
                            range=f"{sheet_name}!A1",
                            valueInputOption="RAW",
                            body={"values": [blended]}
                        ).execute()
                        updated_headers.append(sheet_name)
            except Exception as e:
                # If sheet empty or range not found, set header row
                logger.debug(f"Error while validating header for {sheet_name}: {e}")
                try:
                    logger.info(f"Attempting to (re)create header row for '{sheet_name}'")
                    self.service_sheets.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=f"{sheet_name}!A1",
                        valueInputOption="RAW",
                        body={"values": [header_row]}
                    ).execute()
                    updated_headers.append(sheet_name)
                except Exception:
                    logger.exception(f"Failed to set header row for {sheet_name}")
        # Optionally format headers (bold)
        try:
            format_requests = []
            for sheet_name in updated_headers:
                sheet_id = existing.get(sheet_name)
                if sheet_id:
                    # Bold header text and set background color
                    format_requests.append({
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.93, "green": 0.93, "blue": 0.93}}},
                            "fields": "userEnteredFormat(textFormat,backgroundColor)"
                        }
                    })
                    # Freeze the first row
                    format_requests.append({
                        "updateSheetProperties": {
                            "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                            "fields": "gridProperties.frozenRowCount"
                        }
                    })
                    # Auto-resize columns for number of header columns found
                    # Determine header length by reading current header row
                    try:
                        resp = self.service_sheets.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A1:Z1").execute()
                        current = resp.get('values', [])
                        col_count = len(current[0]) if current else 0
                    except Exception:
                        col_count = 0
                    if col_count > 0:
                        format_requests.append({
                            "autoResizeDimensions": {
                                "dimensions": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": col_count}
                            }
                        })
            if format_requests:
                self.service_sheets.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": format_requests}).execute()
        except Exception:
            logger.exception("Failed to apply header formatting")

        # Track formatting applied in summary
        try:
            if format_requests:
                summary.setdefault('formatted_sheets', [])
                summary['formatted_sheets'].extend(updated_headers)
        except Exception:
            pass

        summary = {"created_sheets": created_sheets, "updated_headers": updated_headers}
        logger.info(f"ensure_sheet_format summary: {summary}")
        return summary
