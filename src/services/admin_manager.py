"""
AdminManager service - manage admin IDs and store them in Google Sheets config.
This provides `get_admin_ids`, `is_admin`, `grant_admin`, and `revoke_admin`.
"""
import logging
from typing import List

from src.config.config import Config
from src.db.sheets_client import SheetsClient
from src.db.repositories.config_repo import ConfigRepo
from src.config.env_loader import load_env

logger = logging.getLogger(__name__)


def _parse_csv_ids(csv_value: str) -> List[int]:
    if not csv_value:
        return []
    ids = []
    for part in csv_value.split(","):
        p = part.strip()
        if p:
            try:
                ids.append(int(p))
            except Exception:
                logger.warning(f"Invalid admin id in config: {p}")
    return ids


def get_admin_ids() -> List[int]:
    """Return combined admin IDs from env and config sheet."""
    load_env()
    cfg = Config.from_env()
    ids_env = list(cfg.ADMIN_USER_IDS) if cfg.ADMIN_USER_IDS else []

    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        from src.services.google_sheets_initializer import ensure_sheets_structure
        ensure_sheets_structure(sc, cfg.SPREADSHEET_ID)
        repo = ConfigRepo(sc, cfg.SPREADSHEET_ID)
        entry = repo.get("ADMIN_USER_IDS")
        ids_sheet = _parse_csv_ids(entry.get("value", "")) if entry else []
        combined = list(sorted(set(ids_env + ids_sheet)))
        return combined
    except Exception as e:
        logger.warning(f"Failed to read admin IDs from sheet: {e}")
        return ids_env


def is_admin(user_id: int) -> bool:
    return user_id in get_admin_ids()


def grant_admin(new_admin_id: int) -> bool:
    """Add admin ID to sheet config; returns True on success."""
    load_env()
    cfg = Config.from_env()
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        repo = ConfigRepo(sc, cfg.SPREADSHEET_ID)
        # Read existing
        entry = repo.get("ADMIN_USER_IDS")
        if entry:
            existing_ids = _parse_csv_ids(entry.get("value", ""))
        else:
            existing_ids = []
        if new_admin_id in existing_ids:
            return True
        existing_ids.append(new_admin_id)
        csv_val = ",".join(str(i) for i in existing_ids)
        repo.set("ADMIN_USER_IDS", csv_val, "Comma-separated admin telegram IDs")
        return True
    except Exception as e:
        logger.exception(f"Failed to grant admin: {e}")
        return False


def revoke_admin(admin_id: int) -> bool:
    """Remove admin ID from sheet config; returns True on success."""
    load_env()
    cfg = Config.from_env()
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        from src.services.google_sheets_initializer import ensure_sheets_structure
        ensure_sheets_structure(sc, cfg.SPREADSHEET_ID)
        repo = ConfigRepo(sc, cfg.SPREADSHEET_ID)
        entry = repo.get("ADMIN_USER_IDS")
        if not entry:
            return False
        existing_ids = _parse_csv_ids(entry.get("value", ""))
        if admin_id not in existing_ids:
            return True
        existing_ids = [i for i in existing_ids if i != admin_id]
        csv_val = ",".join(str(i) for i in existing_ids)
        repo.set("ADMIN_USER_IDS", csv_val, "Comma-separated admin telegram IDs")
        return True
    except Exception as e:
        logger.exception(f"Failed to revoke admin: {e}")
        return False


__all__ = ["get_admin_ids", "is_admin", "grant_admin", "revoke_admin"]
