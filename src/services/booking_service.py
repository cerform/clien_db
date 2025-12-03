from src.db.repositories.calendar_repo import CalendarRepo
from src.db.repositories.bookings_repo import BookingsRepo
from src.db.repositories.clients_repo import ClientsRepo
from src.services.calendar_service import CalendarService

class BookingService:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sp_client = sheets_client
        self.spreadsheet_id = spreadsheet_id
        self.calendar_repo = CalendarRepo(sheets_client, spreadsheet_id)
        self.bookings_repo = BookingsRepo(sheets_client, spreadsheet_id)
        self.clients_repo = ClientsRepo(sheets_client, spreadsheet_id)
        self.calendar_service = CalendarService(sheets_client)

    def list_available_slots(self, date: str, master_id: str = None):
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
        b = self.bookings_repo.create_booking(client["id"], master_id, date, slot_start, slot_end, status="pending")
        masters = self.sp_client.read_sheet(self.spreadsheet_id, "masters")
        calendar_id = None
        for m in masters:
            if m.get("id") == master_id:
                calendar_id = m.get("calendar_id")
                break
        if calendar_id:
            start_iso = f"{date}T{slot_start}:00"
            end_iso = f"{date}T{slot_end}:00"
            try:
                event_id = self.calendar_service.push_booking_to_calendar(calendar_id, start_iso, end_iso, f"Tattoo - {client_name}")
                return {"booking_id": b["id"], "event_id": event_id}
            except Exception:
                pass
        return {"booking_id": b["id"], "event_id": None}

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
