import pytest
import uuid
from datetime import datetime
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.database_unifier import DatabaseUnifier

class MockSheetsClient:
    """Mock Google Sheets client for testing database unifier"""
    def __init__(self, sheets_data=None):
        self.sheets_data = sheets_data or {}

    def get_sheet_values(self, sheet_name):
        return self.sheets_data.get(sheet_name, [])

@pytest.fixture
def mock_sheets_client():
    """Create a mock sheets client with sample data"""
    sample_masters_data = [
        ['id', 'name', 'phone', 'telegram_id', 'specialization', 'rating', 'experience'],
        ['master_1', 'Иван Петров', '501234567', 'ivan_bot', 'Tattoo Artist', '4.5', '5'],
        ['master_2', 'Анна Смирнова', '507654321', 'anna_bot', 'Piercing Specialist', '4.8', '7']
    ]
    
    sample_clients_data = [
        ['id', 'name', 'phone', 'notes', 'email'],
        ['client_1', 'Максим Иванов', '521234567', 'Первый раз, из Тель-Авива', 'maxim@example.com'],
        ['client_2', 'Елена Петрова', '529876543', 'Постоянный клиент', 'elena@example.com']
    ]
    
    sample_services_data = [
        ['id', 'name', 'description', 'duration', 'price'],
        ['service_1', 'Черно-белая татуировка', 'Простая черно-белая татуировка', '120', '1500'],
        ['service_2', 'Цветная татуировка', 'Татуировка с цветными элементами', '180', '2500']
    ]
    
    return MockSheetsClient({
        'Мастера': sample_masters_data,
        'Клиенты': sample_clients_data,
        'Услуги': sample_services_data
    })

@pytest.fixture
def unifier(mock_sheets_client):
    """Create a DatabaseUnifier instance with mock sheets client"""
    return DatabaseUnifier(mock_sheets_client)

def test_parse_client_name_variations(unifier):
    """Test different name parsing scenarios"""
    test_cases = [
        ('Иван', {
            'full_name': 'Иван',
            'first_name': 'Иван',
            'last_name': '',
            'display_name': 'Иван'
        }),
        ('Иван Петров', {
            'full_name': 'Иван Петров',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'display_name': 'Иван Петров'
        }),
        ('Иван Сергеевич Петров', {
            'full_name': 'Иван Сергеевич Петров',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'display_name': 'Иван Сергеевич Петров'
        }),
        ('', {
            'full_name': 'Unknown Client',
            'first_name': 'Unknown',
            'last_name': 'Client',
            'display_name': 'Unknown Client'
        })
    ]

    for name, expected in test_cases:
        assert unifier.parse_client_name(name) == expected

def test_phone_number_normalization(unifier):
    """Comprehensive test for phone number parsing and normalization"""
    test_cases = [
        ('501234567', '+972501234567'),     # Local number
        ('0501234567', '+972501234567'),    # With leading zero
        ('+972501234567', '+972501234567'), # Already correct
        ('', ''),                           # Empty string
        ('invalid', ''),                    # Invalid input
        ('972501234567', '+972501234567')   # Different formats
    ]

    for input_phone, expected in test_cases:
        assert unifier.parse_phone_number(input_phone) == expected

def test_extract_client_info_from_notes(unifier):
    """Test extracting additional client information from notes"""
    test_cases = [
        ('Первый раз, из Тель-Авива', {
            'city': 'тель-авив',
            'gender': '',
            'is_first_tattoo': True
        }),
        ('Он хочет татуировку', {
            'city': '',
            'gender': 'male',
            'is_first_tattoo': False
        }),
        ('Она хочет пирсинг', {
            'city': '',
            'gender': 'female',
            'is_first_tattoo': False
        }),
        ('', {
            'city': '',
            'gender': '',
            'is_first_tattoo': False
        })
    ]

    for notes, expected in test_cases:
        assert unifier.extract_client_info_from_notes(notes) == expected

