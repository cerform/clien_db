#!/usr/bin/env python3
"""
Create RBAC roles in Postgres and grant required privileges for INKA microservices.

This script runs SQL statements that create roles (login users) and apply
GRANT/REVOKE rules for the predefined roles:
  - inka_llm_runtime
  - inka_booking_agent
  - inka_learning_agent
  - calendar_sync

Passwords are optionally set from environment variables. If no password is
provided, the script will not set or change a password (good for IAM / secret
managed deployments).

Usage:
  export DATABASE_URL=postgresql://admin:secret@localhost:5432/tattoo_salon
  export RBAC_INKA_LLM_RUNTIME_PASS=supersecret
  export RBAC_INKA_BOOKING_AGENT_PASS=bookingpass
  python3 scripts/create_rbac_roles.py --apply

Or run without --apply to perform a dry-run.
"""
import os
import argparse
import sqlalchemy
from sqlalchemy import text
from dotenv import load_dotenv
from getpass import getpass
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    logger.error("DATABASE_URL must be set in env")
    sys.exit(1)

ROLE_PASSWORDS = {
    'inka_llm_runtime': os.getenv('RBAC_INKA_LLM_RUNTIME_PASS'),
    'inka_booking_agent': os.getenv('RBAC_INKA_BOOKING_AGENT_PASS'),
    'inka_learning_agent': os.getenv('RBAC_INKA_LEARNING_AGENT_PASS'),
    'calendar_sync': os.getenv('RBAC_CALENDAR_SYNC_PASS'),
}


def run_sql(conn, sql, params=None, dry_run=False):
    if dry_run:
        logger.info('[DRY] SQL to run:\n%s', sql)
        return
    conn.execute(text(sql), params or {})


def apply_roles(engine, apply=False):
    dry_run = not apply
    with engine.begin() as conn:
        # Create roles without passwords (safer if using secrets manager)
        for role, pwd in ROLE_PASSWORDS.items():
            sql = f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{role}') THEN CREATE ROLE {role} NOINHERIT; END IF; END$$;"
            run_sql(conn, sql, dry_run=dry_run)
            if pwd:
                # alter role to set login and password
                sql2 = f"ALTER ROLE {role} WITH LOGIN PASSWORD :pwd;"
                run_sql(conn, sql2, params={'pwd': pwd}, dry_run=dry_run)

        # Apply grants and revokes
        grants = [
            "GRANT SELECT ON services, masters_public, availability_view TO inka_llm_runtime;",
            "REVOKE INSERT, UPDATE, DELETE ON bookings, calendar_events FROM inka_llm_runtime;",
            "GRANT INSERT ON bookings_pending, slot_locks TO inka_booking_agent;",
            "GRANT SELECT ON availability_view, calendar_events TO inka_booking_agent;",
            "GRANT SELECT, INSERT, UPDATE ON learning_rules, learning_faq, learning_style TO inka_learning_agent;",
            "GRANT INSERT, UPDATE ON calendar_events TO calendar_sync;",
            "GRANT SELECT ON calendar_sources TO calendar_sync;",
        ]
        for g in grants:
            run_sql(conn, g, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply changes to DB. Default is dry-run.')
    args = parser.parse_args()

    engine = sqlalchemy.create_engine(DATABASE_URL)
    apply_roles(engine, apply=args.apply)
    if args.apply:
        logger.info('RBAC roles created/updated successfully.')
    else:
        logger.info('Dry run complete. Nothing was changed. Use --apply to apply changes.')


if __name__ == '__main__':
    main()
