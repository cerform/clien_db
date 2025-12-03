import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.db.sheets_client import GoogleSheetsClient
from src.config import SHEET_MASTERS

logger = logging.getLogger(__name__)

class MasterService:
    """Service for managing master data"""
    
    # Новая структура БД
    SHEET_NAME = "Мастера"
    HEADERS = [
        "ID", "Имя", "Специальность", "Опыт (лет)", "Рейтинг",
        "Телефон", "Instagram", "Цена за сеанс (руб)", "Статус", "Описание"
    ]
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets = sheets_client
    
    def create_master(self, name: str, specialization: str, phone: str, calendar_id: str = "") -> bool:
        """Create a new master"""
        try:
            values = [
                name,
                specialization,
                phone,
                calendar_id,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                "active"
            ]
            
            success = self.sheets.append_row(SHEET_MASTERS, values)
            if success:
                logger.info(f"Master created: {name}")
            return success
        except Exception as e:
            logger.error(f"Failed to create master: {e}")
            return False
    
    def get_master(self, master_id: int) -> Optional[Dict[str, Any]]:
        """Get master by ID"""
        try:
            rows = self.sheets.get_sheet_values(SHEET_MASTERS)
            if not rows:
                return None
            
            for row in rows[1:]:  # Skip header
                if len(row) > 0 and str(row[0]).strip() == str(master_id).strip():
                    return {
                        'id': row[0],
                        'name': row[1] if len(row) > 1 else '',
                        'specialization': row[2] if len(row) > 2 else '',
                        'phone': row[3] if len(row) > 3 else '',
                        'calendar_id': row[4] if len(row) > 4 else '',
                        'created_at': row[5] if len(row) > 5 else '',
                        'status': row[6] if len(row) > 6 else 'active'
                    }
            return None
        except Exception as e:
            logger.error(f"Failed to get master: {e}")
            return None
    
    def get_all_masters(self, status: str = "active") -> List[Dict[str, Any]]:
        """Get all masters"""
        try:
            rows = self.sheets.get_sheet_values(SHEET_MASTERS)
            if not rows:
                return []
            
            masters = []
            for row in rows[1:]:  # Skip header
                if len(row) > 0:
                    master_status = row[6] if len(row) > 6 else 'active'
                    if status is None or master_status == status:
                        masters.append({
                            'id': row[0],
                            'name': row[1] if len(row) > 1 else '',
                            'specialization': row[2] if len(row) > 2 else '',
                            'phone': row[3] if len(row) > 3 else '',
                            'calendar_id': row[4] if len(row) > 4 else '',
                            'created_at': row[5] if len(row) > 5 else '',
                            'status': master_status
                        })
            return masters
        except Exception as e:
            logger.error(f"Failed to get all masters: {e}")
            return []
    
    def get_master_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get master by name"""
        try:
            row_idx = self.sheets.find_row(SHEET_MASTERS, 1, name)
            if row_idx:
                rows = self.sheets.get_sheet_values(SHEET_MASTERS)
                row = rows[row_idx - 1]
                return {
                    'id': row[0],
                    'name': row[1] if len(row) > 1 else '',
                    'specialization': row[2] if len(row) > 2 else '',
                    'phone': row[3] if len(row) > 3 else '',
                    'calendar_id': row[4] if len(row) > 4 else '',
                    'created_at': row[5] if len(row) > 5 else '',
                    'status': row[6] if len(row) > 6 else 'active'
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get master by name: {e}")
            return None
    
    def update_master(self, master_id: int, **kwargs) -> bool:
        """Update master information"""
        try:
            master = self.get_master(master_id)
            if not master:
                return False
            
            row_idx = self.sheets.find_row(SHEET_MASTERS, 0, master_id)
            if not row_idx:
                return False
            
            values = [
                master['id'],
                kwargs.get('name', master['name']),
                kwargs.get('specialization', master['specialization']),
                kwargs.get('phone', master['phone']),
                kwargs.get('calendar_id', master['calendar_id']),
                master['created_at'],
                kwargs.get('status', master['status'])
            ]
            
            range_spec = f"A{row_idx}:G{row_idx}"
            success = self.sheets.update_range(SHEET_MASTERS, range_spec, [values])
            if success:
                logger.info(f"Master updated: {master_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to update master: {e}")
            return False
