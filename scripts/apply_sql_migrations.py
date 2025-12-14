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
    dry_run = not apply
    files = sorted(glob.glob(str(MIGRATIONS_DIR / '*.sql')))
    if not files:
        logger.warning('No SQL migration files found')
        return
    with engine.begin() as conn:
        for f in files:
            logger.info('Processing migration: %s', f)
            sql_text = Path(f).read_text(encoding='utf-8')
            if dry_run:
                logger.info('[DRY RUN] Would apply migration: %s', f)
                logger.debug(sql_text)
            else:
                try:
                    conn.execute(text(sql_text))
                    logger.info('Applied migration: %s', f)
                except Exception as e:
                    logger.error('Failed to apply migration %s: %s', f, e)
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
