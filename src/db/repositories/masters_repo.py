import uuid
import datetime
from src.config.constants import SHEET_MASTERS

class MastersRepo:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_masters(self):
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_MASTERS)

    def create_master(self, name: str, calendar_id: str = "", specialties: str = "", active: bool = True):
        mid = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow().isoformat()
        row = [mid, name, calendar_id, specialties, "yes" if active else "no", created_at]
        self.sc.append_row(self.spreadsheet_id, SHEET_MASTERS, row)
        return {"id": mid, "name": name}
