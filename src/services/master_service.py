from src.db.repositories.masters_repo import MastersRepo

class MasterService:
    def __init__(self, sheets_client, spreadsheet_id):
        self.repo = MastersRepo(sheets_client, spreadsheet_id)

    def list_masters(self):
        return self.repo.list_masters()

    def add_master(self, name: str, calendar_id: str = ""):
        return self.repo.create_master(name, calendar_id)
