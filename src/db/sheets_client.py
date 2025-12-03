import logging
from typing import List, Dict, Any, Optional
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google.api_discovery import build
from pathlib import Path

logger = logging.getLogger(__name__)

# Google API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar'
]

class GoogleSheetsClient:
    """Client for working with Google Sheets API"""
    
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        Initialize Google Sheets client
        
        Args:
            credentials_file: Path to Google Service Account credentials JSON
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.spreadsheet_id = spreadsheet_id
        self.credentials = self._load_credentials(credentials_file)
        self.service = self._build_service()
    
    def _load_credentials(self, credentials_file: str) -> Credentials:
        """Load credentials from JSON file"""
        if not Path(credentials_file).exists():
            raise FileNotFoundError(f"Credentials file not found: {credentials_file}")
        
        try:
            credentials = Credentials.from_service_account_file(
                credentials_file,
                scopes=SCOPES
            )
            logger.info(f"Credentials loaded from {credentials_file}")
            return credentials
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            raise
    
    def _build_service(self):
        """Build Google Sheets API service"""
        try:
            service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Google Sheets service built successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to build Sheets service: {e}")
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
            logger.error(f"Failed to get sheet values from {sheet_name}: {e}")
            return []
    
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
            body = {'values': [values]}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"Row appended to {sheet_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to append row to {sheet_name}: {e}")
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
            logger.error(f"Failed to update cell {cell} in {sheet_name}: {e}")
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
            logger.error(f"Failed to update range {range_spec} in {sheet_name}: {e}")
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
            logger.error(f"Failed to find row in {sheet_name}: {e}")
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
            # This requires building a more complex request with batchUpdate
            # For now, we'll clear the row instead
            range_name = f"{sheet_name}!{row_index}:{row_index}"
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete row {row_index} from {sheet_name}: {e}")
            return False
