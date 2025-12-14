import uuid
import datetime
from src.config.constants import SHEET_SERVICES

class ServicesRepo:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_services(self):
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_SERVICES)

    def create_service(self, name: str, description: str, duration_min: int = 60, price_from: int = 0, price_to: int = 0, category: str = 'tattoo', active: bool = True):
        sid = str(uuid.uuid4())
        row = [sid, name, description, duration_min, price_from, price_to, category, 'yes' if active else 'no']
        self.sc.append_row(self.spreadsheet_id, SHEET_SERVICES, row)
        return {"id": sid, "name": name}

    def update_service(self, service_id: str, data: dict) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_SERVICES)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == service_id:
                new_row = [r.get('id'), data.get('name', r.get('name')), data.get('description', r.get('description')),
                           data.get('duration_min', r.get('duration_min')), data.get('price_from', r.get('price_from')),
                           data.get('price_to', r.get('price_to')), data.get('category', r.get('category')), data.get('active', r.get('active'))]
                self.sc.update_row(self.spreadsheet_id, SHEET_SERVICES, idx, new_row)
                return True
        return False

    def delete_service(self, service_id: str) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_SERVICES)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == service_id:
                blank_row = ['' for _ in range(len(r))]
                self.sc.update_row(self.spreadsheet_id, SHEET_SERVICES, idx, blank_row)
                return True
        return False
