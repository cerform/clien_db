import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.db.sheets_client import GoogleSheetsClient
from src.config import SHEET_BOOKINGS, BOOKING_STATUS_PENDING

logger = logging.getLogger(__name__)

class BookingService:
    """Service for managing bookings"""
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets = sheets_client
    
    def create_booking(self, user_id: int, master_id: int, date: str, time: str, service: str) -> bool:
        """Create a new booking"""
        try:
            values = [
                str(user_id),
                str(master_id),
                date,
                time,
                service,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                BOOKING_STATUS_PENDING,
                ""  # Notes
            ]
            
            success = self.sheets.append_row(SHEET_BOOKINGS, values)
            if success:
                logger.info(f"Booking created: user={user_id}, master={master_id}, date={date}")
            return success
        except Exception as e:
            logger.error(f"Failed to create booking: {e}")
            return False
    
    def get_booking(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Get booking by ID"""
        try:
            rows = self.sheets.get_sheet_values(SHEET_BOOKINGS)
            if not rows:
                return None
            
            for idx, row in enumerate(rows[1:], start=1):  # Skip header
                if len(row) > 0 and str(row[0]).strip() == str(booking_id).strip():
                    return {
                        'id': idx,
                        'user_id': row[0],
                        'master_id': row[1] if len(row) > 1 else '',
                        'date': row[2] if len(row) > 2 else '',
                        'time': row[3] if len(row) > 3 else '',
                        'service': row[4] if len(row) > 4 else '',
                        'created_at': row[5] if len(row) > 5 else '',
                        'status': row[6] if len(row) > 6 else '',
                        'notes': row[7] if len(row) > 7 else ''
                    }
            return None
        except Exception as e:
            logger.error(f"Failed to get booking: {e}")
            return None
    
    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all bookings for a user"""
        try:
            rows = self.sheets.get_sheet_values(SHEET_BOOKINGS)
            if not rows:
                return []
            
            bookings = []
            for idx, row in enumerate(rows[1:], start=1):  # Skip header
                if len(row) > 0 and str(row[0]).strip() == str(user_id).strip():
                    bookings.append({
                        'id': idx,
                        'user_id': row[0],
                        'master_id': row[1] if len(row) > 1 else '',
                        'date': row[2] if len(row) > 2 else '',
                        'time': row[3] if len(row) > 3 else '',
                        'service': row[4] if len(row) > 4 else '',
                        'created_at': row[5] if len(row) > 5 else '',
                        'status': row[6] if len(row) > 6 else '',
                        'notes': row[7] if len(row) > 7 else ''
                    })
            return bookings
        except Exception as e:
            logger.error(f"Failed to get user bookings: {e}")
            return []
    
    def get_master_bookings(self, master_id: int, status: str = None) -> List[Dict[str, Any]]:
        """Get all bookings for a master"""
        try:
            rows = self.sheets.get_sheet_values(SHEET_BOOKINGS)
            if not rows:
                return []
            
            bookings = []
            for idx, row in enumerate(rows[1:], start=1):  # Skip header
                if len(row) > 1 and str(row[1]).strip() == str(master_id).strip():
                    booking_status = row[6] if len(row) > 6 else ''
                    if status is None or booking_status == status:
                        bookings.append({
                            'id': idx,
                            'user_id': row[0],
                            'master_id': row[1],
                            'date': row[2] if len(row) > 2 else '',
                            'time': row[3] if len(row) > 3 else '',
                            'service': row[4] if len(row) > 4 else '',
                            'created_at': row[5] if len(row) > 5 else '',
                            'status': booking_status,
                            'notes': row[7] if len(row) > 7 else ''
                        })
            return bookings
        except Exception as e:
            logger.error(f"Failed to get master bookings: {e}")
            return []
    
    def update_booking_status(self, booking_id: int, status: str) -> bool:
        """Update booking status"""
        try:
            rows = self.sheets.get_sheet_values(SHEET_BOOKINGS)
            if not rows:
                return False
            
            for row_idx, row in enumerate(rows):
                if len(row) > 0 and str(row[0]).strip() == str(booking_id).strip():
                    new_row = list(row)
                    if len(new_row) > 6:
                        new_row[6] = status
                    
                    range_spec = f"A{row_idx + 1}:H{row_idx + 1}"
                    return self.sheets.update_range(SHEET_BOOKINGS, range_spec, [new_row])
            
            return False
        except Exception as e:
            logger.error(f"Failed to update booking status: {e}")
            return False
    
    def cancel_booking(self, booking_id: int) -> bool:
        """Cancel a booking"""
        from src.config import BOOKING_STATUS_CANCELLED
        return self.update_booking_status(booking_id, BOOKING_STATUS_CANCELLED)
