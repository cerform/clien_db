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
            if range_spec:
                range_name = f"{sheet_name}!{range_spec}"
            else:
                range_name = sheet_name
            
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
            
            body = {'values': [values]}
            logger.debug(f"   Request body: {body}")
            
            logger.info(f"📤 Sending append request to {sheet_name}...")
            response = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_name,
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
            body = {'values': rows}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_name,
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
            range_name = f"{sheet_name}!{cell}"
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
            range_name = f"{sheet_name}!{range_spec}"
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
            range_name = f"{sheet_name}!{row_index}:{row_index}"
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete row {row_index} from {sheet_name}: {e}")
            return False
