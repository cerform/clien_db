import uuid
import datetime
from src.config.constants import SHEET_MASTERS
from src.db.schemas import build_row, pad_row_to_headers

class MastersRepo:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_masters(self):
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_MASTERS)

    def create_master(self, name: str, calendar_id: str = "", specialties: str = "", active: bool = True):
        mid = str(uuid.uuid4())
        values = {
            'id': mid,
            'name': name,
            'specialization': specialties,
            'status': 'yes' if active else 'no',
            'calendar_id': calendar_id
        }
        row = build_row('masters', values)
        row = pad_row_to_headers('masters', row)
        try:
            self.sc.append_row(self.spreadsheet_id, SHEET_MASTERS, row)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Failed to append master row; proceeding in best-effort mode")
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
                values = {
                    'id': r.get('id'),
                    'name': r.get('name'),
                    'specialization': r.get('specialization') or r.get('specialties') or '',
                    'status': r.get('status') or r.get('active') or 'yes',
                    'calendar_id': calendar_id,
                    'telegram_id': r.get('telegram_id')
                }
                new_row = build_row('masters', values)
                new_row = pad_row_to_headers('masters', new_row)
                try:
                    self.sc.update_row(self.spreadsheet_id, SHEET_MASTERS, idx, new_row)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("Failed to update master calendar; proceeding in best-effort mode")
                return True
        return False

    def update_master(self, master_id: str, data: dict) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_MASTERS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == master_id:
                values = {
                    'id': r.get('id'),
                    'name': data.get('name', r.get('name')),
                    'specialization': data.get('specialization', r.get('specialization')),
                    'rating': data.get('rating', r.get('rating')),
                    'experience_years': data.get('experience_years', r.get('experience_years')),
                    'instagram': data.get('instagram', r.get('instagram')),
                    'status': data.get('status', r.get('status') or 'yes'),
                    'telegram_id': data.get('telegram_id', r.get('telegram_id')),
                    'calendar_id': data.get('calendar_id', r.get('calendar_id')),
                    'notes': data.get('notes', r.get('notes') or '')
                }
                new_row = build_row('masters', values)
                new_row = pad_row_to_headers('masters', new_row)
                try:
                    self.sc.update_row(self.spreadsheet_id, SHEET_MASTERS, idx, new_row)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("Failed to update master row; proceeding in best-effort mode")
                return True
        return False

    def delete_master(self, master_id: str) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_MASTERS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == master_id:
                # Soft delete: set status to 'no' and append deleted note
                notes = (r.get('notes') or '') + f" [deleted:{datetime.datetime.now(datetime.timezone.utc).isoformat()}]"
                values = {
                    'id': r.get('id'),
                    'name': r.get('name'),
                    'specialization': r.get('specialization'),
                    'status': 'no',
                    'calendar_id': r.get('calendar_id'),
                    'notes': notes
                }
                new_row = build_row('masters', values)
                new_row = pad_row_to_headers('masters', new_row)
                try:
                    self.sc.update_row(self.spreadsheet_id, SHEET_MASTERS, idx, new_row)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("Failed to soft-delete master; proceeding in best-effort mode")
                return True
        return False
