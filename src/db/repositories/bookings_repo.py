import uuid
import datetime
from src.config.constants import SHEET_BOOKINGS

class BookingsRepo:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_bookings(self):
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_BOOKINGS)

    def create_booking(self, client_id: str, master_id: str, date: str, slot_start: str, slot_end: str, status: str = "pending", google_event_id: str = ""):
        bid = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow().isoformat()
        row = [bid, client_id, master_id, date, slot_start, slot_end, status, created_at, google_event_id]
        self.sc.append_row(self.spreadsheet_id, SHEET_BOOKINGS, row)
        return {"id": bid}
