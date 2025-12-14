"""Sheet schemas and helper functions to map dicts to ordered sheet rows

This module defines the canonical headers for each sheet and helpers to
build rows that conform to the sheet header order. Repositories should
use these helpers to ensure consistent column mapping.
"""
from typing import List, Dict
import datetime
from datetime import timezone

# Canonical headers for each Google Sheet used by the app.
SHEETS_HEADERS = {
    'clients': ['id', 'telegram_id', 'name', 'phone', 'email', 'notes', 'tags', 'created_at', 'last_visit'],
    'masters': ['id', 'name', 'specialization', 'rating', 'experience_years', 'instagram', 'status', 'telegram_id', 'calendar_id', 'notes'],
    'services': ['id', 'name', 'description', 'duration_min', 'price_from', 'price_to', 'category', 'active'],
    'bookings': ['id', 'client_id', 'master_id', 'service_id', 'datetime_start', 'datetime_end', 'status', 'price', 'comment_client', 'comment_master', 'source', 'created_at', 'updated_at', 'google_event_id'],
    'calendar': ['date', 'master_id', 'slot_start', 'slot_end', 'available', 'note'],
    'config': ['key', 'value', 'description'],
    'conversations': ['id', 'client_id', 'message', 'assistant_reply', 'timestamp', 'source']
    , 'audit_log': ['timestamp', 'user_id', 'user_name', 'sheet', 'row_id', 'action', 'before', 'after']
}


def headers_for(sheet_name: str) -> List[str]:
    return SHEETS_HEADERS.get(sheet_name, [])


def build_row(sheet_name: str, values: Dict[str, object]) -> List[object]:
    """Build an ordered row for a sheet from a dict of values.

    Missing keys are filled with empty strings. Timestamps default to ISO strings
    when appropriate (created_at/updated_at).
    """
    headers = headers_for(sheet_name)
    now = datetime.datetime.now(timezone.utc).isoformat()
    out = []
    for h in headers:
        if h in values and values[h] is not None:
            out.append(values[h])
        else:
            # sensible defaults
            if h == 'id':
                out.append(values.get('id', ''))
            elif h in ('created_at', 'timestamp'):
                out.append(values.get(h, now))
            elif h == 'updated_at':
                out.append(values.get(h, ''))
            else:
                out.append('')
    return out


def pad_row_to_headers(sheet_name: str, row: List[object]) -> List[object]:
    headers = headers_for(sheet_name)
    if len(row) >= len(headers):
        return row[:len(headers)]
    return row + [''] * (len(headers) - len(row))
