#!/usr/bin/env python3
"""Parse credentials from a Google Sheet and (optionally) store them in Secret Manager.

Expected format: sheet named "config" with rows: key | value | description

Usage:
  python scripts/parse_sheets_creds.py --project tattoo-480007 --sheet-id 1o-ipgcRgc6o4Gf0rcatcU9gky56UefS5_lx-df2KjCE --update-secrets --dry-run

This script will:
  - Read `config` sheet using `SheetsClient`
  - For each row, extract `key` and `value`
  - If --update-secrets is passed, create or add a new version to the secret with that name

Be careful: secrets will be created/updated in the provided project.
"""

import argparse
import logging
import sys
from typing import Dict, Any

from src.db.sheets_client import SheetsClient

logger = logging.getLogger("parse_sheets_creds")


def read_config_sheet(sheet_id: str) -> Dict[str, str]:
    sc = SheetsClient()
    try:
        rows = sc.read_sheet(sheet_id, "config")
    except Exception as e:
        # If sheet not found raise clear error
        logger.exception("Failed to read 'config' sheet: %s", e)
        raise

    kv = {}
    # Expect rows to be dictionaries with 'key' and 'value' columns
    for r in rows:
        k = r.get("key") or r.get("Key") or r.get("KEY")
        v = r.get("value") or r.get("Value") or r.get("VALUE")
        if k and v:
            kv[str(k).strip()] = str(v).strip()
    return kv


def ensure_secret(project: str, name: str, payload: str, dry_run: bool = True):
    """Create or add a version to secret `name` in given project with payload."""
    try:
        from google.cloud import secretmanager
    except Exception as e:
        logger.error("google-cloud-secretmanager library not available: %s", e)
        raise

    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project}"

    # Check if secret exists
    secret_name = f"projects/{project}/secrets/{name}"
    try:
        client.get_secret(request={"name": secret_name})
        exists = True
    except Exception:
        exists = False

    if dry_run:
        if exists:
            logger.info("[dry-run] Would add new version to secret: %s", name)
        else:
            logger.info("[dry-run] Would create secret and add version: %s", name)
        return

    if not exists:
        logger.info("Creating secret: %s", name)
        client.create_secret(request={
            "parent": parent,
            "secret_id": name,
            "secret": {"replication": {"automatic": {}}}
        })

    logger.info("Adding secret version for: %s", name)
    client.add_secret_version(request={
        "parent": secret_name,
        "payload": {"data": payload.encode('utf-8')}
    })


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="GCP project id")
    parser.add_argument("--sheet-id", required=False, help="Google Spreadsheet ID (overrides env SPREADSHEET_ID)")
    parser.add_argument("--update-secrets", action="store_true", help="Create/update secrets in Secret Manager")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Don't actually modify secrets; just show what would be done")

    args = parser.parse_args(argv)

    # Determine sheet id
    sheet_id = args.sheet_id
    if not sheet_id:
        from src.config.config import Config
        cfg = Config.from_env()
        sheet_id = cfg.SPREADSHEET_ID

    if not sheet_id:
        logger.error("No sheet id provided and SPREADSHEET_ID is not set in env")
        sys.exit(2)

    try:
        creds = read_config_sheet(sheet_id)
    except Exception as e:
        logger.error("Failed to read config sheet: %s", e)
        sys.exit(1)

    logger.info("Found %d config entries", len(creds))

    # Filter for common secrets (but show all)
    secret_targets = ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN", "DATABASE_URL", "CLOUDSQL_PASSWORD", "BOT_TOKEN", "SPREADSHEET_ID"]

    for k, v in creds.items():
        tag = "(secret)" if k in secret_targets else ""
        logger.info("%s => %s %s", k, '<redacted>' if 'key' in k.lower() or 'token' in k.lower() or 'password' in k.lower() else v, tag)

    if args.update_secrets:
        for k in creds:
            if k.upper() in secret_targets:
                logger.info("Processing secret: %s", k)
                ensure_secret(args.project, k, creds[k], dry_run=args.dry_run)

    logger.info("Done")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
