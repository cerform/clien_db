from src.db.repositories.clients_repo import ClientsRepo

class ClientService:
    def __init__(self, sheets_client, spreadsheet_id):
        self.repo = ClientsRepo(sheets_client, spreadsheet_id)

    def register_client(self, telegram_id: int, name: str, phone: str = "", email: str = ""):
        existing = [c for c in self.repo.list_clients() if c.get("telegram_id") == str(telegram_id)]
        if existing:
            return existing[0]
        return self.repo.create_client(telegram_id, name, phone, email)