def test_normalize_client_data_full_details(unifier):
    """Test comprehensive client data normalization"""
    client_data = {
        'name': 'Максим Иванов',
        'phone': '521234567',
        'email': 'maxim@example.com',
        'telegram_id': 'maxim_bot',
        'notes': 'Первый раз, из Тель-Авива'
    }

    normalized = unifier.normalize_client_data(client_data)

    assert normalized['name'] == 'Максим Иванов'
    assert normalized['first_name'] == 'Максим'
    assert normalized['last_name'] == 'Иванов'
    assert normalized['phone'] == '+972521234567'
    assert normalized['email'] == 'maxim@example.com'
    assert normalized['telegram_id'] == 'maxim_bot'
    assert normalized['city'] == 'тель-авив'
    assert normalized['is_first_tattoo'] == True
    assert 'id' in normalized  # UUID should be generated
    assert 'created_at' in normalized

def test_rating_normalization(unifier):
    """Test rating normalization with various inputs"""
    test_cases = [
        (5.0, 5.0),      # Within range
        (6.5, 5.0),      # Above maximum
        (-2.3, 0.0),     # Below minimum
        ('4,5', 4.5),    # Comma-separated input
        ('invalid', 0.0) # Invalid input
    ]

    for input_val, expected in test_cases:
        assert unifier._normalize_rating(input_val) == expected

def test_experience_normalization(unifier):
    """Test experience years normalization"""
    test_cases = [
        (5, 5),          # Within range
        (60, 50),        # Above maximum
        (-3, 0),         # Below minimum
        ('3 года', 3),   # String with text
        ('invalid', 0)   # Invalid input
    ]

    for input_val, expected in test_cases:
        assert unifier._normalize_experience(input_val) == expected

def test_validate_client_scenarios(unifier):
    """Test client validation with different scenarios"""
    valid_cases = [
        {'id': 'client_1', 'name': 'Максим Иванов'},
        {'id': 'client_2', 'name': 'Елена Петрова', 'phone': '529876543'}
    ]

    invalid_cases = [
        {},  # Empty dict
        {'name': 'Максим Иванов'},  # Missing ID
        {'id': 'client_123'}  # Missing name
    ]

    for valid_client in valid_cases:
        is_valid, errors = unifier.validate_client(valid_client)
        assert is_valid, f"Client {valid_client} should be valid"
        assert len(errors) == 0, f"No errors expected for {valid_client}"

    for invalid_client in invalid_cases:
        is_valid, errors = unifier.validate_client(invalid_client)
        assert not is_valid, f"Client {invalid_client} should be invalid"
        assert len(errors) > 0, f"Errors expected for {invalid_client}"

def test_parse_master_id_from_text(unifier):
    """Test parsing master ID from text"""
    masters_list = [
        {'id': 'master_1', 'name': 'Иван Петров'},
        {'id': 'master_2', 'name': 'Анна Смирнова'}
    ]

    assert unifier.parse_master_id_from_text('Иван Петров', masters_list) == 'master_1'
    assert unifier.parse_master_id_from_text('Анна', masters_list) == 'master_2'
    assert unifier.parse_master_id_from_text('Unknown', masters_list) is None

def test_normalize_master_data(unifier):
    """Test master data normalization"""
    master_data = {
        'name': 'Максим Иванов',
        'phone': '501234567',
        'telegram_id': 'maxim_bot',
        'specialization': 'Tattoo Artist',
        'rating': '4.5',
        'experience': '5 лет',
        'instagram': '@maxim_tattoo'
    }

    normalized = unifier.normalize_master_data(master_data)

    assert normalized['name'] == 'Максим Иванов'
    assert normalized['first_name'] == 'Максим'
    assert normalized['last_name'] == 'Иванов'
    assert normalized['phone'] == '+972501234567'
    assert normalized['telegram_id'] == 'maxim_bot'
    assert normalized['specialization'] == 'Tattoo Artist'
    assert normalized['rating'] == 4.5
    assert normalized['experience'] == 5
    assert normalized['instagram'] == '@maxim_tattoo'
    assert 'id' in normalized  # UUID should be generated
    assert normalized['status'] == 'active'

def test_unify_database(unifier, mock_sheets_client):
    """Test the complete database unification process"""
    result = unifier.unify_database(dry_run=True)

    assert 'masters' in result
    assert 'clients' in result
    assert 'services' in result
    assert 'validation_errors' in result
    assert result['dry_run'] == True
    
    # Verify each table has been processed
    assert result['masters']['status'] == 'success'
    assert result['masters']['total_masters'] > 0
    assert len(result['clients']['data']) > 0
    assert len(result['services']['data']) > 0