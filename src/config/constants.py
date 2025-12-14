import os

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
SHEET_CLIENTS = "clients"
SHEET_MASTERS = "masters"
SHEET_CALENDAR = "calendar"
SHEET_BOOKINGS = "bookings"
SHEET_SERVICES = "services"
# Cloud SQL config
CLOUDSQL_USER = os.getenv("CLOUDSQL_USER", "root")
CLOUDSQL_PASSWORD = os.getenv("CLOUDSQL_PASSWORD", "password")
CLOUDSQL_DB = os.getenv("CLOUDSQL_DB", "admin_messages")
CLOUDSQL_HOST = os.getenv("CLOUDSQL_HOST", "127.0.0.1")
CLOUDSQL_PORT = os.getenv("CLOUDSQL_PORT", "3306")
