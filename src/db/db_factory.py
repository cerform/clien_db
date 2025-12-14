"""
Database factory for creating repository instances
Manages connections to PostgreSQL and Google Sheets
"""
import os
import logging
from typing import Optional
from sqlalchemy import create_engine, text
from src.db.repositories.postgres import (
    ClientsRepoPG,
    MastersRepoPG,
    BookingsRepoPG,
    ServicesRepoPG,
    CalendarRepoPG
)
from src.db.repositories.admin_messages_repo import AdminMessagesRepo
from src.db.sheets_client import SheetsClient
from src.config.config import Config

logger = logging.getLogger(__name__)


class DatabaseFactory:
    """Factory for creating database repositories"""

    def __init__(self, use_postgres: bool = True, config: Optional[Config] = None):
        """
        Initialize database factory

        Args:
            use_postgres: If True, use PostgreSQL; if False, use Google Sheets
            config: Configuration object (optional, will load from env if not provided)
        """
        self.use_postgres = use_postgres
        self.config = config or Config.from_env()
        self.pg_engine = None
        self.sheets_client = None

        if use_postgres:
            self._init_postgres()
        else:
            self._init_sheets()

    def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # Try constructing from individual env vars
            user = os.getenv("CLOUDSQL_USER", "postgres")
            password = os.getenv("CLOUDSQL_PASSWORD", "password")
            host = os.getenv("CLOUDSQL_HOST", "127.0.0.1")
            port = os.getenv("CLOUDSQL_PORT", "5432")
            db = os.getenv("CLOUDSQL_DB", "tattoo_salon")
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

        try:
            self.pg_engine = create_engine(
                database_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                echo=False
            )
            # Test connection
            with self.pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ PostgreSQL connection established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def _init_sheets(self):
        """Initialize Google Sheets client"""
        try:
            self.sheets_client = SheetsClient(
                creds_path=self.config.GOOGLE_CREDENTIALS_PATH,
                token_path=self.config.GOOGLE_TOKEN_PATH
            )
            logger.info("✅ Google Sheets client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise

    def get_clients_repo(self):
        """Get clients repository"""
        if self.use_postgres:
            return ClientsRepoPG(self.pg_engine)
        else:
            from src.db.repositories.clients_repo import ClientsRepo
            return ClientsRepo(self.sheets_client, self.config.SPREADSHEET_ID)

    def get_masters_repo(self):
        """Get masters repository"""
        if self.use_postgres:
            return MastersRepoPG(self.pg_engine)
        else:
            from src.db.repositories.masters_repo import MastersRepo
            return MastersRepo(self.sheets_client, self.config.SPREADSHEET_ID)

    def get_bookings_repo(self):
        """Get bookings repository"""
        if self.use_postgres:
            return BookingsRepoPG(self.pg_engine)
        else:
            from src.db.repositories.bookings_repo import BookingsRepo
            return BookingsRepo(self.sheets_client, self.config.SPREADSHEET_ID)

    def get_services_repo(self):
        """Get services repository"""
        if self.use_postgres:
            return ServicesRepoPG(self.pg_engine)
        else:
            # Sheets doesn't have services repo yet, return None
            logger.warning("Services repository not implemented for Sheets")
            return None

    def get_calendar_repo(self):
        """Get calendar repository"""
        if self.use_postgres:
            return CalendarRepoPG(self.pg_engine)
        else:
            # Sheets calendar repo would go here
            logger.warning("Calendar repository not fully implemented for Sheets")
            return None

    def get_admin_messages_repo(self):
        """Get admin messages repository (always PostgreSQL)"""
        if not self.pg_engine:
            self._init_postgres()
        return AdminMessagesRepo(self.pg_engine)

    def close(self):
        """Close all database connections"""
        if self.pg_engine:
            self.pg_engine.dispose()
            logger.info("PostgreSQL connections closed")


# Global factory instance
_db_factory = None


def get_db_factory(use_postgres: bool = None) -> DatabaseFactory:
    """
    Get singleton database factory instance

    Args:
        use_postgres: If provided, override the default behavior

    Returns:
        DatabaseFactory instance
    """
    global _db_factory

    if use_postgres is None:
        # Auto-detect: use PostgreSQL if DATABASE_URL is set
        use_postgres = bool(os.getenv("DATABASE_URL"))

    if _db_factory is None:
        _db_factory = DatabaseFactory(use_postgres=use_postgres)
        logger.info(f"Database factory initialized (mode: {'PostgreSQL' if use_postgres else 'Google Sheets'})")

    return _db_factory


def init_db_factory(use_postgres: bool = True) -> DatabaseFactory:
    """
    Initialize database factory (call at app startup)

    Args:
        use_postgres: Whether to use PostgreSQL (True) or Google Sheets (False)

    Returns:
        DatabaseFactory instance
    """
    global _db_factory
    _db_factory = DatabaseFactory(use_postgres=use_postgres)
    return _db_factory
