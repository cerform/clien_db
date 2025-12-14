"""Audit logging utilities for DB Admin actions."""
from typing import Dict, Any, List
import datetime
from datetime import timezone
import json
import logging

from src.db.sheets_client import SheetsClient
from src.db.schemas import build_row, pad_row_to_headers

logger = logging.getLogger(__name__)

AUDIT_SHEET = 'audit_log'


def append_audit_entry(spreadsheet_id: str, user_id: int, user_name: str, sheet: str, row_id: str, action: str, before: Dict[str, Any], after: Dict[str, Any]):
    sc = SheetsClient()
    ts = datetime.datetime.now(timezone.utc).isoformat()
    values = {
        'timestamp': ts,
        'user_id': str(user_id) if user_id is not None else '',
        'user_name': user_name or '',
        'sheet': sheet,
        'row_id': str(row_id),
        'action': action,
        'before': json.dumps(before or {}),
        'after': json.dumps(after or {})
    }
    row = build_row('audit_log', values)
    row = pad_row_to_headers('audit_log', row)
    try:
        sc.append_row(spreadsheet_id, AUDIT_SHEET, row)
    except Exception as e:
        logger.exception(f"Failed to write audit log: {e}")


def list_audit_for_row(spreadsheet_id: str, sheet: str, row_id: str, offset: int = 0, limit: int = 50) -> list:
    """Return a (possibly paginated) list of audit entries for a sheet row.

    Returns a list of matching rows (unpaginated by default); keep signature compatible with older callers/tests that expect a list.
    """
    sc = SheetsClient()
    rows = sc.read_sheet(spreadsheet_id, AUDIT_SHEET)
    res = [r for r in rows if r.get('sheet') == sheet and str(r.get('row_id')) == str(row_id)]
    if offset or limit:
        return res[offset: offset + limit]
    return res


def get_latest_audit_for_row(spreadsheet_id: str, sheet: str, row_id: str) -> Dict[str, Any]:
    rows = list_audit_for_row(spreadsheet_id, sheet, row_id)
    if not rows:
        return {}
    # Rows are appended; return last
    return rows[-1]
