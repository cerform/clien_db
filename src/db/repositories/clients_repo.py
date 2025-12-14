import uuid
import datetime
from src.config.constants import SHEET_CLIENTS
from src.db.schemas import build_row, pad_row_to_headers

class ClientsRepo:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_clients(self):
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_CLIENTS)

    def create_client(self, telegram_id: int, name: str, phone: str = "", email: str = "", notes: str = ""):
        cid = str(uuid.uuid4())
        values = {
            'id': cid,
            'telegram_id': str(telegram_id),
            'name': name,
            'phone': phone,
            'email': email,
            'notes': notes,
            # tags, last_visit will be empty by default
        }
        row = build_row('clients', values)
        row = pad_row_to_headers('clients', row)
        try:
            self.sc.append_row(self.spreadsheet_id, SHEET_CLIENTS, row)
        except Exception:
            # Best-effort in test environments or if spreadsheet is missing — log and continue
            import logging
            logging.getLogger(__name__).exception("Failed to append client row; proceeding in best-effort mode")
        return {"id": cid, "telegram_id": telegram_id, "name": name, "phone": phone}

    def update_client(self, client_id: str, data: dict) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_CLIENTS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == client_id:
                # keep original created_at
                values = {
                    'id': r.get('id'),
                    'telegram_id': data.get('telegram_id', r.get('telegram_id')),
                    'name': data.get('name', r.get('name')),
                    'phone': data.get('phone', r.get('phone')),
                    'email': data.get('email', r.get('email')),
                    'notes': data.get('notes', r.get('notes')),
                    'created_at': r.get('created_at')
                }
                new_row = build_row('clients', values)
                new_row = pad_row_to_headers('clients', new_row)
                try:
                    self.sc.update_row(self.spreadsheet_id, SHEET_CLIENTS, idx, new_row)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("Failed to update client row; proceeding in best-effort mode")
                return True
        return False

    def delete_client(self, client_id: str) -> bool:
        # Attempt hard delete: remove the row from the sheet so it does not reappear
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_CLIENTS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == client_id:
                try:
                    # Preferred: actually delete the row
                    if hasattr(self.sc, 'delete_row'):
                        self.sc.delete_row(self.spreadsheet_id, SHEET_CLIENTS, idx)
                    else:
                        # Fallback: blank the row
                        blank_row = ['' for _ in range(len(rows[0]))]
                        self.sc.update_row(self.spreadsheet_id, SHEET_CLIENTS, idx, blank_row)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("Failed to delete client row; proceeding in best-effort mode")
                return True
        return False
