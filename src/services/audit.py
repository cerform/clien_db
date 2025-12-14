"""Audit logging utilities for DB Admin actions."""
from typing import Dict, Any, List
import datetime
import json
import logging

from src.db.sheets_client import SheetsClient

logger = logging.getLogger(__name__)

AUDIT_SHEET = 'audit_log'


def append_audit_entry(spreadsheet_id: str, user_id: int, user_name: str, sheet: str, row_id: str, action: str, before: Dict[str, Any], after: Dict[str, Any]):
    sc = SheetsClient()
    ts = datetime.datetime.utcnow().isoformat()
    payload = [ts, str(user_id) if user_id is not None else '', user_name or '', sheet, str(row_id), action, json.dumps(before or {}), json.dumps(after or {})]
    try:
        sc.append_row(spreadsheet_id, AUDIT_SHEET, payload)
    except Exception as e:
        logger.exception(f"Failed to write audit log: {e}")


def list_audit_for_row(spreadsheet_id: str, sheet: str, row_id: str, offset: int = 0, limit: int = 50) -> Dict[str, Any]:
    """Return paginated audit entries for a sheet row.

    Returns dict: {total: int, items: List[dict]}
    """
    sc = SheetsClient()
    rows = sc.read_sheet(spreadsheet_id, AUDIT_SHEET)
    res = [r for r in rows if r.get('sheet') == sheet and str(r.get('row_id')) == str(row_id)]
    total = len(res)
    items = res[offset: offset + limit]
    return {'total': total, 'items': items}


def get_latest_audit_for_row(spreadsheet_id: str, sheet: str, row_id: str) -> Dict[str, Any]:
    rows = list_audit_for_row(spreadsheet_id, sheet, row_id)
    if not rows:
        return {}
    # Rows are appended; return last
    return rows[-1]
