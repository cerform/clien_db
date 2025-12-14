"""
Utility to check and initialize Google Sheets structure for the app.
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

EXPECTED_SHEETS_HEADERS = {
    "clients": ["id","telegram_id","name","phone","email","notes","tags","created_at","last_visit"],
    "masters": ["id","name","specialization","rating","experience_years","instagram","status","telegram_id","calendar_id","notes"],
    "services": ["id","name","description","duration_min","price_from","price_to","category","active"],
    "bookings": ["id","client_id","master_id","service_id","datetime_start","datetime_end","status","price","comment_client","comment_master","source","created_at","updated_at","google_event_id"],
    "config": ["key","value","description"],
    "conversations": ["id","client_id","message","assistant_reply","timestamp","source"],
}

def ensure_sheets_structure(sheets_client, spreadsheet_id: str) -> None:
    """Ensure that all expected sheets exist and have headers. Uses an instance of SheetsClient."""
    if not spreadsheet_id:
        raise ValueError("spreadsheet_id is required")

    service = getattr(sheets_client, "service_sheets", None)
    if not service:
        raise RuntimeError("sheets_client.service_sheets not initialized")

    # Get spreadsheet metadata
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing_sheets = [s["properties"]["title"] for s in ss.get("sheets", [])]

    requests = []
    for sheet_name, header in EXPECTED_SHEETS_HEADERS.items():
        if sheet_name not in existing_sheets:
            logger.info("Sheet '%s' missing, creating...", sheet_name)
            requests.append({"addSheet": {"properties": {"title": sheet_name}}})
    if requests:
        body = {"requests": requests}
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        logger.info("Added missing sheets: %s", requests)

    # Ensure headers exist (create or patch)
    for sheet, header in EXPECTED_SHEETS_HEADERS.items():
        try:
            resp = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f"{sheet}!A1:Z1").execute()
            values = resp.get("values", [])
            existing_header = values[0] if values else []
            if existing_header != header:
                logger.info("Updating header for sheet %s", sheet)
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet}!A1:Z1",
                    valueInputOption="RAW",
                    body={"values": [header]}
                ).execute()
        except Exception as e:
            logger.warning("Failed to ensure header for %s: %s", sheet, e)

    logger.info("✅ Spreadsheet %s structure ensured", spreadsheet_id)
