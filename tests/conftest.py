"""Pytest configuration and fixtures"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config import Config


@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = Mock(spec=Config)
    config.BOT_TOKEN = "test_token"
    config.SPREADSHEET_ID = "test_spreadsheet_id"
    config.GOOGLE_CREDENTIALS_PATH = "credentials.json"
    config.GOOGLE_TOKEN_PATH = "token.json"
    config.ADMIN_USER_IDS = [12345678]
    config.DEFAULT_TIMEZONE = "Asia/Jerusalem"
    config.USE_WEBHOOK = False
    config.WEBHOOK_URL = None
    config.PORT = 8080
    config.OPENAI_API_KEY = None
    return config


@pytest.fixture
def mock_sheets_client():
    """Mock Google Sheets client"""
    client = MagicMock()
    client.service_sheets = MagicMock()
    client.service_calendar = MagicMock()
    client.read_sheet = MagicMock(return_value=[])
    client.write_sheet = MagicMock(return_value=True)
    client.append_row = MagicMock(return_value=True)
    client.update_cell = MagicMock(return_value=True)
    client.get_values = MagicMock(return_value=[])
    client.create_calendar_event = MagicMock(return_value="event_123")
    client.delete_calendar_event = MagicMock(return_value=True)
    return client


@pytest.fixture
def sample_client():
    """Sample client data"""
    return {
        "id": "client_001",
        "telegram_id": "123456789",
        "name": "John Doe",
        "phone": "+972501234567",
        "notes": "Test client",
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_master():
    """Sample master data"""
    return {
        "id": "master_001",
        "name": "Jane Artist",
        "calendar_id": "jane@example.com",
        "specialties": "traditional, watercolor",
        "active": "yes"
    }


@pytest.fixture
def sample_booking():
    """Sample booking data"""
    return {
        "id": "booking_001",
        "client_id": "client_001",
        "master_id": "master_001",
        "date": "2025-12-10",
        "slot_start": "14:00",
        "slot_end": "16:00",
        "status": "confirmed",
        "notes": "Small dragon tattoo",
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_slot():
    """Sample calendar slot data"""
    return {
        "date": "2025-12-10",
        "master_id": "master_001",
        "slot_start": "14:00",
        "slot_end": "16:00",
        "available": "yes",
        "notes": ""
    }


@pytest.fixture
def sample_free_slots():
    """Sample free slots for testing"""
    today = datetime.now().date()
    return [
        {
            "date": (today + timedelta(days=i)).isoformat(),
            "master_id": "master_001",
            "slot_start": "10:00",
            "slot_end": "12:00",
            "available": "yes",
            "notes": ""
        }
        for i in range(1, 8)
    ]
