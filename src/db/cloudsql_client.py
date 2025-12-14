"""
Cloud SQL client for managing database connections
Supports both local (via proxy) and Cloud Run (Unix socket) connections
"""
import os
import sqlalchemy
from sqlalchemy import create_engine
from contextlib import contextmanager


class CloudSQLClient:
    """Manages Cloud SQL connections for both local and production environments"""

    def __init__(self, connection_name: str = None):
        """
        Initialize Cloud SQL client

        Args:
            connection_name: GCP connection name (project:region:instance)
                           e.g., "tattoo-480007:us-central1:tattoo-bot-db"
        """
        self.connection_name = connection_name or os.getenv("CLOUDSQL_CONNECTION_NAME")
        self.db_user = os.getenv("CLOUDSQL_USER", "postgres")
        self.db_password = os.getenv("CLOUDSQL_PASSWORD", "password")
        self.db_name = os.getenv("CLOUDSQL_DB", "admin_messages")
        self.db_host = os.getenv("CLOUDSQL_HOST", "127.0.0.1")
        self.db_port = os.getenv("CLOUDSQL_PORT", "5432")

        self.engine = None
        self._create_engine()

    def _create_engine(self):
        """Create SQLAlchemy engine based on environment"""

        # Check if DATABASE_URL is set (PostgreSQL)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Use DATABASE_URL directly (supports PostgreSQL)
            connection_string = database_url
        # Check if running on Cloud Run (Unix socket connection)
        elif os.getenv("CLOUD_RUN_ENV") == "true" and self.connection_name:
            # Cloud Run uses Unix socket. Prefer Postgres/psycopg2 connection string
            # Note: For Postgres, use the host query parameter: `?host=/cloudsql/INSTANCE`
            # For compatibility, prefer Postgres connection string; if user uses MySQL, update env.
            db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
            unix_socket_path = f"{db_socket_dir}/{self.connection_name}"

            connection_string = (
                f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
                f"@/{self.db_name}?host={unix_socket_path}"
            )
        else:
            # Local development (via Cloud SQL Proxy on TCP)
            connection_string = (
                f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )

        # Create engine with connection pooling
        self.engine = create_engine(
            connection_string,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False  # Set to True for SQL debugging
        )

    def get_engine(self):
        """Get SQLAlchemy engine"""
        return self.engine

    @contextmanager
    def get_connection(self):
        """
        Get database connection as context manager

        Usage:
            with client.get_connection() as conn:
                result = conn.execute(query)
        """
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = None):
        """
        Execute a query and return results as list of dicts

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            List of dicts with column names as keys
        """
        try:
            with self.get_connection() as conn:
                # Convert params tuple to dict for SQLAlchemy
                if params:
                    # Create parameter dict from positional params
                    param_dict = {}
                    # Split query to find parameter placeholders
                    import re
                    placeholders = re.findall(r'%s', query)
                    for i, val in enumerate(params):
                        param_dict[f'param_{i}'] = val
                    # Replace %s with :param_0, :param_1, etc.
                    modified_query = query
                    for i in range(len(params)):
                        modified_query = modified_query.replace('%s', f':param_{i}', 1)

                    result = conn.execute(sqlalchemy.text(modified_query), param_dict)
                else:
                    result = conn.execute(sqlalchemy.text(query))

                # Check if query returns rows (SELECT, RETURNING)
                if result.returns_rows:
                    rows = result.fetchall()
                    # Convert to list of dicts
                    return [dict(zip(result.keys(), row)) for row in rows]
                else:
                    # For INSERT/UPDATE/DELETE without RETURNING
                    conn.commit()
                    return []
        except Exception as e:
            print(f"Query execution error: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test database connection

        Returns:
            True if connection successful
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute(sqlalchemy.text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def close(self):
        """Close database engine and all connections"""
        if self.engine:
            self.engine.dispose()


# Singleton instance for global use
_cloudsql_client = None


def get_cloudsql_client(connection_name: str = None) -> CloudSQLClient:
    """
    Get singleton CloudSQL client instance

    Args:
        connection_name: Optional connection name for first initialization

    Returns:
        CloudSQLClient instance
    """
    global _cloudsql_client
    if _cloudsql_client is None:
        _cloudsql_client = CloudSQLClient(connection_name)
    return _cloudsql_client


def init_cloudsql_client(connection_name: str = None) -> CloudSQLClient:
    """
    Initialize CloudSQL client (use at app startup)

    Args:
        connection_name: GCP connection name

    Returns:
        CloudSQLClient instance
    """
    global _cloudsql_client
    _cloudsql_client = CloudSQLClient(connection_name)
    return _cloudsql_client
