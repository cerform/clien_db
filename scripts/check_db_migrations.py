#!/usr/bin/env python3
"""Check whether the DB schema tables exist and report missing ones."""
import logging
from src.db.cloudsql_client import init_cloudsql_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUIRED_TABLES = [
    'clients', 'masters', 'services', 'bookings', 'calendar_slots', 'conversation_history'
]

def main():
    client = init_cloudsql_client()
    engine = client.get_engine()
    missing = []
    with engine.connect() as conn:
        for t in REQUIRED_TABLES:
            try:
                res = conn.execute(f"SELECT to_regclass('{t}') as reg").fetchone()
                if res is None or res[0] is None:
                    missing.append(t)
            except Exception as e:
                logger.warning(f"Failed to check table {t}: {e}")
                missing.append(t)
    if missing:
        logger.error(f"Missing tables: {missing}")
        return 1
    logger.info("All required tables present")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
