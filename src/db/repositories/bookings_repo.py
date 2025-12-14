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

    def update_booking(self, booking_id: str, data: dict) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_BOOKINGS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == booking_id:
                new_row = [r.get('id'), data.get('client_id', r.get('client_id')), data.get('master_id', r.get('master_id')),
                           data.get('service_id', r.get('service_id')), data.get('datetime_start', r.get('datetime_start')),
                           data.get('datetime_end', r.get('datetime_end')), data.get('status', r.get('status')),
                           data.get('price', r.get('price')), data.get('comment_client', r.get('comment_client')),
                           data.get('comment_master', r.get('comment_master')), data.get('source', r.get('source')),
                           r.get('created_at'), data.get('updated_at', r.get('updated_at') or ''), data.get('google_event_id', r.get('google_event_id') or '')]
                self.sc.update_row(self.spreadsheet_id, SHEET_BOOKINGS, idx, new_row)
                return True
        return False

    def delete_booking(self, booking_id: str) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_BOOKINGS)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == booking_id:
                blank_row = ['' for _ in range(len(r))]
                self.sc.update_row(self.spreadsheet_id, SHEET_BOOKINGS, idx, blank_row)
                return True
        return False

    def cancel_booking(self, booking_id: str, reason: str = "") -> bool:
        """
        Cancel a booking by changing its status to 'cancelled'
        Args:
            booking_id: ID of the booking to cancel
            reason: Optional reason for cancellation
        Returns:
            bool: True if booking was cancelled successfully, False otherwise
        """
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_BOOKINGS)
        if not rows:
            return False

        for idx, r in enumerate(rows, start=1):
            if r.get('id') == booking_id:
                # Update status to cancelled and add cancellation timestamp
                data = {
                    'status': 'cancelled',
                    'updated_at': datetime.datetime.utcnow().isoformat(),
                    'comment_master': f"{r.get('comment_master', '')} | Cancelled: {reason}" if reason else r.get('comment_master', '')
                }
                return self.update_booking(booking_id, data)

        return False

    def reschedule_booking(self, booking_id: str, new_date: str, new_start_time: str, new_end_time: str) -> bool:
        """
        Reschedule a booking to a new date/time
        Args:
            booking_id: ID of the booking to reschedule
            new_date: New date for the booking (ISO format)
            new_start_time: New start time
            new_end_time: New end time
        Returns:
            bool: True if booking was rescheduled successfully, False otherwise
        """
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_BOOKINGS)
        if not rows:
            return False

        for idx, r in enumerate(rows, start=1):
            if r.get('id') == booking_id:
                # Update booking with new date/time
                data = {
                    'date': new_date,
                    'slot_start': new_start_time,
                    'slot_end': new_end_time,
                    'datetime_start': f"{new_date}T{new_start_time}",
                    'datetime_end': f"{new_date}T{new_end_time}",
                    'updated_at': datetime.datetime.utcnow().isoformat(),
                    'status': 'rescheduled'  # Mark as rescheduled
                }
                return self.update_booking(booking_id, data)

        return False

    def get_booking_by_id(self, booking_id: str) -> dict:
        """
        Get a single booking by ID
        Args:
            booking_id: ID of the booking
        Returns:
            dict: Booking data or None if not found
        """
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_BOOKINGS)
        if not rows:
            return None

        for r in rows:
            if r.get('id') == booking_id:
                return r

        return None

    def get_bookings_by_client(self, client_id: str) -> list:
        """
        Get all bookings for a specific client
        Args:
            client_id: Client ID
        Returns:
            list: List of booking dictionaries
        """
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_BOOKINGS)
        if not rows:
            return []

        return [r for r in rows if r.get('client_id') == client_id]

    def get_bookings_by_master(self, master_id: str) -> list:
        """
        Get all bookings for a specific master
        Args:
            master_id: Master ID
        Returns:
            list: List of booking dictionaries
        """
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_BOOKINGS)
        if not rows:
            return []

        return [r for r in rows if r.get('master_id') == master_id]

    def get_bookings_by_date_range(self, start_date: str, end_date: str) -> list:
        """
        Get all bookings within a date range
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
        Returns:
            list: List of booking dictionaries
        """
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_BOOKINGS)
        if not rows:
            return []

        bookings_in_range = []
        for r in rows:
            booking_date = r.get('date', '')
            if booking_date and start_date <= booking_date <= end_date:
                bookings_in_range.append(r)

        return bookings_in_range
