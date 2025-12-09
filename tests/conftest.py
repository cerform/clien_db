"""
Pytest configuration and fixtures for the project.

This file provides shared test fixtures for all test modules.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from tests.mocks.google_sheets_client import MockGoogleSheetsClient

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    return {
        "TELEGRAM_BOT_TOKEN": "test_token_123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "WEBHOOK_URL": "https://test-bot.example.com",
        "ADMIN_IDS": "12345,67890",
        "GOOGLE_SHEETS_ID": "test_sheet_id_123",
        "GOOGLE_CALENDAR_ID": "test_calendar_id_123",
        "OPENAI_API_KEY": "sk-test-key",
        "OPENAI_ASSISTANT_ID": "asst_test123",
    }


@pytest.fixture
def mock_google_sheets():
    """Mock Google Sheets API client."""
    mock = MagicMock()
    mock.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
        "values": [
            ["id", "name", "email", "specialization"],
            ["1", "Anna", "anna@test.com", "реализм"],
            ["2", "Platon", "platon@test.com", "минимализм"],
        ]
    }
    return mock


@pytest.fixture
def mock_sheets_client(monkeypatch, mock_sheet_data):
    """Provide and patch the GoogleSheetsClient to use in-memory mock for tests."""
    initial_data = {
        'Masters': [
            ['id','name','phone','telegram_id','specialization','rating','experience','instagram','status','bio','calendar_id'],
            ['1','Anna','+1234567890','111','реализм','4.5','5','@anna','active','bio','cal_1']
        ],
        'Services': [
            ['id','name','description','duration_min','price_from','price_to','category','active'],
            ['1','Consultation','free',30,0,0,'other','TRUE']
        ],
        'Clients': [
            ['id','telegram_id','name','phone','email','notes','created_at','last_visit'],
        ],
        'Bookings': [
            ['id','client_id','master_id','service_id','date','time','duration_min','price','status','notes','created_at'],
        ],
        'Расписание': [
            ['id','master_id','day_of_week','start_time','end_time','is_working','break_start','break_end','notes'],
        ],
        'Admin_Audit_Log': [
            ['timestamp','admin_id','action','sheet','details'],
        ],
        'INKA_Training': [
            ['id','timestamp','category','user_input','inka_response','admin_correction','improvement','tags','status'],
        ]
    }

    mock_client = MockGoogleSheetsClient(initial_data=initial_data)
    monkeypatch.setattr('src.db.sheets_client.GoogleSheetsClient', lambda credentials_file, spreadsheet_id: mock_client)
    return mock_client


@pytest.fixture
def mock_google_calendar():
    """Mock Google Calendar API client."""
    mock = MagicMock()
    mock.events.return_value.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "event1",
                "summary": "Consultation",
                "start": {"dateTime": "2025-01-10T10:00:00Z"},
                "end": {"dateTime": "2025-01-10T11:00:00Z"},
            }
        ]
    }
    return mock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI API client."""
    mock = MagicMock()
    mock_text = Mock()
    mock_text.value = "Test response from INKA"
    mock.beta.threads.messages.create.return_value = Mock(
        content=[Mock(text=mock_text)]
    )
    return mock


@pytest.fixture
def sample_telegram_message():
    """Sample Telegram message for webhook testing."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "date": 1704895200,
            "chat": {"id": 987654321, "type": "private"},
            "from": {"id": 987654321, "is_bot": False, "first_name": "Test"},
            "text": "Hello, I want to book a tattoo appointment",
        },
    }


@pytest.fixture
def sample_telegram_callback():
    """Sample Telegram callback query for button testing."""
    return {
        "update_id": 123456790,
        "callback_query": {
            "id": "callback_id_123",
            "from": {"id": 987654321, "is_bot": False, "first_name": "Test"},
            "chat_instance": "123456789",
            "data": "master_1",
            "message": {
                "message_id": 1,
                "date": 1704895200,
                "chat": {"id": 987654321, "type": "private"},
                "text": "Select a master",
            },
        },
    }


@pytest.fixture
def test_config():
    """Test configuration object."""
    config = {
        "telegram": {
            "token": "test_token_123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            "webhook_url": "https://test-bot.example.com",
            "webhook_path": "/webhook/telegram",
            "webhook_port": 8080,
        },
        "admin": {
            "ids": [12345, 67890],
        },
        "google": {
            "sheets_id": "test_sheet_id_123",
            "calendar_id": "test_calendar_id_123",
            "credentials_file": "credentials.json",
        },
        "openai": {
            "api_key": "sk-test-key",
            "assistant_id": "asst_test123",
            "model": "gpt-4",
        },
        "database": {
            "type": "sheets",
            "sync_interval": 300,
        },
    }
    return config


@pytest.fixture
def mock_sheet_data():
    """Mock data from Google Sheets."""
    return {
        "masters": [
            {
                "id": "1",
                "name": "Anna",
                "email": "anna@test.com",
                "specialization": "реализм",
                "phone": "+1234567890",
                "bio": "Professional tattoo artist",
            },
            {
                "id": "2",
                "name": "Platon",
                "email": "platon@test.com",
                "specialization": "минимализм",
                "phone": "+0987654321",
                "bio": "Minimalist tattoo specialist",
            },
        ],
        "services": [
            {
                "id": "1",
                "name": "Consultation",
                "duration": 30,
                "price": 0,
                "description": "Free initial consultation",
            },
            {
                "id": "2",
                "name": "Small Tattoo",
                "duration": 60,
                "price": 100,
                "description": "Up to 5x5 cm",
            },
        ],
        "schedule": [
            {
                "id": "1",
                "master_id": "1",
                "date": "2025-01-10",
                "start_time": "10:00",
                "end_time": "11:00",
                "booked": False,
            },
            {
                "id": "2",
                "master_id": "1",
                "date": "2025-01-10",
                "start_time": "11:00",
                "end_time": "12:00",
                "booked": True,
            },
        ],
        "bookings": [
            {
                "id": "1",
                "client_id": "123456",
                "master_id": "1",
                "service_id": "1",
                "date": "2025-01-10",
                "time": "10:00",
                "status": "confirmed",
                "notes": "First visit",
            }
        ],
    }


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files after each test."""
    yield
    # Cleanup code here if needed
    pass


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line(
        "markers", "webhook: marks tests as webhook-related tests"
    )
    config.addinivalue_line("markers", "calendar: marks tests as calendar-related")
    config.addinivalue_line("markers", "sheets: marks tests as sheets-related")


# Markers for categorizing tests
pytestmark = [
    pytest.mark.unit,  # Default to unit tests
]


@pytest.fixture
def suppress_logs(caplog):
    """Suppress INFO and DEBUG logs during tests."""
    caplog.set_level("WARNING")
    return caplog
