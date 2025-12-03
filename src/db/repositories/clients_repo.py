import uuid
import datetime
from src.config.constants import SHEET_CLIENTS

class ClientsRepo:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_clients(self):
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_CLIENTS)

    def create_client(self, telegram_id: int, name: str, phone: str = "", email: str = "", notes: str = ""):
        cid = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow().isoformat()
        row = [cid, str(telegram_id), name, phone, email, notes, created_at]
        self.sc.append_row(self.spreadsheet_id, SHEET_CLIENTS, row)
        return {"id": cid, "telegram_id": telegram_id, "name": name, "phone": phone}
