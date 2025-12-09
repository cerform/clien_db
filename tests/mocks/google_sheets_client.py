from typing import List, Any, Dict
import logging
logger = logging.getLogger(__name__)


class MockGoogleSheetsClient:
    def __init__(self, initial_data: Dict[str, List[List[Any]]] = None):
        self._data = initial_data or {}
        # Ensure headers
        for k, v in list(self._data.items()):
            if not v:
                self._data[k] = [[]]

    def get_sheet_values(self, sheet_name: str, range_spec: str = "") -> List[List[Any]]:
        key = sheet_name
        return self._data.get(key, [])

    def get_all_rows(self, sheet_name: str) -> List[List[Any]]:
        return self.get_sheet_values(sheet_name)

    def get_sheets_list(self) -> List[str]:
        return list(self._data.keys())

    def append_rows(self, sheet_name: str, rows: List[List[Any]]) -> bool:
        if sheet_name not in self._data:
            self._data[sheet_name] = []
        self._data[sheet_name].extend(rows)
        return True

    def append_row(self, sheet_name: str, values: List[Any]) -> bool:
        return self.append_rows(sheet_name, [values])

    def update_range(self, sheet_name: str, range_spec: str, values: List[List[Any]]) -> bool:
        # naive: replace entire sheet for simplicity
        self._data[sheet_name] = values
        return True

    def update_cell(self, sheet_name: str, cell: str, value: Any) -> bool:
        # naive cell update; parse cell like 'A1'
        sheet = self._data.get(sheet_name, [])
        if not sheet:
            return False
        # very simplified: A1 -> col 0, row 1
        try:
            col = ord(cell[0].upper()) - ord('A')
            row = int(cell[1:]) - 1
            while len(sheet) <= row:
                sheet.append([])
            row_data = sheet[row]
            while len(row_data) <= col:
                row_data.append('')
            row_data[col] = value
            return True
        except Exception as e:
            logger.debug(f"update_cell error: {e}")
            return False

    def create_sheet(self, sheet_name: str) -> bool:
        if sheet_name not in self._data:
            self._data[sheet_name] = []
        return True

    def find_row(self, sheet_name: str, column_index: int, value: Any):
        sheet = self._data.get(sheet_name, [])
        for idx, row in enumerate(sheet):
            if len(row) > column_index and row[column_index] == value:
                return idx + 1
        return None

    def delete_row(self, sheet_name: str, row_index: int) -> bool:
        sheet = self._data.get(sheet_name, [])
        idx = row_index - 1
        if 0 <= idx < len(sheet):
            sheet.pop(idx)
            return True
        return False
