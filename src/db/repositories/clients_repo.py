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

    def update_client(self, client_id: str, data: dict) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_CLIENTS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == client_id:
                # keep original created_at
                new_row = [r.get('id'), data.get('telegram_id', r.get('telegram_id')), data.get('name', r.get('name')),
                           data.get('phone', r.get('phone')), data.get('email', r.get('email')), data.get('notes', r.get('notes')),
                           r.get('created_at')]
                self.sc.update_row(self.spreadsheet_id, SHEET_CLIENTS, idx, new_row)
                return True
        return False

    def delete_client(self, client_id: str) -> bool:
        # Soft delete: mark as deleted if an 'active' or 'status' column exists; otherwise remove row by writing blank
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_CLIENTS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == client_id:
                # clear row
                blank_row = ['' for _ in range(len(r))]
                self.sc.update_row(self.spreadsheet_id, SHEET_CLIENTS, idx, blank_row)
                return True
        return False
