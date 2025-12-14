"""
Sheets migration helpers — bring existing sheets to the expected schema without losing data.

This module offers a conservative migration path:
- For each sheet, it collects current headers and rows
- Creates a new dataset with target headers; copies values by column name mapping
- Overwrites the sheet (header + rows) with the new normalized rows

This avoids complex structural mutations while guaranteeing new headers and preserving as much data as possible.
"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

EXPECTED_HEADERS = {
    "clients": ["id","telegram_id","name","phone","email","notes","tags","created_at","last_visit"],
    "masters": ["id","name","specialization","rating","experience_years","instagram","status","telegram_id","calendar_id","notes"],
    "services": ["id","name","description","duration_min","price_from","price_to","category","active"],
    "bookings": ["id","client_id","master_id","service_id","datetime_start","datetime_end","status","price","comment_client","comment_master","source","created_at","updated_at","google_event_id"],
    "config": ["key","value","description"],
    "conversations": ["id","client_id","message","assistant_reply","timestamp","source"],
}

# Some common renames from older schema -> canonical schema
RENAMES: Dict[str, Dict[str, str]] = {
    "bookings": {
        "slot_start": "datetime_start",
        "slot_end": "datetime_end",
        "client": "client_id",
        "master": "master_id",
    },
    "clients": {
        "mobile": "phone",
    }
}


def migrate_sheet_to_schema(sheets_client, spreadsheet_id: str, sheet_name: str) -> Dict[str, int]:
    """Normalize a single sheet to expected schema: returns a dict with counts of processed rows.

    Steps:
    - read existing rows
    - map headers to expected headers using `RENAMES` if necessary
    - build rows matching expected headers order
    - write header + rows (overwrite)
    """
    logger.info("Starting migration for sheet %s", sheet_name)
    if sheet_name not in EXPECTED_HEADERS:
        raise ValueError(f"Unknown sheet: {sheet_name}")

    expected = EXPECTED_HEADERS[sheet_name]
    rows = []
    try:
        existing = sheets_client.read_sheet(spreadsheet_id, sheet_name)
    except Exception as e:
        # sheet may not exist — just create a header and return
        logger.info("Sheet %s doesn't exist; creating header only", sheet_name)
        sheets_client.service_sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A1:Z1",
            valueInputOption="RAW", body={"values": [expected]}
        ).execute()
        return {"rows_written": 0}

    # existing is a list of dicts mapping header->value
    count = 0
    for r in existing:
        count += 1
        new_row = []
        for col in expected:
            # try direct match
            if col in r and r[col] is not None:
                new_row.append(r[col])
                continue
            # try rename mapping
            mapped = None
            if sheet_name in RENAMES:
                for old, new in RENAMES[sheet_name].items():
                    if new == col and old in r and r[old] is not None:
                        mapped = r[old]
                        break
            if mapped is not None:
                new_row.append(mapped)
            else:
                new_row.append(r.get(col, ""))
        rows.append(new_row)

    # Write header first then rows; we overwrite everything
    try:
        sheets_client.service_sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A1:Z1",
            valueInputOption="RAW", body={"values": [expected]}
        ).execute()
        if rows:
            sheets_client.service_sheets.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A2:Z{2+len(rows)}",
                valueInputOption="RAW", body={"values": rows}
            ).execute()
    except Exception as e:
        logger.exception("Failed to write normalized data for %s: %s", sheet_name, e)
        raise

    logger.info("Migrated %s rows for sheet %s", len(rows), sheet_name)
    return {"rows_written": len(rows)}


def migrate_spreadsheet(sheets_client, spreadsheet_id: str, sheet_names: List[str] | None = None) -> Dict[str, Dict[str, int]]:
    """Migrate multiple sheets in the spreadsheet. If sheet_names is None, migrate all expected sheets."""
    results = {}
    to_migrate = sheet_names or list(EXPECTED_HEADERS.keys())
    for s in to_migrate:
        try:
            res = migrate_sheet_to_schema(sheets_client, spreadsheet_id, s)
            results[s] = {"ok": True, **res}
        except Exception as e:
            logger.exception("Migration failed for %s: %s", s, e)
            results[s] = {"ok": False, "error": str(e)}
    return results
