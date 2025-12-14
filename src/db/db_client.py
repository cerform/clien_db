"""
DB client wrapper for Postgres using psycopg2 or asyncpg depending on the environment.
Provides get_db() that returns a small wrapper with methods get_connection() (sync) or get_conn_async().
This repo uses synchronous code paths for migrations and workers; if you prefer async, adapt accordingly.
"""
import os
import logging
import psycopg2
from typing import Optional

logger = logging.getLogger(__name__)


class DBClient:
    def __init__(self, dsn: Optional[str] = None):
        # Support role-based DB URLs by env var: DATABASE_URL, DATABASE_URL_INKA_BOOKING_AGENT, etc.
        self._dsn = dsn or os.getenv('DATABASE_URL')
        if not self._dsn:
            raise RuntimeError('DATABASE_URL not configured')
        self.conn = None

    def get_connection(self):
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(self._dsn)
        return self.conn


_db_singleton = None


def get_db(dsn: Optional[str] = None) -> DBClient:
    global _db_singleton
    if _db_singleton is None:
        _db_singleton = DBClient(dsn)
    return _db_singleton


def get_db_for_role(role: str) -> DBClient:
    """Return DB client configured for a specific role. Use role-based env var if present.
    Example: DATABASE_URL_INKA_BOOKING_AGENT
    """
    role_key = role.upper() if role else 'DEFAULT'
    env_key = f"DATABASE_URL_{role_key}"
    dsn = os.getenv(env_key) or os.getenv('DATABASE_URL')
    if not dsn:
        raise RuntimeError(f'DATABASE URL for role {role} not configured')
    return DBClient(dsn)
