#!/usr/bin/env python3
"""
Migrate data currently in Google Sheets to a SQL database (Cloud SQL / Postgres / MySQL)

This script performs the following steps:
- Reads data from existing sheets (Masters, Services, Clients, Bookings, Расписание, Admin_Audit_Log, INKA_Training)
- Creates equivalent SQL tables using SQLAlchemy models
- Bulk inserts rows into SQL tables, preserving IDs and timestamps

Use with environment variable DATABASE_URL (e.g. postgresql://user:pass@host:5432/dbname)
Or pass --database-url as an argument.
"""
import argparse
import logging
import os
from src.db.sql_client import SQLClient
from src.db.sheets_client import GoogleSheetsClient
from src.config.config import get_config

logger = logging.getLogger(__name__)


def map_masters(rows):
    # rows is a list of lists; first row may be headers
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    out = []
    for r in rows[1:]:
        out.append({
            'id': r[0] if len(r) > 0 else None,
            'name': r[1] if len(r) > 1 else None,
            'phone': r[2] if len(r) > 2 else None,
            'telegram_id': r[3] if len(r) > 3 else None,
            'specialization': r[4] if len(r) > 4 else None,
            'rating': r[5] if len(r) > 5 else '0',
            'experience': r[6] if len(r) > 6 else None,
            'instagram': r[7] if len(r) > 7 else None,
            'status': r[8] if len(r) > 8 else 'active',
            'bio': r[9] if len(r) > 9 else None,
            'calendar_id': r[10] if len(r) > 10 else None,
        })
    return out


def map_services(rows):
    if not rows or len(rows) < 2:
        return []
    out = []
    for r in rows[1:]:
        out.append({
            'id': r[0] if len(r) > 0 else None,
            'name': r[1] if len(r) > 1 else None,
            'description': r[2] if len(r) > 2 else None,
            'duration_min': r[3] if len(r) > 3 else None,
            'price_from': r[4] if len(r) > 4 else None,
            'price_to': r[5] if len(r) > 5 else None,
            'category': r[6] if len(r) > 6 else None,
            'active': r[7] if len(r) > 7 else 'TRUE'
        })
    return out


def map_clients(rows):
    if not rows or len(rows) < 2:
        return []
    out = []
    for r in rows[1:]:
        out.append({
            'id': r[0] if len(r) > 0 else None,
            'telegram_id': r[1] if len(r) > 1 else None,
            'name': r[2] if len(r) > 2 else None,
            'phone': r[3] if len(r) > 3 else None,
            'email': r[4] if len(r) > 4 else None,
            'notes': r[5] if len(r) > 5 else None,
            'created_at': r[6] if len(r) > 6 else None,
            'last_visit': r[7] if len(r) > 7 else None,
        })
    return out


def map_bookings(rows):
    if not rows or len(rows) < 2:
        return []
    out = []
    for r in rows[1:]:
        out.append({
            'id': r[0] if len(r) > 0 else None,
            'client_id': r[1] if len(r) > 1 else None,
            'master_id': r[2] if len(r) > 2 else None,
            'service_id': r[3] if len(r) > 3 else None,
            'date': r[4] if len(r) > 4 else None,
            'time': r[5] if len(r) > 5 else None,
            'duration_min': r[6] if len(r) > 6 else None,
            'price': r[7] if len(r) > 7 else None,
            'status': r[8] if len(r) > 8 else None,
            'notes': r[9] if len(r) > 9 else None,
            'created_at': r[10] if len(r) > 10 else None,
        })
    return out


def map_schedule(rows):
    if not rows or len(rows) < 2:
        return []
    out = []
    for r in rows[1:]:
        out.append({
            'id': r[0] if len(r) > 0 else None,
            'master_id': r[1] if len(r) > 1 else None,
            'day_of_week': r[2] if len(r) > 2 else None,
            'start_time': r[3] if len(r) > 3 else None,
            'end_time': r[4] if len(r) > 4 else None,
            'is_working': r[5] if len(r) > 5 else 'true',
            'break_start': r[6] if len(r) > 6 else None,
            'break_end': r[7] if len(r) > 7 else None,
            'notes': r[8] if len(r) > 8 else None,
        })
    return out


