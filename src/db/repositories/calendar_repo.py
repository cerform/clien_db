from src.config.constants import SHEET_CALENDAR
from src.db.schemas import build_row, pad_row_to_headers

class CalendarRepo:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_slots(self):
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_CALENDAR)

    def add_slot(self, date: str, master_id: str, slot_start: str, slot_end: str, available: str = "yes", note: str = ""):
        values = {
            'date': date,
            'master_id': master_id,
            'slot_start': slot_start,
            'slot_end': slot_end,
            'available': available,
            'note': note
        }
        row = build_row('calendar', values)
        row = pad_row_to_headers('calendar', row)
        try:
            self.sc.append_row(self.spreadsheet_id, SHEET_CALENDAR, row)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Failed to append calendar slot; proceeding in best-effort mode")
