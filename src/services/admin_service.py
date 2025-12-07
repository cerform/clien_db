import logging
from typing import List, Dict, Any
from src.db.sheets_client import GoogleSheetsClient
from src.services.client_service import ClientService
from src.services.master_service import MasterService
from src.services.booking_service import BookingService

logger = logging.getLogger(__name__)

class AdminService:
    """Service for admin operations"""
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets = sheets_client
        self.clients = ClientService(sheets_client)
        self.masters = MasterService(sheets_client)
        self.bookings = BookingService(sheets_client)
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            total_clients = len(self.clients.get_all_clients())
            total_masters = len(self.masters.get_all_masters())
            
            return {
                'total_clients': total_clients,
                'total_masters': total_masters,
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            return {}
    
    def export_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export all data"""
        try:
            return {
                'clients': self.clients.get_all_clients(),
                'masters': self.masters.get_all_masters(status=None),
            }
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return {}
