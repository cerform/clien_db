from src.db.repositories.calendar_repo import CalendarRepo
from src.db.repositories.bookings_repo import BookingsRepo
from src.db.repositories.clients_repo import ClientsRepo
from src.services.calendar_service import CalendarService
from src.config.env_loader import load_env
from src.config.config import Config
from datetime import datetime

try:
    from src.services.slot_engine import create_pending_booking as pg_create_pending_booking
except Exception:
    pg_create_pending_booking = None

class BookingService:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sp_client = sheets_client
        self.spreadsheet_id = spreadsheet_id
        self.calendar_repo = CalendarRepo(sheets_client, spreadsheet_id)
        self.bookings_repo = BookingsRepo(sheets_client, spreadsheet_id)
        self.clients_repo = ClientsRepo(sheets_client, spreadsheet_id)
        self.calendar_service = CalendarService(sheets_client)

    def list_available_slots(self, date: str, master_id: str = None):
        # If Postgres slot engine is available, prefer it for fast and accurate results
        load_env()
        cfg = Config.from_env()
        if cfg.DATABASE_URL:
            try:
                # Slot engine returns slots with start/end datetimes
                from src.services.slot_engine import get_available_slots
                from datetime import datetime, timedelta
                start_dt = datetime.fromisoformat(f"{date}T00:00:00")
                end_dt = start_dt + timedelta(days=1)
                slots = get_available_slots(master_id if master_id else 'all', 60, start_dt, end_dt, caller_role='inka_llm_runtime')
                return [s for s in slots if not master_id or s.get('master_id') == master_id]
            except Exception:
                pass
        # Fallback to Sheets-based implementation
        slots = self.calendar_repo.list_slots()
        res = []
        for s in slots:
            if s.get("available", "").lower() in ("yes", "true", "1"):
                if (not master_id) or s.get("master_id") == master_id:
                    if s.get("date") == date:
                        res.append(s)
        return res

    def create_booking(self, client_telegram_id: int, client_name: str, client_phone: str, date: str, master_id: str, slot_start: str, slot_end: str, notes: str = ""):
        client = self.clients_repo.create_client(client_telegram_id, client_name, phone=client_phone, notes=notes)
        # If Postgres is configured, use slot_engine for pending booking + lock to ensure consistency
        load_env()
        cfg = Config.from_env()
        booking_id = None
        if getattr(cfg, 'DATABASE_URL', None) and pg_create_pending_booking:
            # Convert start/end to datetimes
            try:
                start_dt = datetime.fromisoformat(f"{date}T{slot_start}")
                end_dt = datetime.fromisoformat(f"{date}T{slot_end}")
                pending_id = pg_create_pending_booking(client_telegram_id, master_id, None, start_dt, end_dt, lock_holder=f"tg:{client_telegram_id}", caller_role='inka_booking_agent')
                if pending_id:
                    booking_id = pending_id
            except Exception:
                booking_id = None
        # Fallback to Sheets repo for compatibility
        if not booking_id:
            b = self.bookings_repo.create_booking(client["id"], master_id, date, slot_start, slot_end, status="pending")
            booking_id = b["id"]
        masters = self.sp_client.read_sheet(self.spreadsheet_id, "masters")
        calendar_id = None
        for m in masters:
            if m.get("id") == master_id:
                calendar_id = m.get("calendar_id")
                break
        if calendar_id and booking_id:
            start_iso = f"{date}T{slot_start}:00"
            end_iso = f"{date}T{slot_end}:00"
            try:
                event_id = self.calendar_service.push_booking_to_calendar(calendar_id, start_iso, end_iso, f"Tattoo - {client_name}")
                return {"booking_id": booking_id, "event_id": event_id}
            except Exception:
                pass
        return {"booking_id": booking_id, "event_id": None}

    def list_pending_bookings(self):
        try:
            from src.db.repositories.bookings_repo import BookingsRepo
            return self.bookings_repo.list_bookings(status='pending')
        except Exception:
            return []

    def confirm_pending_booking(self, pending_id: str, confirmed_by: str) -> bool:
        """Confirm a pending booking and write to bookings table. Return True on success."""
        db = None
        # If using Postgres for pending bookings, move to confirmed booking table
        from src.config.env_loader import load_env
        from src.config.config import Config
        load_env()
        cfg = Config.from_env()
        if getattr(cfg, 'DATABASE_URL', None):
            try:
                # Import lazily - allow graceful failure in environments without postgres client
                try:
                    from src.db.db_client import get_db
                except Exception:
                    return False
                db = get_db()
                conn = db.get_connection()
                cur = conn.cursor()
                # Get pending booking row
                cur.execute("SELECT user_id, master_id, service_id, start_time, end_time, locked_by FROM bookings_pending WHERE id = %s", (pending_id,))
                row = cur.fetchone()
                if not row:
                    return False
                user_id, master_id, service_id, start_time, end_time, locked_by = row
                # Create confirmed booking
                cur.execute("INSERT INTO bookings (pending_id, user_id, master_id, service_id, start_time, end_time, status, created_by) VALUES (%s, %s, %s, %s, %s, %s, 'confirmed', %s) RETURNING id",
                            (pending_id, user_id, master_id, service_id, start_time, end_time, confirmed_by))
                new_id = cur.fetchone()[0]
                # Optionally, push to calendar
                conn.commit()
                # Delete pending row or mark as processed
                cur.execute("DELETE FROM bookings_pending WHERE id = %s", (pending_id,))
                conn.commit()
                cur.close()
                return True
            except Exception as e:
                if db:
                    conn.rollback()
                return False
        # Sheets fallback: mark booking as confirmed in sheet
        try:
            # bookings_repo has update functionality
            from src.db.repositories.bookings_repo import BookingsRepo
            b = self.bookings_repo.get_booking_by_id(pending_id)
            if not b:
                return False
            success = self.bookings_repo.update_booking(b['id'], {'status': 'confirmed'})
            return success
        except Exception:
            return False

    def get_user_bookings(self, user_id: int, spreadsheet_id: str):
        """Get all bookings for a specific user by telegram ID"""
        # First, find the client by telegram_id
        clients = self.clients_repo.list_clients()
        client_id = None
        for client in clients:
            if str(client.get("telegram_id")) == str(user_id):
                client_id = client.get("id")
                break
        
        if not client_id:
            return []
        
        # Get all bookings for this client
        bookings = self.bookings_repo.list_bookings()
        user_bookings = []
        for booking in bookings:
            if booking.get("client_id") == client_id:
                user_bookings.append({
                    "id": booking.get("id"),
                    "date": booking.get("date"),
                    "time": f"{booking.get('slot_start')}-{booking.get('slot_end')}",
                    "description": booking.get("status", ""),
                    "status": booking.get("status", "pending")
                })
        
        return user_bookings
