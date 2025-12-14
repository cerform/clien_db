import os
import json
from typing import Dict, Any
from google.cloud import secretmanager
from google.api_core.exceptions import NotFound

CONFIG_SHEET = os.getenv("CONFIG_SHEET_ID")
GCP_PROJECT = os.getenv("GCP_PROJECT_ID")

def _get_secret_client():
    return secretmanager.SecretManagerServiceClient()

def get_secret(secret_id: str) -> str | None:
    """Get secret from Google Secret Manager. Return None if not set.

    Fall back to environment variable or local config.
    """
    # Check environment first (local dev convenience)
    env_val = os.getenv(secret_id)
    if env_val:
        return env_val
    client = _get_secret_client()
    name = f"projects/{GCP_PROJECT}/secrets/{secret_id}/versions/latest"
    try:
        resp = client.access_secret_version(request={"name": name})
        return resp.payload.data.decode("UTF-8")
    except NotFound:
        return None
    except Exception:
        # swallow for now and return None
        return None

def set_secret(secret_id: str, value: str) -> None:
    client = _get_secret_client()
    parent = f"projects/{GCP_PROJECT}"
    secret_name = f"{parent}/secrets/{secret_id}"
    try:
        # Try to create secret; if exists, ignore
        client.create_secret(parent=parent, secret_id=secret_id, secret={"replication": {"automatic": {}}})
    except Exception:
        pass
    # Add a new version
    client.add_secret_version(parent=secret_name, payload={"data": value.encode()})


def get_config() -> Dict[str, Any]:
    """Returns aggregated config from local file and optionally configuration sheet.

    Priorities: environment variables -> secret manager / local file -> sheet-based config (TODO).
    """
    cfg = {}
    if os.path.exists("config.json"):
        with open("config.json", encoding="utf-8") as f:
            try:
                cfg = json.load(f)
            except Exception:
                cfg = {}
    # Merge env vars specific to this app
    # Allow overriding via env
    for key in ["GCP_PROJECT_ID", "SPREADSHEET_ID", "TELEGRAM_BOT_TOKEN", "LLM_API_KEY"]:
        v = os.getenv(key)
        if v:
            cfg[key.lower()] = v
    # Optionally read config from Google Sheet if available
    # Note: This requires a SheetsClient to call get_config_from_sheet explicitly; we do not attempt to load it automatically here.
    return cfg


def save_config(data: Dict[str, Any]) -> None:
    """Save configuration locally and distribute secrets to Secret Manager.

    The function separates secrets (LLM keys, Telegram tokens) and saves them in Secret Manager, while keeping non-secrets in `config.json`.
    """
    os.makedirs(os.path.dirname("config.json") or ".", exist_ok=True)
    # Extract secrets
    secrets = {}
    # Map local keys to canonical Secret Manager names
    secret_map = {"telegram_token": "TELEGRAM_BOT_TOKEN", "llm_api_key": "LLM_API_KEY"}
    for k, secret_name in secret_map.items():
        if k in data:
            secrets[secret_name] = data.pop(k)
    # Load existing config and merge non-secret fields to avoid overwriting
    existing = {}
    if os.path.exists("config.json"):
        try:
            with open("config.json", encoding='utf-8') as f:
                existing = json.load(f) or {}
        except Exception:
            existing = {}
    existing.update({k: v for k, v in data.items() if k not in secret_map})
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    # Save secrets to Secret Manager
    for secret_name, secret_value in secrets.items():
        set_secret(secret_name, secret_value)


def save_config_to_sheet(sheets_client, spreadsheet_id: str, data: Dict[str, Any]) -> None:
    """Saves non-secret configuration values to 'config' sheet in the spreadsheet.

    sheets_client should provide `append_row` or `update_row` methods; expected schema: key,value,description
    """
    if not spreadsheet_id:
        return
    # Convert to key/value rows
    rows = [[k, v, "saved_by_installer"] for k, v in data.items()]
    # Clear existing config and append new items simply by writing header and rows - simple and safe.
    try:
        sheets_client.service_sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range="config!A1:Z1",
            valueInputOption="RAW", body={"values": [["key", "value", "description"]]}
        ).execute()
        for row in rows:
            sheets_client.append_row(spreadsheet_id, "config", row)
    except Exception:
        # failing silently for now; sheet might not exist
        pass


def load_config_from_sheet(sheets_client, spreadsheet_id: str) -> Dict[str, Any]:
    """Load configuration from 'config' sheet as key/value pairs; returns a dict."""
    if not spreadsheet_id:
        return {}
    try:
        resp = sheets_client.read_sheet(spreadsheet_id, "config")
        cfg = {r.get("key"): r.get("value") for r in resp if r.get("key")}
        return cfg
    except Exception:
        return {}


def is_configured() -> bool:
    cfg = get_config()
    return bool(cfg.get("setup_complete") or cfg.get("setup_complete") is True)


def is_force_sheet_mode() -> bool:
    """Return True if predeploy indicates we should force sheet-backed mode (no mock fallbacks)."""
    cfg = get_config()
    v = cfg.get('force_sheet_mode')
    if v is True:
        return True
    if isinstance(v, str) and v.lower() in ('1', 'true', 'yes'):
        return True
    # fallback to env var
    ev = os.getenv('FORCE_SHEET_MODE')
    if ev and ev.lower() in ('1', 'true', 'yes'):
        return True
    return False
