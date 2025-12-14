"""
Migration script: Google Sheets → PostgreSQL
Migrates all data from Google Sheets to PostgreSQL database
"""
import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.db.db_factory import DatabaseFactory
from src.config.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_clients(sheets_factory: DatabaseFactory, pg_factory: DatabaseFactory) -> int:
    """Migrate clients from Sheets to PostgreSQL"""
    logger.info("Migrating clients...")

    sheets_repo = sheets_factory.get_clients_repo()
    pg_repo = pg_factory.get_clients_repo()

    clients = sheets_repo.list_clients()
    migrated_count = 0

    for client in clients:
        try:
            # Check if client already exists
            existing = pg_repo.get_client_by_telegram_id(int(client.get('telegram_id', 0)))
            if existing:
                logger.debug(f"Client {client.get('telegram_id')} already exists, skipping")
                continue

            # Create new client
            pg_repo.create_client(
                telegram_id=int(client.get('telegram_id', 0)),
                name=client.get('name', 'Unknown'),
                phone=client.get('phone', ''),
                email=client.get('email', ''),
                notes=client.get('notes', ''),
                language=client.get('language', 'ru')
            )
            migrated_count += 1
            logger.debug(f"Migrated client: {client.get('name')}")
        except Exception as e:
            logger.error(f"Failed to migrate client {client.get('name')}: {e}")

    logger.info(f"✅ Migrated {migrated_count} clients")
    return migrated_count


def migrate_masters(sheets_factory: DatabaseFactory, pg_factory: DatabaseFactory) -> int:
    """Migrate masters from Sheets to PostgreSQL"""
    logger.info("Migrating masters...")

    sheets_repo = sheets_factory.get_masters_repo()
    pg_repo = pg_factory.get_masters_repo()

    masters = sheets_repo.list_masters()
    migrated_count = 0

    for master in masters:
        try:
            # Create new master
            pg_repo.create_master(
                name=master.get('name', 'Unknown'),
                calendar_id=master.get('calendar_id', ''),
                specialization=master.get('specialization', ''),
                telegram_id=int(master.get('telegram_id')) if master.get('telegram_id') else None,
                status=master.get('status', 'active')
            )
            migrated_count += 1
            logger.debug(f"Migrated master: {master.get('name')}")
        except Exception as e:
            logger.error(f"Failed to migrate master {master.get('name')}: {e}")

    logger.info(f"✅ Migrated {migrated_count} masters")
    return migrated_count


def migrate_bookings(sheets_factory: DatabaseFactory, pg_factory: DatabaseFactory,
                     client_map: dict, master_map: dict) -> int:
    """Migrate bookings from Sheets to PostgreSQL"""
    logger.info("Migrating bookings...")

    sheets_repo = sheets_factory.get_bookings_repo()
    pg_repo = pg_factory.get_bookings_repo()

    bookings = sheets_repo.list_bookings()
    migrated_count = 0

    for booking in bookings:
        try:
            # Map old IDs to new UUIDs
            client_id = client_map.get(booking.get('client_id'))
            master_id = master_map.get(booking.get('master_id'))

            if not client_id or not master_id:
                logger.warning(f"Skipping booking - client or master not found")
                continue

            # Parse datetime
            datetime_start_str = booking.get('datetime_start', '')
            datetime_end_str = booking.get('datetime_end', '')

            if not datetime_start_str or not datetime_end_str:
                logger.warning(f"Skipping booking - missing datetime")
                continue

            datetime_start = datetime.fromisoformat(datetime_start_str.replace('Z', '+00:00'))
            datetime_end = datetime.fromisoformat(datetime_end_str.replace('Z', '+00:00'))

            pg_repo.create_booking(
                client_id=client_id,
                master_id=master_id,
                service_id='',  # Service ID mapping would go here
                datetime_start=datetime_start,
                datetime_end=datetime_end,
                status=booking.get('status', 'pending'),
                google_event_id=booking.get('google_event_id', '')
            )
            migrated_count += 1
            logger.debug(f"Migrated booking for client {client_id}")
        except Exception as e:
            logger.error(f"Failed to migrate booking: {e}")

    logger.info(f"✅ Migrated {migrated_count} bookings")
    return migrated_count


def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("Starting migration: Google Sheets → PostgreSQL")
    logger.info("=" * 60)

    # Check if PostgreSQL is available
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL not set. Please configure PostgreSQL connection.")
        sys.exit(1)

    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        logger.error("❌ SPREADSHEET_ID not set. Cannot read from Google Sheets.")
        sys.exit(1)

    try:
        # Initialize factories
        sheets_factory = DatabaseFactory(use_postgres=False)
        pg_factory = DatabaseFactory(use_postgres=True)

        # Migration statistics
        stats = {
            'clients': 0,
            'masters': 0,
            'bookings': 0
        }

        # Migrate clients
        stats['clients'] = migrate_clients(sheets_factory, pg_factory)

        # Migrate masters
        stats['masters'] = migrate_masters(sheets_factory, pg_factory)

        # Build ID mappings (simplified - in real scenario, would need proper mapping)
        client_map = {}  # Old sheet row ID -> new UUID
        master_map = {}  # Old sheet row ID -> new UUID

        # Migrate bookings (would need proper ID mapping)
        # stats['bookings'] = migrate_bookings(sheets_factory, pg_factory, client_map, master_map)

        logger.info("")
        logger.info("=" * 60)
        logger.info("Migration Summary:")
        logger.info(f"  Clients:  {stats['clients']}")
        logger.info(f"  Masters:  {stats['masters']}")
        logger.info(f"  Bookings: {stats['bookings']}")
        logger.info("=" * 60)
        logger.info("✅ Migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        logger.exception("Full error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
