"""
Проверка форматирования Google Sheets для БД (ИНКА + админ)
"""
import sys
import logging
from src.db.db_initializer import DatabaseInitializer
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Эталонная структура
SHEETS_STRUCTURE = {
    "Мастера": [
        "ID", "name", "specialization", "experience_years", "rating",
        "phone", "instagram", "price_per_session", "status", "bio",
        "calendar_id", "language", "tags",
        "name_ru", "name_en", "name_he",
        "specialization_ru", "specialization_en", "specialization_he",
        "bio_ru", "bio_en", "bio_he"
    ],
    "Клиенты": [
        "id", "telegram_id", "name", "phone", "email",
        "notes", "created_at", "last_visit", "preferred_language", "language_code"
    ],
    "Записи": [
        "id", "client_id", "master_id", "service_id",
        "date", "time", "duration_min", "price", "status", "notes", "created_at"
    ],
    "Услуги": [
        "id", "name", "description", "duration_min",
        "base_price", "category", "status", "image_url", "language", "tags",
        "name_ru", "name_en", "name_he",
        "description_ru", "description_en", "description_he"
    ],
    "Расписание": [
        "id", "master_id", "day_of_week", "start_time", "end_time",
        "is_working", "break_start", "break_end", "notes"
    ],
    "Отзывы": [
        "id", "client_id", "master_id", "booking_id",
        "rating", "text", "created_at", "helpful_count"
    ],
    "Прайс-лист": [
        "id", "master_id", "service_id", "price", "commission_percent",
        "net_income", "created_at", "is_active", "notes"
    ]
}

def validate_db_format(credentials_file, spreadsheet_id):
    creds = Credentials.from_service_account_file(credentials_file, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    service = build("sheets", "v4", credentials=creds)
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    errors = []
    for sheet_name, expected_headers in SHEETS_STRUCTURE.items():
        found = False
        for sheet in spreadsheet.get("sheets", []):
            if sheet["properties"]["title"] == sheet_name:
                found = True
                # Получить заголовки
                result = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet_name}!1:1"
                ).execute()
                actual_headers = result.get("values", [[]])[0]

                # Normalize headers to lowercase for lenient comparison
                expected_set = set([h.lower() for h in expected_headers])
                actual_set = set([h.lower() for h in actual_headers])

                # Identify missing headers
                missing = sorted(list(expected_set - actual_set))
                if missing:
                    errors.append(f"❌ [{sheet_name}] missing headers: {missing}\n  Expected (subset): {expected_headers}\n  Actual: {actual_headers}")
                else:
                    # If no missing headers, but actual ordering differ, warn (non-fatal)
                    if [h.lower() for h in actual_headers][:len(expected_headers)] != [h.lower() for h in expected_headers]:
                        errors.append(f"⚠️ [{sheet_name}] header order differs (not fatal).\n  Expected start: {expected_headers[:len(expected_headers)]}\n  Actual start: {actual_headers[:len(expected_headers)]}")
                break
        if not found:
            errors.append(f"❌ [{sheet_name}] not found in spreadsheet.")
    if errors:
        print("DB FORMAT ERRORS:")
        for err in errors:
            print(err)
        sys.exit(1)
    print("✅ DB format is valid.")
    return True

if __name__ == "__main__":
    import os
    cred = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")
    sheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    if not sheet_id:
        print("GOOGLE_SPREADSHEET_ID not set")
        sys.exit(1)
    validate_db_format(cred, sheet_id)
