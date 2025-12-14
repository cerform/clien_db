#!/usr/bin/env python3
"""
Apply SQL migration files from db/migrations/sql in lexical order.
This script reads all .sql files from db/migrations/sql and executes them against DATABASE_URL.
Use this for DB provisioning in a simple environment (for production, use your preferred migration tool e.g. Alembic).
"""
import os
import glob
import argparse
import sqlalchemy
from sqlalchemy import text
from dotenv import load_dotenv
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    logger.error('DATABASE_URL must be set in env')
    sys.exit(1)

MIGRATIONS_DIR = Path(__file__).parent.parent / 'db' / 'migrations' / 'sql'


def apply_migrations(engine, apply=False):
    """Scan for migrations and apply if required"""
    dry_run = not apply
    files = sorted(glob.glob(str(MIGRATIONS_DIR / '*.sql')))
    if not files:
        logger.warning('No SQL migration files found')
        return
    for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        logger.info(f"Processing migration: {migration_file}")
        with open(migration_file, "r") as f:
            # Read whole file, do not split by ;
            sql_text = f.read()
            if not apply:
                logger.info(f"[DRY RUN] Would apply migration: {migration_file}")
                continue

            try:
                with engine.connect() as conn:
                    conn.execute(text(sql_text))
                    conn.commit()
                logger.info(f"Applied migration: {migration_file}")
            except Exception as e:
                logger.error(
                    f"Failed to apply migration {migration_file}: {e}"
                )
                # Exit on first failure
                raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply changes to DB. Default is dry-run.')
    args = parser.parse_args()
    engine = sqlalchemy.create_engine(DATABASE_URL)
    apply_migrations(engine, apply=args.apply)
    if args.apply:
        logger.info('All migrations applied successfully')
    else:
        logger.info('Dry-run complete')


if __name__ == '__main__':
    main()