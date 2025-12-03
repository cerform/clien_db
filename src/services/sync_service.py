"""Service for syncing Google Calendar free slots with Sheets"""
import logging
from datetime import datetime, timedelta
from src.db.repositories.calendar_repo import CalendarRepo
from src.db.repositories.masters_repo import MastersRepo

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sheets_client = sheets_client
        self.spreadsheet_id = spreadsheet_id
        self.calendar_repo = CalendarRepo(sheets_client, spreadsheet_id)
        self.masters_repo = MastersRepo(sheets_client, spreadsheet_id)

    def sync_calendar_slots(self, master_id: str, calendar_id: str, days_ahead: int = 30, slot_duration_minutes: int = 60):
        """
        Sync free slots from Google Calendar to Sheets
        Reads all free time blocks from calendar and creates slots in Sheets
        
        Args:
            master_id: Master ID in database
            calendar_id: Google Calendar ID
            days_ahead: How many days ahead to sync (default 30)
            slot_duration_minutes: Duration of each slot (default 60)
        """
        try:
            # Get all events from calendar for next N days
            now = datetime.utcnow()
            start_date = now.date()
            end_date = start_date + timedelta(days=days_ahead)
            
            # Fetch busy times from calendar
            busy_slots = self._get_calendar_busy_times(calendar_id, start_date, end_date)
            
            # Generate all free slots first
            all_slots = []
            for current_date in self._date_range(start_date, end_date):
                date_str = current_date.isoformat()
                
                # Define business hours (9 AM to 6 PM)
                business_hours = [
                    ("09:00", "18:00")
                ]
                
                # Generate 1-hour slots during business hours
                free_slots = self._generate_free_slots(
                    date_str, 
                    business_hours, 
                    busy_slots.get(date_str, []),
                    slot_duration_minutes
                )
                all_slots.extend(free_slots)
            
            # Add all slots in batch (single request)
            if all_slots:
                self._add_slots_batch(master_id, all_slots)
            
            logger.info(f"✅ Synced {len(all_slots)} slots for master {master_id}")
            return {"status": "success", "synced": len(all_slots)}
        except Exception as e:
            logger.exception(f"❌ Calendar sync failed: {e}")
            return {"status": "error", "message": str(e)}

    def _get_calendar_busy_times(self, calendar_id: str, start_date, end_date) -> dict:
        """Get busy times from Google Calendar"""
        busy_slots = {}
        try:
            start_iso = f"{start_date}T00:00:00Z"
            end_iso = f"{end_date}T23:59:59Z"
            
            events = self.sheets_client.service_calendar.events().list(
                calendarId=calendar_id,
                timeMin=start_iso,
                timeMax=end_iso,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            for event in events.get('items', []):
                if event.get('start', {}).get('dateTime'):
                    start_dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                    date_key = start_dt.date().isoformat()
                    
                    if date_key not in busy_slots:
                        busy_slots[date_key] = []
                    
                    busy_slots[date_key].append({
                        'start': start_dt.strftime('%H:%M'),
                        'end': end_dt.strftime('%H:%M')
                    })
        except Exception as e:
            logger.warning(f"Failed to get calendar events: {e}")
        
        return busy_slots

    def _generate_free_slots(self, date_str: str, business_hours: list, busy_times: list, slot_duration: int = 60) -> list:
        """Generate free slots based on business hours and busy times"""
        free_slots = []
        
        for start_hour_str, end_hour_str in business_hours:
            start_h, start_m = map(int, start_hour_str.split(':'))
            end_h, end_m = map(int, end_hour_str.split(':'))
            
            current_time = start_h * 60 + start_m  # Convert to minutes
            end_time = end_h * 60 + end_m
            
            while current_time + slot_duration <= end_time:
                slot_start = f"{current_time // 60:02d}:{current_time % 60:02d}"
                slot_end = f"{(current_time + slot_duration) // 60:02d}:{(current_time + slot_duration) % 60:02d}"
                
                # Check if slot conflicts with busy times
                if not self._is_slot_busy(slot_start, slot_end, busy_times):
                    free_slots.append({
                        'date': date_str,
                        'start': slot_start,
                        'end': slot_end
                    })
                
                current_time += slot_duration
        
        return free_slots

    def _is_slot_busy(self, slot_start: str, slot_end: str, busy_times: list) -> bool:
        """Check if slot overlaps with any busy time"""
        slot_start_min = int(slot_start.split(':')[0]) * 60 + int(slot_start.split(':')[1])
        slot_end_min = int(slot_end.split(':')[0]) * 60 + int(slot_end.split(':')[1])
        
        for busy in busy_times:
            busy_start_min = int(busy['start'].split(':')[0]) * 60 + int(busy['start'].split(':')[1])
            busy_end_min = int(busy['end'].split(':')[0]) * 60 + int(busy['end'].split(':')[1])
            
            # Check for overlap
            if slot_start_min < busy_end_min and slot_end_min > busy_start_min:
                return True
        
        return False

    def _clear_master_slots(self, master_id: str, start_date, end_date):
        """Clear existing slots for master in date range"""
        try:
            slots = self.calendar_repo.list_slots()
            # In practice, this would need a delete method
            # For now, we'll just log that we're clearing
            logger.debug(f"Clearing slots for {master_id} between {start_date} and {end_date}")
        except Exception as e:
            logger.warning(f"Could not clear slots: {e}")

    def _add_slots_batch(self, master_id: str, slots: list):
        """Add multiple slots in a single batch request"""
        try:
            rows = []
            for slot in slots:
                row = [
                    slot["date"],
                    master_id,
                    slot["start"],
                    slot["end"],
                    "yes",
                    ""
                ]
                rows.append(row)
            
            # Batch append all rows at once
            if rows:
                body = {"values": rows}
                self.sheets_client.service_sheets.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range="calendar",
                    valueInputOption="RAW",
                    body=body
                ).execute()
                logger.info(f"✅ Added {len(rows)} slots for {master_id}")
        except Exception as e:
            logger.exception(f"Failed to add slots batch: {e}")
            raise

    def _date_range(self, start_date, end_date):
        """Generate dates between start_date and end_date"""
        current = start_date
        while current <= end_date:
            yield current
            current += timedelta(days=1)
