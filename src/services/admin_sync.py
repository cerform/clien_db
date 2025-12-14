"""Sync utilities to keep admin IDs in sync between Cloud SQL and Sheets config."""
from typing import List, Optional, Dict
import logging

from src.db.cloudsql_client import get_cloudsql_client
from src.db.sheets_client import SheetsClient
from src.db.repositories.config_repo import ConfigRepo

logger = logging.getLogger(__name__)


def _fetch_admin_ids_from_sql(cloudsql_client) -> List[int]:
    """Query Cloud SQL for masters with role='admin' and return distinct telegram IDs."""
    queries = [
        "SELECT telegram_id FROM masters WHERE role = 'admin' AND is_active = TRUE",
        # Fallback if role column doesn't exist - read any telegram_id marked active
        "SELECT telegram_id FROM masters WHERE telegram_id IS NOT NULL AND is_active = TRUE",
        # Last resort: select any telegram_id
        "SELECT telegram_id FROM masters WHERE telegram_id IS NOT NULL"
    ]
    import os
    try:
        # Allow a custom SQL query via env var for bespoke DB schemas
        custom_q = os.getenv('ADMIN_SYNC_SQL')
        if custom_q:
            try:
                rows = cloudsql_client.execute_query(custom_q)
            except Exception as e:
                logger.exception(f"Custom ADMIN_SYNC_SQL query failed: {e}")
                rows = []
            ids = []
            for r in rows:
                tid = r.get('telegram_id') if isinstance(r, dict) else r[0]
                try:
                    ids.append(int(tid))
                except Exception:
                    logger.debug(f"Skipping non-int telegram_id from custom query: {tid}")
            return sorted(set(ids))

        rows = []
        rows = []
        for q in queries:
            try:
                rows = cloudsql_client.execute_query(q)
                if rows:
                    break
            except Exception as e:
                logger.debug(f"Query failed: {q} -> {e}")

        ids = []
        for r in rows:
            tid = r.get('telegram_id') if isinstance(r, dict) else r[0]
            if tid is None:
                continue
            try:
                ids.append(int(tid))
            except Exception:
                logger.warning(f"Skipping invalid telegram_id from DB: {tid}")
        # deduplicate and sort
        unique = sorted(set(ids))
        return unique
    except Exception as e:
        logger.exception(f"Failed to fetch admin ids from SQL: {e}")
        return []


def _fetch_admin_ids_from_sheets(spreadsheet_id: str) -> List[int]:
    """Fallback: read masters sheet from Google Sheets and extract telegram_id for admins."""
    try:
        sc = SheetsClient()
        rows = sc.read_sheet(spreadsheet_id, 'masters')
        ids = []
        for r in rows:
            role = str(r.get('role') or '').lower()
            if 'admin' in role:
                tid = r.get('telegram_id')
                try:
                    ids.append(int(tid))
                except Exception:
                    logger.debug(f"Skipping non-int telegram_id in sheets: {tid}")
        unique = sorted(set(ids))
        return unique
    except Exception as e:
        logger.exception(f"Failed to fetch admin ids from sheets: {e}")
        return []


def sync_admins_to_sheet(spreadsheet_id: str, cloudsql_client=None, sheets_client=None) -> Dict[str, object]:
    """Sync admin IDs from Cloud SQL masters table into the Sheets config key `ADMIN_USER_IDS`.

    Returns a dict with sync results.
    """
    if cloudsql_client is None:
        cloudsql_client = get_cloudsql_client()

    admin_ids = _fetch_admin_ids_from_sql(cloudsql_client)

    # If SQL returned nothing, fall back to reading masters from Sheets
    if not admin_ids:
        try:
            admin_ids = _fetch_admin_ids_from_sheets(spreadsheet_id)
        except Exception:
            pass

    csv_val = ",".join(str(i) for i in admin_ids)

    if sheets_client is None:
        sheets_client = SheetsClient()

    try:
        repo = ConfigRepo(sheets_client, spreadsheet_id)
        repo.set("ADMIN_USER_IDS", csv_val, "Synced from Cloud SQL masters table")
        return {"ok": True, "admin_ids": admin_ids, "csv": csv_val}
    except Exception as e:
        logger.exception(f"Failed to write ADMIN_USER_IDS to sheet: {e}")
        return {"ok": False, "error": str(e), "admin_ids": admin_ids}


__all__ = ["sync_admins_to_sheet", "_fetch_admin_ids_from_sql"]
