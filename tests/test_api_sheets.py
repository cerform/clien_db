import importlib
if importlib.util.find_spec('fastapi') is None:
    import pytest
    pytest.skip('fastapi not installed, skipping API sheet tests', allow_module_level=True)

from fastapi.testclient import TestClient
from src.web.app import create_app


class DummySheetsClient:
    def __init__(self):
        self.sheets = {
            'TestSheet': [['id', 'name'], ['1', 'Alice']]
        }

    def get_sheets_list(self):
        return list(self.sheets.keys())

    def get_sheet_values(self, sheet_name, range_spec=''):
        return self.sheets.get(sheet_name, [])

    def append_rows(self, sheet_name, rows):
        if sheet_name not in self.sheets:
            self.sheets[sheet_name] = [['id', 'name']]
        self.sheets[sheet_name] += rows
        return True

    def update_range(self, sheet_name, range_spec, values):
        self.sheets[sheet_name] = values
        return True


class DummyDBManager:
    def __init__(self):
        from src.db.sheets_client import GoogleSheetsClient
        self.sheets = DummySheetsClient()

    def list_sheets(self):
        return self.sheets.get_sheets_list()

    def export_sheet(self, sheet_name):
        values = self.sheets.get_sheet_values(sheet_name)
        if not values:
            return {"headers": [], "rows": []}
        headers = values[0]
        rows = [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in values[1:]]
        return {"headers": headers, "rows": rows}

    def import_sheet(self, sheet_name, rows, mode='append'):
        list_rows = [[r.get(h, '') for h in (rows[0].keys() if rows and isinstance(rows, list) else [])] for r in rows]
        self.sheets.append_rows(sheet_name, list_rows)
        return True, 'Imported'

    def backup_db(self):
        return {s: {'headers': self.sheets.get_sheet_values(s)[0], 'rows': [dict(zip(self.sheets.get_sheet_values(s)[0], row)) for row in self.sheets.get_sheet_values(s)[1:]]} for s in self.sheets.get_sheets_list()}

    def restore_db(self, data, mode='replace'):
        for sname, sheet in data.items():
            self.sheets.update_range(sname, 'A1:Z9999', [sheet.get('headers', [])] + [list(r.values()) for r in sheet.get('rows', [])])
        return True, 'Restored'

    def add_audit_log(self, admin_id, action, sheet, details=''):
        return True

    def get_audit_logs(self, limit=100):
        return [{'timestamp': '2025-01-01T00:00:00', 'admin_id': 'test', 'action': 'test', 'sheet': 'TestSheet', 'details': ''}]


def test_api_sheets_endpoints(monkeypatch):
    app = create_app()
    # monkeypatch the db_manager
    import src.web.app as webapp
    webapp.db_manager = DummyDBManager()

    client = TestClient(app)

    res_list = client.get('/api/sheets')
    assert res_list.status_code == 200
    assert 'TestSheet' in res_list.json()

    res_export = client.get('/api/sheets/TestSheet')
    assert res_export.status_code == 200
    data = res_export.json()
    assert 'headers' in data and 'rows' in data

    # Import rows
    rows = [{'id': '2', 'name': 'Bob'}]
    res_import = client.post('/api/sheets/TestSheet/import', json={'rows': rows, 'mode': 'append', 'admin_id': 'tester'})
    assert res_import.status_code == 200
    assert res_import.json().get('success')

    # backup
    res_backup = client.get('/api/db/backup')
    assert res_backup.status_code == 200
    assert 'TestSheet' in res_backup.json()

    # audit logs
    res_logs = client.get('/api/audit/logs')
    assert res_logs.status_code == 200
    assert isinstance(res_logs.json(), list)

    # restore
    backup = res_backup.json()
    res_restore = client.post('/api/db/restore', json={'backup': backup, 'mode': 'replace', 'admin_id': 'tester'})
    assert res_restore.status_code == 200
    assert res_restore.json().get('success')
