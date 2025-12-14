"""
Script to migrate admin_messages from Google Sheets to Google Cloud SQL
"""
import os
import gspread
import sqlalchemy
from google.oauth2.service_account import Credentials

# Google Sheets setup
SHEET_NAME = os.getenv("ADMIN_MESSAGES_SHEET", "admin_messages")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS", "credentials.json")

# Cloud SQL setup
DB_USER = os.getenv("CLOUDSQL_USER", "root")
DB_PASSWORD = os.getenv("CLOUDSQL_PASSWORD", "password")
DB_NAME = os.getenv("CLOUDSQL_DB", "admin_messages")
DB_HOST = os.getenv("CLOUDSQL_HOST", "127.0.0.1")
DB_PORT = os.getenv("CLOUDSQL_PORT", "3306")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Connect to Google Sheets
gs_creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(gs_creds)
sh = gc.open(SHEET_NAME)
worksheet = sh.sheet1

# Connect to Cloud SQL
db_engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URL)
conn = db_engine.connect()

# Read all rows from Google Sheets
rows = worksheet.get_all_values()

# Create table if not exists
conn.execute(f"""
CREATE TABLE IF NOT EXISTS admin_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp VARCHAR(32),
    user_id VARCHAR(32),
    username VARCHAR(64),
    message TEXT,
    category VARCHAR(64),
    data JSON,
    inka_category VARCHAR(64),
    sheet_row INT
);
""")

# Insert rows into Cloud SQL
for i, row in enumerate(rows[1:], start=2):  # skip header
    timestamp, user_id, username, message, category, data, inka_category, sheet_row = row[:8]
    conn.execute(sqlalchemy.text("""
        INSERT INTO admin_messages (timestamp, user_id, username, message, category, data, inka_category, sheet_row)
        VALUES (:timestamp, :user_id, :username, :message, :category, :data, :inka_category, :sheet_row)
    """), {
        "timestamp": timestamp,
        "user_id": user_id,
        "username": username,
        "message": message,
        "category": category,
        "data": data,
        "inka_category": inka_category,
        "sheet_row": i
    })

print("Migration complete.")
conn.close()
