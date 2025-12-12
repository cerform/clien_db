"""
Script to setup Cloud SQL database and user for admin_messages
"""
import os
import sqlalchemy

DB_USER = os.getenv("CLOUDSQL_USER", "root")
DB_PASSWORD = os.getenv("CLOUDSQL_PASSWORD", "password")
DB_NAME = os.getenv("CLOUDSQL_DB", "admin_messages")
DB_HOST = os.getenv("CLOUDSQL_HOST", "127.0.0.1")
DB_PORT = os.getenv("CLOUDSQL_PORT", "3306")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/"

db_engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URL)
conn = db_engine.connect()

# Create database if not exists
conn.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
conn.execute(f"USE {DB_NAME};")

# Create user and grant privileges
conn.execute(f"CREATE USER IF NOT EXISTS '{DB_USER}'@'%' IDENTIFIED BY '{DB_PASSWORD}';")
conn.execute(f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{DB_USER}'@'%';")
conn.execute("FLUSH PRIVILEGES;")

print("Cloud SQL setup complete.")
conn.close()
