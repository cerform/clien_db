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

    def update_master_calendar(self, master_id: str, calendar_id: str):
        """Update the calendar_id for a master by master UUID.

        Returns True if updated, False if not found.
        """
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_MASTERS)
        if not rows:
            return False
        # The SheetsClient read_sheet returns list of dicts keyed by header
        for idx, r in enumerate(rows, start=1):
            # r is dict of header->value; assume id column is 'id'
            if r.get('id') == master_id:
                # Build full row in the expected format: id, name, calendar_id, specialties, active, created_at
                new_row = [r.get('id'), r.get('name'), calendar_id, r.get('specialties') or '', r.get('active') or 'yes', r.get('created_at') or '']
                # idx is row index starting from 1 for the first data row, but update_row expects 0-based index
                self.sc.update_row(self.spreadsheet_id, SHEET_MASTERS, idx, new_row)
                return True
        return False

    def update_master(self, master_id: str, data: dict) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_MASTERS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == master_id:
                new_row = [r.get('id'), data.get('name', r.get('name')), data.get('specialization', r.get('specialization')),
                           data.get('rating', r.get('rating')), data.get('experience_years', r.get('experience_years')),
                           data.get('instagram', r.get('instagram')), data.get('status', r.get('status') or 'yes'),
                           data.get('telegram_id', r.get('telegram_id')), data.get('calendar_id', r.get('calendar_id')),
                           data.get('notes', r.get('notes') or '')]
                self.sc.update_row(self.spreadsheet_id, SHEET_MASTERS, idx, new_row)
                return True
        return False

    def delete_master(self, master_id: str) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_MASTERS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == master_id:
                blank_row = ['' for _ in range(len(r))]
                self.sc.update_row(self.spreadsheet_id, SHEET_MASTERS, idx, blank_row)
                return True
        return False
