"""Helpers for generic sheet row operations used by the DB Admin UI/API."""
from typing import List, Dict, Any, Optional
import logging

from src.db.sheets_client import SheetsClient
from src.db.schemas import headers_for, build_row, pad_row_to_headers
# Import get_config lazily inside functions to avoid importing google.cloud at module import time

logger = logging.getLogger(__name__)


def _get_spreadsheet_id() -> str:
    from src.core.config_manager import get_config
    cfg = get_config()
    return cfg.get('spreadsheet_id')


def list_rows(sheet_name: str) -> List[Dict[str, Any]]:
    sid = _get_spreadsheet_id()
    sc = SheetsClient()
    return sc.read_sheet(sid, sheet_name)


def find_row_index_by_id(rows: List[Dict[str, Any]], row_id: str) -> Optional[int]:
    for idx, r in enumerate(rows, start=1):
        if str(r.get('id')) == str(row_id):
            return idx
    return None


def get_row(sheet_name: str, row_id: str) -> Optional[Dict[str, Any]]:
    rows = list_rows(sheet_name)
    for r in rows:
        if str(r.get('id')) == str(row_id):
            return r
    return None


def update_row(sheet_name: str, row_id: str, values: Dict[str, Any]) -> bool:
    sid = _get_spreadsheet_id()
    sc = SheetsClient()
    rows = sc.read_sheet(sid, sheet_name)
    idx = find_row_index_by_id(rows, row_id)
    if idx is None:
        return False
    # Build new row based on headers ordering
    headers = list(rows[0].keys()) if rows else list(values.keys())
    new_row = [values.get(h, rows[idx-1].get(h, "")) for h in headers]
    sc.update_row(sid, sheet_name, idx, new_row)
    return True


def append_row(sheet_name: str, values: Dict[str, Any]) -> Dict[str, Any]:
    sid = _get_spreadsheet_id()
    sc = SheetsClient()
    # If we have a canonical header for the sheet, use build_row to align columns
    hdrs = headers_for(sheet_name)
    if hdrs:
        row = build_row(sheet_name, values)
        row = pad_row_to_headers(sheet_name, row)
    else:
        # fallback: append values in key order
        row = [values.get(k, "") for k in values.keys()]
    sc.append_row(sid, sheet_name, row)
    return values


def delete_row(sheet_name: str, row_id: str) -> bool:
    sid = _get_spreadsheet_id()
    sc = SheetsClient()
    rows = sc.read_sheet(sid, sheet_name)
    idx = find_row_index_by_id(rows, row_id)
    if idx is None:
        return False
    blank_row = ['' for _ in range(len(rows[0]))]
    sc.update_row(sid, sheet_name, idx, blank_row)
    return True


__all__ = [
    'list_rows', 'get_row', 'update_row', 'append_row', 'delete_row', 'find_row_index_by_id'
]
