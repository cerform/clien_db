from src.config.constants import SHEET_CALENDAR

class CalendarRepo:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_slots(self):
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_CALENDAR)

    def add_slot(self, date: str, master_id: str, slot_start: str, slot_end: str, available: str = "yes", note: str = ""):
        row = [date, master_id, slot_start, slot_end, available, note]
        self.sc.append_row(self.spreadsheet_id, SHEET_CALENDAR, row)
