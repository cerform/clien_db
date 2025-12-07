import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.db.sheets_client import GoogleSheetsClient
from src.config import SHEET_CLIENTS

logger = logging.getLogger(__name__)

class ClientService:
    """Service for managing client data"""
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets = sheets_client
    
    def create_client(self, user_id: int, name: str, phone: str, email: str = "") -> bool:
        """Create a new client"""
        try:
            values = [
                str(user_id),
                name,
                phone,
                email,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                "active"
            ]
            
            success = self.sheets.append_row(SHEET_CLIENTS, values)
            if success:
                logger.info(f"Client created: {user_id} - {name}")
            return success
        except Exception as e:
            logger.error(f"Failed to create client: {e}")
            return False
    
    def get_client(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get client by user_id"""
        try:
            rows = self.sheets.get_sheet_values(SHEET_CLIENTS)
            if not rows:
                return None
            
            for row in rows[1:]:  # Skip header
                if len(row) > 0 and str(row[0]).strip() == str(user_id).strip():
                    return {
                        'user_id': row[0],
                        'name': row[1] if len(row) > 1 else '',
                        'phone': row[2] if len(row) > 2 else '',
                        'email': row[3] if len(row) > 3 else '',
                        'created_at': row[4] if len(row) > 4 else '',
                        'status': row[5] if len(row) > 5 else 'active'
                    }
            return None
        except Exception as e:
            logger.error(f"Failed to get client: {e}")
            return None
    
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Get all clients"""
        try:
            rows = self.sheets.get_sheet_values(SHEET_CLIENTS)
            if not rows:
                return []
            
            clients = []
            for row in rows[1:]:  # Skip header
                if len(row) > 0:
                    clients.append({
                        'user_id': row[0],
                        'name': row[1] if len(row) > 1 else '',
                        'phone': row[2] if len(row) > 2 else '',
                        'email': row[3] if len(row) > 3 else '',
                        'created_at': row[4] if len(row) > 4 else '',
                        'status': row[5] if len(row) > 5 else 'active'
                    })
            return clients
        except Exception as e:
            logger.error(f"Failed to get all clients: {e}")
            return []
    
    def update_client(self, user_id: int, name: str = None, phone: str = None, email: str = None) -> bool:
        """Update client information"""
        try:
            client = self.get_client(user_id)
            if not client:
                return False
            
            row_idx = self.sheets.find_row(SHEET_CLIENTS, 0, user_id)
            if not row_idx:
                return False
            
            new_name = name if name else client['name']
            new_phone = phone if phone else client['phone']
            new_email = email if email else client['email']
            
            values = [
                client['user_id'],
                new_name,
                new_phone,
                new_email,
                client['created_at'],
                client['status']
            ]
            
            range_spec = f"A{row_idx}:F{row_idx}"
            success = self.sheets.update_range(SHEET_CLIENTS, range_spec, [values])
            if success:
                logger.info(f"Client updated: {user_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to update client: {e}")
            return False
    
    def client_exists(self, user_id: int) -> bool:
        """Check if client exists"""
        return self.get_client(user_id) is not None
