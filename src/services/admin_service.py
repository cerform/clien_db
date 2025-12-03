from src.db.repositories.clients_repo import ClientsRepo
from src.db.repositories.masters_repo import MastersRepo
from src.db.repositories.bookings_repo import BookingsRepo

class AdminService:
    def __init__(self, sheets_client, spreadsheet_id):
        self.clients = ClientsRepo(sheets_client, spreadsheet_id)
        self.masters = MastersRepo(sheets_client, spreadsheet_id)
        self.bookings = BookingsRepo(sheets_client, spreadsheet_id)

    def list_clients(self):
        return self.clients.list_clients()

    def list_masters(self):
        return self.masters.list_masters()

    def list_bookings(self):
        return self.bookings.list_bookings()
