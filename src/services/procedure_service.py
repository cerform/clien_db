"""
Сервис для работы с процедурами/услугами в Google Sheets
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ProcedureService:
    """Сервис для управления процедурами"""
    
    def __init__(self, sheets_client):
        """
        Инициализация сервиса
        
        Args:
            sheets_client: Google Sheets клиент
        """
        self.sheets = sheets_client
    
    def get_all_procedures(self) -> List[Dict]:
        """Получить все процедуры/услуги"""
        try:
            values = self.sheets.get_range("Услуги!A2:H")
            
            procedures = []
            for row in values:
                if len(row) >= 2:
                    procedure = {
                        "id": row[0] if len(row) > 0 else "",
                        "name": row[1] if len(row) > 1 else "",
                        "description": row[2] if len(row) > 2 else "",
                        "price": row[3] if len(row) > 3 else "",
                        "duration": row[4] if len(row) > 4 else "",
                        "category": row[5] if len(row) > 5 else "",
                        "popularity": row[6] if len(row) > 6 else "",
                        "active": row[7] if len(row) > 7 else ""
                    }
                    procedures.append(procedure)
            
            return procedures
        
        except Exception as e:
            logger.error(f"Error getting procedures: {e}")
            return []
    
    def get_procedure(self, procedure_id: str) -> Optional[Dict]:
        """Получить процедуру по ID"""
        try:
            procedures = self.get_all_procedures()
            
            for proc in procedures:
                if proc.get('id') == procedure_id or proc.get('name') == procedure_id:
                    return proc
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting procedure {procedure_id}: {e}")
            return None
    
    def add_procedure(self, procedure_data: Dict) -> bool:
        """Добавить новую процедуру"""
        try:
            row = [
                procedure_data.get("id", ""),
                procedure_data.get("name", ""),
                procedure_data.get("description", ""),
                procedure_data.get("price", ""),
                procedure_data.get("duration", ""),
                procedure_data.get("category", ""),
                procedure_data.get("popularity", ""),
                procedure_data.get("active", "")
            ]
            
            self.sheets.append_row("Услуги", row)
            logger.info(f"Procedure added: {procedure_data.get('name', 'Unknown')}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding procedure: {e}")
            return False
    
    def get_active_procedures(self) -> List[Dict]:
        """Получить только активные процедуры"""
        try:
            procedures = self.get_all_procedures()
            return [p for p in procedures if p.get('active', '').upper() in ['ДА', 'YES', 'TRUE']]
        
        except Exception as e:
            logger.error(f"Error getting active procedures: {e}")
            return []
    
    def get_procedures_by_category(self, category: str) -> List[Dict]:
        """Получить процедуры по категории"""
        try:
            procedures = self.get_all_procedures()
            return [p for p in procedures if p.get('category', '').lower() == category.lower()]
        
        except Exception as e:
            logger.error(f"Error getting procedures by category: {e}")
            return []
