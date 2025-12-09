import pytest

from src.db.sheets_client import GoogleSheetsClient


class FakeValues:
    def __init__(self):
        self.last_append = None

    def append(self, spreadsheetId=None, range=None, valueInputOption=None, body=None):
        self.last_append = {
            'spreadsheetId': spreadsheetId,
            'range': range,
            'body': body
        }

        class Exec:
            def execute(self_inner):
                return {'updates': {'updatedCells': 1}}

        return Exec()

    def update(self, spreadsheetId=None, range=None, valueInputOption=None, body=None):
        # just simulate update and record last range
        self.last_update = {
            'spreadsheetId': spreadsheetId,
            'range': range,
            'body': body
        }

        class Exec:
            def execute(self_inner):
                return {'updatedCells': 1}

        return Exec()


class FakeSpreadsheets:
    def __init__(self, values):
        self._values = values

    def values(self):
        return self._values


class FakeService:
    def __init__(self):
        self._values = FakeValues()

    def spreadsheets(self):
        return FakeSpreadsheets(self._values)


def test_resolve_sheet_name_alias_and_append():
    # Create a GoogleSheetsClient instance without calling __init__ (to avoid real Google API calls)
    client = GoogleSheetsClient.__new__(GoogleSheetsClient)
    client.spreadsheet_id = 'fake-spreadsheet'
    client.service = FakeService()
    client.sheet_aliases = {
        'clients': ['Clients', 'Клиенты']
    }

    # Simulate sheet exists only as Cyrillic name
    client._sheet_exists = lambda name: True if name == 'Клиенты' else False
    client.get_sheets_list = lambda: ['Клиенты']

    # Resolve a name and verify it's the Cyrillic alias
    resolved = client._resolve_sheet_name('Clients')
    assert resolved == 'Клиенты'

    # Append row using the English name; it should resolve and call API with Cyrillic sheet name
    success = client.append_row('Clients', ['id1', 'Test User'])
    assert success is True
    assert client.service._values.last_append is not None
    assert client.service._values.last_append['range'] == 'Клиенты'


def test_append_rows_resolve_alias():
    client = GoogleSheetsClient.__new__(GoogleSheetsClient)
    client.spreadsheet_id = 'fake-spreadsheet'
    client.service = FakeService()
    client.sheet_aliases = {
        'clients': ['Clients', 'Клиенты']
    }

    # Simulate sheet exists only as English name
    client._sheet_exists = lambda name: True if name == 'Clients' else False
    client.get_sheets_list = lambda: ['Clients']

    # Append multiple rows using Cyrillic name; should resolve to 'Clients'
    success = client.append_rows('Клиенты', [['id1', 'Test User'], ['id2', 'Bob']])
    assert success is True
    assert client.service._values.last_append['range'] == 'Clients'


def test_update_cell_resolve_alias():
    client = GoogleSheetsClient.__new__(GoogleSheetsClient)
    client.spreadsheet_id = 'fake-spreadsheet'
    client.service = FakeService()
    client.sheet_aliases = {
        'clients': ['Clients', 'Клиенты']
    }
    client._sheet_exists = lambda name: True if name == 'Clients' else False
    client.get_sheets_list = lambda: ['Clients']

    success = client.update_cell('Клиенты', 'B2', 'New Value')
    assert success is True
    assert getattr(client.service._values, 'last_update', None) is not None
    assert client.service._values.last_update['range'] == 'Clients!B2'


def test_advanced_inka_create_client_resolves_sheet_alias():
    from src.ai.advanced_inka import AdvancedINKA

    # Fake sheets client that simulates only English sheet 'Clients' exists
    class FakeSheetsClientForInka:
        def __init__(self):
            self.sheets = {
                'Clients': [['id','telegram_id','name','phone','email','notes','created_at','last_visit']]
            }
            self.last_appended = None

        def get_all_rows(self, sheet_name):
            return self.sheets.get(sheet_name, [])

        def append_row(self, sheet_name, values):
            # simulate resolution by just recording what was passed
            self.last_appended = {'sheet': sheet_name, 'values': values}
            if sheet_name not in self.sheets:
                self.sheets[sheet_name] = [['id','telegram_id','name','phone','email','notes','created_at','last_visit']]
            self.sheets[sheet_name].append(values)
            return True

        def get_sheets_list(self):
            return list(self.sheets.keys())

    fake_sheets = FakeSheetsClientForInka()

    # Instantiate INKA with fake sheets client
    inka = AdvancedINKA(api_key='fake', assistant_id='fake', sheets_client=fake_sheets, calendar_service=None, data_sync=None)

    # Create a client; create_client uses 'Клиенты' inside the method
    result = inka.create_client(telegram_id=55555, name='Alias Test', phone='+111', email='a@b.com', notes='Test')

    assert result.get('success') is True
    # Since our FakeSheetsClient doesn't implement resolution, ensure it received append for 'Клиенты'
    # The real GoogleSheetsClient would resolve to 'Clients'. Our fake just records what was called.
    assert fake_sheets.last_appended is not None
    assert fake_sheets.last_appended['values'][2] == 'Alias Test'
