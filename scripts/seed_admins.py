#!/usr/bin/env python3
"""Seed admin users into the database (masters table) based on ADMIN_USER_IDS env variable"""
import os
import sys
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from sqlalchemy import text
from src.db.cloudsql_client import init_cloudsql_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_admin_list_from_env():
    raw = os.getenv('ADMIN_USER_IDS', '')
    ids = [x.strip() for x in raw.split(',') if x.strip()]
    return ids

def main():
    admin_ids = get_admin_list_from_env()
    if not admin_ids:
        logger.error('No ADMIN_USER_IDS provided in environment; set ADMIN_USER_IDS as comma-separated list')
        return 1
    client = init_cloudsql_client()
    engine = client.get_engine()
    with engine.connect() as conn:
        for aid in admin_ids:
            try:
                # Put in masters table as role=admin
                stmt = text("INSERT INTO masters (telegram_id, name, role, is_active) VALUES (:tid, :name, :role, true) ON CONFLICT (telegram_id) DO UPDATE SET is_active = TRUE, role = EXCLUDED.role")
                conn.execute(stmt, {"tid": int(aid), "name": f"Admin {aid}", "role": "admin"})
                logger.info(f"Inserted/Updated admin user: {aid}")
            except Exception as e:
                logger.warning(f"Failed to insert admin {aid}: {e}")
    logger.info('Admin seeding complete')
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