def map_audit(rows):
    if not rows or len(rows) < 2:
        return []
    out = []
    for r in rows[1:]:
        out.append({
            'timestamp': r[0] if len(r) > 0 else None,
            'admin_id': r[1] if len(r) > 1 else None,
            'action': r[2] if len(r) > 2 else None,
            'sheet': r[3] if len(r) > 3 else None,
            'details': r[4] if len(r) > 4 else None,
        })
    return out


def map_training(rows):
    if not rows or len(rows) < 2:
        return []
    out = []
    for r in rows[1:]:
        out.append({
            'id': r[0] if len(r) > 0 else None,
            'timestamp': r[1] if len(r) > 1 else None,
            'category': r[2] if len(r) > 2 else None,
            'user_input': r[3] if len(r) > 3 else None,
            'inka_response': r[4] if len(r) > 4 else None,
            'admin_correction': r[5] if len(r) > 5 else None,
            'improvement': r[6] if len(r) > 6 else 'no',
            'tags': r[7] if len(r) > 7 else None,
            'status': r[8] if len(r) > 8 else 'active'
        })
    return out


def main():
    parser = argparse.ArgumentParser(description="Migrate Google Sheets DB to Cloud SQL")
    parser.add_argument('--database-url', help='DATABASE_URL for SQLAlchemy connection', default=os.getenv('DATABASE_URL'))
    parser.add_argument('--confirm', action='store_true', help='Apply changes; omit for dry-run')
    args = parser.parse_args()

    config = get_config()
    creds_path = getattr(config, 'google_credentials_json', 'credentials.json')
    spreadsheet_id = getattr(config, 'google_spreadsheet_id', None)

    if not spreadsheet_id:
        raise SystemExit('GOOGLE_SPREADSHEET_ID not set in config or env')

    sheets_client = GoogleSheetsClient(credentials_file=creds_path, spreadsheet_id=spreadsheet_id)
    sql_client = SQLClient(database_url=args.database_url)

    # Read sheets and map
    masters_rows = sheets_client.get_sheet_values('Masters')
    services_rows = sheets_client.get_sheet_values('Services')
    clients_rows = sheets_client.get_sheet_values('Clients')
    bookings_rows = sheets_client.get_sheet_values('Bookings')
    schedule_rows = sheets_client.get_sheet_values('Расписание')
    audit_rows = sheets_client.get_sheet_values('Admin_Audit_Log')
    training_rows = sheets_client.get_sheet_values('INKA_Training')

    masters = map_masters(masters_rows)
    services = map_services(services_rows)
    clients = map_clients(clients_rows)
    bookings = map_bookings(bookings_rows)
    schedule = map_schedule(schedule_rows)
    audit = map_audit(audit_rows)
    training = map_training(training_rows)

    if not args.confirm:
        logger.info("Dry run mode: no changes will be made. Use --confirm to apply.")
        logger.info(f"Masters to import: {len(masters)}")
        logger.info(f"Services to import: {len(services)}")
        logger.info(f"Clients to import: {len(clients)}")
        logger.info(f"Bookings to import: {len(bookings)}")
        logger.info(f"Schedule rows to import: {len(schedule)}")
        logger.info(f"Audit logs to import: {len(audit)}")
        logger.info(f"Training examples to import: {len(training)}")
        return

    # Create tables
    sql_client.create_tables()
    # Bulk insert in order to maintain referential integrity
    sql_client.bulk_insert_masters(masters)
    sql_client.bulk_insert_services(services)
    sql_client.bulk_insert_clients(clients)
    sql_client.bulk_insert_bookings(bookings)
    sql_client.bulk_insert_schedule(schedule)
    sql_client.bulk_insert_audit_logs(audit)
    sql_client.bulk_insert_training(training)

    logger.info("✅ Migration completed successfully")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
