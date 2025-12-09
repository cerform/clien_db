from src.services.admin_db_manager import DatabaseManager
from tests.mocks.google_sheets_client import MockGoogleSheetsClient


def test_add_client_with_mock_sheets(mock_sheets_client):
    db_manager = DatabaseManager(mock_sheets_client)
    success, message = db_manager.add_client({'name': 'Test Client', 'phone': '+10000000000'}, actor='web')
    assert success
    clients = db_manager.get_all_clients()
    assert any(c['name'] == 'Test Client' for c in clients)
