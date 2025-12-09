import logging
import os
from typing import List, Dict, Any, Optional
from google.auth import default as google_auth_default
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Google API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar'
]


class GoogleSheetsClient:
    """Client for working with Google Sheets API using Cloud Run's native Service Account"""
    
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        Initialize Google Sheets client
        
        Args:
            credentials_file: Path to service account JSON file (optional). If None, uses Cloud Run's native Service Account
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.spreadsheet_id = spreadsheet_id
        self.credentials_file = credentials_file
        self.credentials = self._load_credentials()
        self.service = self._build_service()
        # Aliases to try for sheet names when a provided sheet name doesn't exist.
        self.sheet_aliases = {
            'clients': ['Clients', 'Клиенты'],
            'masters': ['Masters', 'Мастера'],
            'bookings': ['Bookings', 'Записи'],
            'services': ['Services', 'Услуги'],
            'schedule': ['Schedule', 'Расписание'],
            'pricing': ['Pricing', 'Прайс-лист'],
            'reviews': ['Reviews', 'Отзывы'],
        }
    
    def _load_credentials(self):
        """Load credentials from file or Cloud Run's native Service Account"""
        
        # If credentials_file is provided and exists, use it
        if self.credentials_file and os.path.exists(self.credentials_file):
            logger.info(f"🔍 Loading credentials from file: {self.credentials_file}...")
            try:
                credentials = Credentials.from_service_account_file(
                    self.credentials_file,
                    scopes=SCOPES
                )
                logger.info(f"✅ Successfully loaded credentials from file")
                return credentials
            except Exception as e:
                logger.error(f"❌ Failed to load credentials from file: {e}")
                raise
        
        # Otherwise use Cloud Run's native Service Account
        logger.info("🔍 Loading credentials using google.auth.default()...")
        
        try:
            credentials, project = google_auth_default(scopes=SCOPES)
            logger.info(f"✅ Successfully loaded credentials from environment")
            logger.info(f"   Project: {project}")
            logger.info(f"   Credentials type: {type(credentials).__name__}")
            return credentials
        except Exception as e:
            logger.error(f"❌ Failed to load credentials: {e}")
            raise
    
    def _build_service(self):
        """Build Google Sheets API service"""
        try:
            service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("✅ Google Sheets service built successfully")
            return service
        except Exception as e:
            logger.error(f"❌ Failed to build Sheets service: {e}")
            raise
    
    def get_sheet_values(self, sheet_name: str, range_spec: str = "") -> List[List[Any]]:
        """
        Get values from a sheet
        
        Args:
            sheet_name: Name of the sheet tab
            range_spec: Range specification (e.g., "A1:D10")
        
        Returns:
            List of rows with values
        """
        try:
            sheet_name_resolved = self._resolve_sheet_name(sheet_name)
            if range_spec:
                range_name = f"{sheet_name_resolved}!{range_spec}"
            else:
                range_name = sheet_name_resolved
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            return values
        except Exception as e:
            logger.error(f"❌ Failed to get sheet values from {sheet_name}: {e}")
            return []
    
    def get_all_rows(self, sheet_name: str) -> List[List[Any]]:
        """
        Get all rows from a sheet (convenience method)
        
        Args:
            sheet_name: Name of the sheet tab
        
        Returns:
            List of rows with values
        """
        return self.get_sheet_values(sheet_name)

    def get_sheets_list(self) -> List[str]:
        """
        Return list of sheet/tab names in the spreadsheet
        """
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            names = [s.get('properties', {}).get('title', '') for s in sheets]
            return names
        except Exception as e:
            logger.error(f"❌ Failed to get sheets list: {e}")
            return []

    def _resolve_sheet_name(self, sheet_name: str) -> str:
        """
        Resolve a sheet name to an existing sheet name by trying aliases.
        If the passed sheet_name exists, return it. Otherwise try common aliases (EN/RU).
        """
        try:
            # If it exists as provided, just return
            if self._sheet_exists(sheet_name):
                return sheet_name
            key = sheet_name.strip().lower()
            # Try known aliases if key exists
            if key in self.sheet_aliases:
                for alt in self.sheet_aliases[key]:
                    if self._sheet_exists(alt):
                        logger.info(f"Resolved sheet name '{sheet_name}' -> '{alt}'")
                        return alt
            # Try to find any sheet that case-insensitively matches
            for s in self.get_sheets_list():
                if s.strip().lower() == key:
                    return s
            # As a fallback, if the original has Cyrillic -> English translations
            for names in self.sheet_aliases.values():
                for alt in names:
                    if alt.strip().lower() == key:
                        # find the counterpart that's present
                        for cand in names:
                            if self._sheet_exists(cand):
                                return cand
            return sheet_name
        except Exception as e:
            logger.debug(f"Failed to resolve sheet name {sheet_name}: {e}")
            return sheet_name
    
    def append_row(self, sheet_name: str, values: List[Any]) -> bool:
        """
        Append a row to a sheet
        
        Args:
            sheet_name: Name of the sheet tab
            values: List of values to append
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"🔍 append_row() called for sheet '{sheet_name}' with {len(values)} values")
            logger.debug(f"   Values: {values}")
            
            # Validate inputs
            if not sheet_name or sheet_name.strip() == "":
                logger.error("❌ sheet_name is empty!")
                return False
            
            if not values or len(values) == 0:
                logger.error("❌ values list is empty!")
                return False
            
            sheet_name_resolved = self._resolve_sheet_name(sheet_name)
            body = {'values': [values]}
            logger.debug(f"   Request body: {body}")
            
            logger.info(f"📤 Sending append request to {sheet_name}...")
            response = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_name_resolved,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"✅ Append successful!")
            logger.debug(f"   Response: {response}")
            
            cells_updated = response.get('updates', {}).get('updatedCells', 1)
            logger.info(f"✅ Row appended to {sheet_name}: {cells_updated} cells updated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to append row to {sheet_name}")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error message: {str(e)}")
            logger.error(f"   sheet_name: {sheet_name}")
            logger.error(f"   values length: {len(values) if values else 0}")
            logger.error(f"   spreadsheet_id: {self.spreadsheet_id[:20]}...")
            logger.exception(f"   Full traceback:")
            return False
            return False
    
    def append_rows(self, sheet_name: str, rows: List[List[Any]]) -> bool:
        """
        Append multiple rows to a sheet
        
        Args:
            sheet_name: Name of the sheet tab
            rows: List of rows (each row is a list of values)
        
        Returns:
            True if successful
        """
        try:
            sheet_name_resolved = self._resolve_sheet_name(sheet_name)
            body = {'values': rows}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_name_resolved,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"✅ {len(rows)} rows appended to {sheet_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to append rows to {sheet_name}: {e}")
            return False
    
    def update_cell(self, sheet_name: str, cell: str, value: Any) -> bool:
        """
        Update a single cell
        
        Args:
            sheet_name: Name of the sheet tab
            cell: Cell address (e.g., "A1")
            value: New value
        
        Returns:
            True if successful
        """
        try:
            sheet_name_resolved = self._resolve_sheet_name(sheet_name)
            range_name = f"{sheet_name_resolved}!{cell}"
            body = {'values': [[value]]}
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update cell {cell} in {sheet_name}: {e}")
            return False
    
    def update_range(self, sheet_name: str, range_spec: str, values: List[List[Any]]) -> bool:
        """
        Update a range of cells
        
        Args:
            sheet_name: Name of the sheet tab
            range_spec: Range specification (e.g., "A1:D10")
            values: List of rows with values
        
        Returns:
            True if successful
        """
        try:
            sheet_name_resolved = self._resolve_sheet_name(sheet_name)
            range_name = f"{sheet_name_resolved}!{range_spec}"
            body = {'values': values}
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update range {range_spec} in {sheet_name}: {e}")
            return False
    
    def find_row(self, sheet_name: str, column_index: int, value: Any) -> Optional[int]:
        """
        Find row index by value in column
        
        Args:
            sheet_name: Name of the sheet tab
            column_index: Column index (0-based)
            value: Value to find
        
        Returns:
            Row index (1-based) or None if not found
        """
        try:
            values = self.get_sheet_values(sheet_name)
            for row_idx, row in enumerate(values):
                if len(row) > column_index and str(row[column_index]).strip() == str(value).strip():
                    return row_idx + 1
            return None
        except Exception as e:
            logger.error(f"❌ Failed to find row in {sheet_name}: {e}")
            return None
    
    def delete_row(self, sheet_name: str, row_index: int) -> bool:
        """
        Delete a row from a sheet
        
        Args:
            sheet_name: Name of the sheet tab
            row_index: Row index (1-based)
        
        Returns:
            True if successful
        """
        try:
            sheet_name_resolved = self._resolve_sheet_name(sheet_name)
            range_name = f"{sheet_name_resolved}!{row_index}:{row_index}"
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete row {row_index} from {sheet_name}: {e}")
            return False

    def create_sheet(self, sheet_name: str) -> bool:
        """
        Create a new sheet/tab in the spreadsheet if it doesn't already exist.
        """
        try:
            if self._sheet_exists(sheet_name):
                logger.info(f"Sheet '{sheet_name}' already exists")
                return True
            body = {
                'requests': [
                    { 'addSheet': { 'properties': { 'title': sheet_name } } }
                ]
            }
            self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
            logger.info(f"✅ Sheet '{sheet_name}' created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create sheet '{sheet_name}': {e}")
            return False

    def update_client(self, client_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update client data by client_id
        
        Args:
            client_id: Client UUID
            update_data: Dict with fields to update (name, phone, email, notes)
        
        Returns:
            True if successful
        """
        try:
            # Получаем все данные клиентов
            values = self.get_sheet_values("Clients")
            if not values:
                logger.error("❌ No data in Clients sheet")
                return False
            
            # Ищем строку с нужным client_id (колонка A = индекс 0)
            row_index = None
            for idx, row in enumerate(values):
                if len(row) > 0 and row[0] == client_id:
                    row_index = idx + 1  # 1-based для Google Sheets
                    break
            
            if row_index is None:
                logger.error(f"❌ Client {client_id} not found")
                return False
            
            # Колонки: id(A), telegram_id(B), name(C), phone(D), email(E), notes(F), created_at(G), last_visit(H)
            column_map = {
                "name": "C",
                "phone": "D", 
                "email": "E",
                "notes": "F"
            }
            
            # Обновляем каждое поле
            for field, value in update_data.items():
                if field in column_map:
                    cell = f"{column_map[field]}{row_index}"
                    self.update_cell("Clients", cell, value)
                    logger.info(f"✅ Updated client {client_id}: {field} = {value[:50] if len(str(value)) > 50 else value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update client {client_id}: {e}")
            return False
