"""
Data Synchronization Service
Синхронизирует данные между:
- Google Sheets (основной источник)
- Google Calendar (расписание мастеров)
- Внутренний кэш INKA
- Bookings/Events

Архитектура:
    Google Sheets (истина)
         ↓
    DataSync Service
     ↙       ↓       ↘
  Cache   Calendar  INKA Cache
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.db.sheets_client import GoogleSheetsClient
from src.calendars.calendar_init import get_calendar_service

logger = logging.getLogger(__name__)


@dataclass
class SyncStats:
    """Statistics for sync operation"""
    timestamp: datetime
    tables_synced: List[str]
    events_synced: int
    masters_cached: int
    services_cached: int
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DataSyncService:
    """
    Unified data synchronization service
    
    Manages synchronization between:
    - Google Sheets (masters, services, schedule, bookings)
    - Google Calendar (actual events and availability)
    - INKA cache (for fast access)
    """
    
    def __init__(self, sheets_client: GoogleSheetsClient, 
                 calendar_service=None,
                 sync_interval: int = 3600):
        """
        Initialize sync service
        
        Args:
            sheets_client: GoogleSheetsClient instance
            calendar_service: Google Calendar service instance
            sync_interval: Sync interval in seconds (default 1 hour)
        """
        self.sheets_client = sheets_client
        self.calendar_service = calendar_service
        self.sync_interval = sync_interval
        self.last_sync_time = 0
        
        # Data caches
        self._masters_data = None
        self._services_data = None
        self._schedule_data = None
        self._bookings_data = None
        self._calendar_events = None
        
        # Sync metadata
        self._last_full_sync = 0
        self.last_stats: Optional[SyncStats] = None
    
    def should_sync(self) -> bool:
        """Check if sync is needed"""
        current_time = time.time()
        return (current_time - self.last_sync_time) > self.sync_interval
    
    def sync_all(self) -> SyncStats:
        """
        Full synchronization of all data
        
        Returns:
            SyncStats with sync results
        """
        logger.info("🔄 Starting full data synchronization...")
        start_time = time.time()
        
        stats = SyncStats(
            timestamp=datetime.now(),
            tables_synced=[],
            events_synced=0,
            masters_cached=0,
            services_cached=0
        )
        
        try:
            # 1. Sync from Google Sheets
            self._sync_sheets_data(stats)
            
            # 2. Sync with Google Calendar
            if self.calendar_service:
                self._sync_calendar_data(stats)
            
            # 3. Validate consistency
            self._validate_consistency(stats)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Sync completed in {elapsed:.2f}s")
            logger.info(f"   Tables: {', '.join(stats.tables_synced)}")
            logger.info(f"   Masters: {stats.masters_cached}, Services: {stats.services_cached}")
            logger.info(f"   Calendar events: {stats.events_synced}")
            
            self.last_sync_time = time.time()
            self.last_stats = stats
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Sync error: {e}", exc_info=True)
            stats.errors.append(str(e))
            return stats
    
    def _sync_sheets_data(self, stats: SyncStats) -> None:
        """Sync data from Google Sheets"""
        try:
            # Load masters
            masters = self.sheets_client.get_all_rows("masters")
            if masters:
                self._masters_data = self._rows_to_dicts(masters)
                stats.masters_cached = len(self._masters_data)
                stats.tables_synced.append("masters")
                logger.info(f"   📊 Loaded {len(self._masters_data)} masters")
            
            # Load services
            services = self.sheets_client.get_all_rows("services")
            if services:
                self._services_data = self._rows_to_dicts(services)
                stats.services_cached = len(self._services_data)
                stats.tables_synced.append("services")
                logger.info(f"   📊 Loaded {len(self._services_data)} services")
            
            # Load schedule
            schedule = self.sheets_client.get_all_rows("schedule")
            if schedule:
                self._schedule_data = self._rows_to_dicts(schedule)
                stats.tables_synced.append("schedule")
                logger.info(f"   📊 Loaded {len(self._schedule_data)} schedule entries")
            
            # Load bookings
            bookings = self.sheets_client.get_all_rows("bookings")
            if bookings:
                self._bookings_data = self._rows_to_dicts(bookings)
                stats.tables_synced.append("bookings")
                logger.info(f"   📊 Loaded {len(self._bookings_data)} bookings")
                
        except Exception as e:
            logger.error(f"❌ Sheets sync error: {e}")
            stats.errors.append(f"Sheets sync: {e}")
    
    def _sync_calendar_data(self, stats: SyncStats) -> None:
        """Sync events from Google Calendar for all masters"""
        try:
            if not self.calendar_service:
                logger.warning("⚠️ Calendar service not available")
                return
            
            # Get events for next 30 days
            from datetime import datetime as dt
            today = dt.now()
            start_date = today.date().isoformat()
            end_date = (today + timedelta(days=30)).date().isoformat()
            
            all_events = []
            
            # Get masters with calendar_id
            masters = self._masters_data or []
            
            for master in masters:
                calendar_id = master.get("calendar_id")
                master_id = master.get("id")
                
                if not calendar_id:
                    logger.debug(f"⚠️ Master '{master.get('name')}' has no calendar_id")
                    continue
                
                try:
                    events_result = self.calendar_service.events().list(
                        calendarId=calendar_id,
                        timeMin=f"{start_date}T00:00:00Z",
                        timeMax=f"{end_date}T23:59:59Z",
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    events = events_result.get('items', [])
                    
                    # Add master_id to each event for later filtering
                    for event in events:
                        event['_master_id'] = master_id
                    
                    all_events.extend(events)
                    logger.debug(f"   📅 Loaded {len(events)} events from master '{master.get('name')}'")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Calendar query error for master '{master.get('name')}': {e}")
                    stats.errors.append(f"Calendar (master {master_id}): {e}")
            
            self._calendar_events = all_events
            stats.events_synced = len(all_events)
            stats.tables_synced.append("calendar")
            logger.info(f"   📅 Loaded {len(all_events)} total calendar events from {len(masters)} masters")
                
        except Exception as e:
            logger.error(f"❌ Calendar sync error: {e}")
            stats.errors.append(f"Calendar sync: {e}")
    
    def _validate_consistency(self, stats: SyncStats) -> None:
        """Validate data consistency between sources"""
        if not self._masters_data or not self._schedule_data:
            return
        
        # Check all schedule entries have valid master_id
        master_ids = {m.get("id") for m in self._masters_data}
        invalid_schedules = []
        
        for sched in self._schedule_data:
            master_id = sched.get("master_id")
            if master_id not in master_ids:
                invalid_schedules.append(sched.get("id"))
        
        if invalid_schedules:
            error_msg = f"Invalid schedule entries: {invalid_schedules}"
            logger.warning(f"⚠️ {error_msg}")
            stats.errors.append(error_msg)
        else:
            logger.info("✅ Data consistency OK")
    
    def get_masters(self) -> List[Dict[str, Any]]:
        """Get cached masters data"""
        if not self._masters_data or self.should_sync():
            self.sync_all()
        return self._masters_data or []
    
    def get_services(self) -> List[Dict[str, Any]]:
        """Get cached services data"""
        if not self._services_data or self.should_sync():
            self.sync_all()
        return self._services_data or []
    
    def get_schedule(self, master_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cached schedule data, optionally filtered by master"""
        if not self._schedule_data or self.should_sync():
            self.sync_all()
        
        if not self._schedule_data:
            return []
        
        if master_id:
            return [s for s in self._schedule_data if s.get("master_id") == master_id]
        return self._schedule_data
    
    def get_bookings(self, master_id: Optional[str] = None, 
                     date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cached bookings data, optionally filtered"""
        if not self._bookings_data or self.should_sync():
            self.sync_all()
        
        if not self._bookings_data:
            return []
        
        result = self._bookings_data
        
        if master_id:
            result = [b for b in result if b.get("master_id") == master_id]
        
        if date:
            result = [b for b in result if b.get("date") == date]
        
        return result
    
    def get_calendar_events(self, master_id: Optional[str] = None) -> List[Dict]:
        """Get calendar events, optionally filtered by master"""
        if not self._calendar_events or self.should_sync():
            self.sync_all()
        
        if not self._calendar_events:
            return []
        
        if master_id:
            # Filter events by master_id that was added during sync
            return [e for e in self._calendar_events 
                   if e.get("_master_id") == master_id]
        
        return self._calendar_events
    
    def search_masters(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search masters by keyword in name or bio
        
        Args:
            keyword: Search keyword (case-insensitive)
        
        Returns:
            List of matching masters
        """
        masters = self.get_masters()
        keyword_lower = keyword.lower()
        
        results = []
        for master in masters:
            name = (master.get("name") or "").lower()
            bio = (master.get("bio") or "").lower()
            specialization = (master.get("specialization") or "").lower()
            
            if (keyword_lower in name or 
                keyword_lower in bio or 
                keyword_lower in specialization):
                results.append(master)
        
        return results
    
    def get_available_slots(self, master_id: str, 
                           date: str, 
                           duration_minutes: int = 60) -> List[Dict]:
        """
        Get available time slots for a master on specific date
        
        Combines:
        - Master schedule (from Sheets)
        - Existing bookings (from Sheets)
        - Calendar events (from Calendar)
        
        Args:
            master_id: Master ID
            date: Date in YYYY-MM-DD format
            duration_minutes: Required duration
        
        Returns:
            List of available slots
        """
        from datetime import datetime as dt, time
        
        # Get master schedule
        schedules = [s for s in self.get_schedule(master_id) 
                    if s.get("is_working") in ["TRUE", "true", True]]
        
        if not schedules:
            logger.warning(f"No schedule for master {master_id}")
            return []
        
        # Get bookings for this date
        bookings = self.get_bookings(master_id, date)
        
        # Get calendar events for this master on this date
        cal_events = self.get_calendar_events(master_id)
        
        # Generate slots
        slots = []
        
        for schedule in schedules:
            try:
                start_time = dt.strptime(schedule.get("start_time", "10:00"), "%H:%M").time()
                end_time = dt.strptime(schedule.get("end_time", "18:00"), "%H:%M").time()
                
                current = dt.combine(dt.strptime(date, "%Y-%m-%d").date(), start_time)
                end = dt.combine(dt.strptime(date, "%Y-%m-%d").date(), end_time)
                
                while current + timedelta(minutes=duration_minutes) <= end:
                    slot_end = current + timedelta(minutes=duration_minutes)
                    
                    # Check if slot is booked
                    is_booked = any(
                        b.get("date") == date and b.get("time") == current.strftime("%H:%M")
                        for b in bookings
                    )
                    
                    # Check calendar events
                    is_calendar_busy = any(
                        self._time_overlaps(current, slot_end, event)
                        for event in cal_events
                    )
                    
                    if not is_booked and not is_calendar_busy:
                        slots.append({
                            "date": date,
                            "time": current.strftime("%H:%M"),
                            "end_time": slot_end.strftime("%H:%M"),
                            "duration_minutes": duration_minutes
                        })
                    
                    current += timedelta(minutes=60)
                    
            except Exception as e:
                logger.error(f"Error generating slots: {e}")
        
        return slots
    
    @staticmethod
    def _time_overlaps(start1: datetime, end1: datetime, event: Dict) -> bool:
        """Check if time range overlaps with calendar event"""
        try:
            event_start = event.get("start", {}).get("dateTime")
            event_end = event.get("end", {}).get("dateTime")
            
            if not event_start or not event_end:
                return False
            
            # Parse ISO format datetime
            from dateutil import parser
            es = parser.parse(event_start)
            ee = parser.parse(event_end)
            
            return start1 < ee and end1 > es
            
        except Exception:
            return False
    
    @staticmethod
    def _rows_to_dicts(rows: List[List[Any]]) -> List[Dict[str, Any]]:
        """Convert sheet rows to list of dicts"""
        if not rows or len(rows) < 2:
            return []
        
        headers = rows[0]
        result = []
        
        for row in rows[1:]:
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = row[i] if i < len(row) else ""
            result.append(row_dict)
        
        return result


# Global sync service instance
_sync_service: Optional[DataSyncService] = None


def get_data_sync_service(sheets_client: Optional[GoogleSheetsClient] = None,
                         calendar_service=None) -> DataSyncService:
    """Get or create global sync service"""
    global _sync_service
    
    if _sync_service is None:
        if sheets_client is None:
            from src.config import get_config
            config = get_config()
            sheets_client = GoogleSheetsClient(
                "",
                config.google_spreadsheet_id
            )
        
        _sync_service = DataSyncService(sheets_client, calendar_service)
    
    return _sync_service
