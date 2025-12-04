#!/usr/bin/env python3
"""
Reformat Google Sheets database to English with proper structure
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config.config import get_config
from src.db.sheets_client import GoogleSheetsClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database schema with English names
SCHEMA = {
    "masters": {
        "headers": ["id", "name", "phone", "telegram_id", "specialization", "rating", "photo_url", "bio", "status", "created_at"],
        "sample_data": [
            ["1", "Анна Иванова", "+7-999-123-4567", "123456789", "Татуировка, Пирсинг", "4.9", "", "Опыт 8 лет", "active", "2025-01-01"],
            ["2", "Мария Петрова", "+7-999-234-5678", "234567890", "Татуировка", "4.8", "", "Опыт 5 лет", "active", "2025-01-01"],
        ]
    },
    "clients": {
        "headers": ["id", "telegram_id", "name", "phone", "email", "notes", "created_at", "last_visit"],
        "sample_data": [
            ["1", "111222333", "Иван Сидоров", "+7-999-345-6789", "", "Постоянный клиент", "2025-01-15", "2025-11-20"],
            ["2", "444555666", "Елена Козлова", "+7-999-456-7890", "elena@mail.ru", "", "2025-02-10", "2025-11-25"],
        ]
    },
    "bookings": {
        "headers": ["id", "client_id", "master_id", "service_id", "date", "time", "duration_min", "price", "status", "notes", "created_at"],
        "sample_data": [
            ["1", "1", "1", "1", "2025-12-10", "14:00", "120", "8000", "confirmed", "Первый сеанс", "2025-12-01"],
            ["2", "2", "2", "2", "2025-12-12", "11:00", "60", "3000", "confirmed", "", "2025-12-02"],
        ]
    },
    "services": {
        "headers": ["id", "name", "description", "duration_min", "price_from", "price_to", "category", "active"],
        "sample_data": [
            ["1", "Татуировка малая", "До 5см", "60", "3000", "5000", "tattoo", "true"],
            ["2", "Татуировка средняя", "5-15см", "120", "8000", "15000", "tattoo", "true"],
            ["3", "Пирсинг", "Любая зона", "30", "2000", "4000", "piercing", "true"],
            ["4", "Консультация", "Эскиз и консультация", "60", "1000", "1000", "consultation", "true"],
        ]
    },
    "schedule": {
        "headers": ["id", "master_id", "day_of_week", "start_time", "end_time", "is_working", "notes"],
        "sample_data": [
            ["1", "1", "monday", "10:00", "18:00", "true", ""],
            ["2", "1", "tuesday", "10:00", "18:00", "true", ""],
            ["3", "1", "wednesday", "10:00", "18:00", "true", ""],
            ["4", "2", "monday", "11:00", "19:00", "true", ""],
            ["5", "2", "thursday", "11:00", "19:00", "true", ""],
        ]
    },
    "reviews": {
        "headers": ["id", "client_id", "master_id", "booking_id", "rating", "comment", "created_at"],
        "sample_data": [
            ["1", "1", "1", "1", "5", "Отличная работа!", "2025-11-21"],
            ["2", "2", "2", "2", "5", "Очень довольна результатом", "2025-11-26"],
        ]
    },
    "price_list": {
        "headers": ["id", "service_id", "master_id", "custom_price", "description", "active"],
        "sample_data": [
            ["1", "1", "1", "4000", "Специальная цена Анны", "true"],
            ["2", "2", "2", "10000", "Специальная цена Марии", "true"],
        ]
    }
}

def create_sheet_if_not_exists(sheets_client, sheet_name):
    """Create sheet if it doesn't exist"""
    try:
        # Check if sheet exists
        spreadsheet = sheets_client.service.spreadsheets().get(
            spreadsheetId=sheets_client.spreadsheet_id
        ).execute()
        
        existing_sheets = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        
        if sheet_name in existing_sheets:
            logger.info(f"Sheet {sheet_name} already exists")
            return True
        
        # Create new sheet
        requests = [{
            "addSheet": {
                "properties": {
                    "title": sheet_name,
                    "gridProperties": {
                        "rowCount": 1000,
                        "columnCount": 20
                    }
                }
            }
        }]
        
        sheets_client.service.spreadsheets().batchUpdate(
            spreadsheetId=sheets_client.spreadsheet_id,
            body={"requests": requests}
        ).execute()
        
        logger.info(f"✅ Created sheet {sheet_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sheet {sheet_name}: {e}")
        return False

def clear_sheet(sheets_client, sheet_name):
    """Clear all data from a sheet"""
    try:
        sheets_client.service.spreadsheets().values().clear(
            spreadsheetId=sheets_client.spreadsheet_id,
            range=f"{sheet_name}!A1:Z1000"
        ).execute()
        logger.info(f"✅ Cleared {sheet_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to clear {sheet_name}: {e}")
        return False

def create_or_update_sheet(sheets_client, sheet_name, headers, sample_data):
    """Create or update a sheet with proper structure"""
    try:
        # Add headers
        sheets_client.service.spreadsheets().values().update(
            spreadsheetId=sheets_client.spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
        
        # Add sample data
        if sample_data:
            sheets_client.service.spreadsheets().values().update(
                spreadsheetId=sheets_client.spreadsheet_id,
                range=f"{sheet_name}!A2",
                valueInputOption='RAW',
                body={'values': sample_data}
            ).execute()
        
        # Format header row (bold)
        requests = [{
            "repeatCell": {
                "range": {
                    "sheetId": get_sheet_id(sheets_client, sheet_name),
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True},
                        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor)"
            }
        }]
        
        sheets_client.service.spreadsheets().batchUpdate(
            spreadsheetId=sheets_client.spreadsheet_id,
            body={"requests": requests}
        ).execute()
        
        logger.info(f"✅ Created/Updated {sheet_name} with {len(headers)} columns and {len(sample_data)} rows")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create/update {sheet_name}: {e}")
        return False

def get_sheet_id(sheets_client, sheet_name):
    """Get sheet ID by name"""
    try:
        spreadsheet = sheets_client.service.spreadsheets().get(
            spreadsheetId=sheets_client.spreadsheet_id
        ).execute()
        
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        return 0
    except:
        return 0

def main():
    """Main function"""
    try:
        logger.info("=" * 60)
        logger.info("REFORMATTING DATABASE TO ENGLISH")
        logger.info("=" * 60)
        
        config = get_config()
        sheets_client = GoogleSheetsClient(
            config.google_credentials_json,
            config.google_spreadsheet_id
        )
        
        logger.info(f"\nSpreadsheet ID: {config.google_spreadsheet_id}")
        logger.info(f"\nCreating {len(SCHEMA)} tables...\n")
        
        for sheet_name, schema in SCHEMA.items():
            logger.info(f"Processing: {sheet_name}")
            create_sheet_if_not_exists(sheets_client, sheet_name)
            clear_sheet(sheets_client, sheet_name)
            create_or_update_sheet(
                sheets_client,
                sheet_name,
                schema["headers"],
                schema["sample_data"]
            )
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ DATABASE FORMATTED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("\nCreated tables:")
        for i, sheet_name in enumerate(SCHEMA.keys(), 1):
            logger.info(f"  {i}. {sheet_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
