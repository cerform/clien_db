import logging
from typing import List, Optional, Dict

from src.db.sheets_client import SheetsClient
from src.db.schemas import build_row, pad_row_to_headers
from src.config.constants import SHEET_CLIENTS

logger = logging.getLogger(__name__)

# Default sheet name for configurations
SHEET_CONFIG = "config"


class ConfigRepo:
    def __init__(self, sheets_client: SheetsClient, spreadsheet_id: str):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_config(self) -> List[Dict]:
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_CONFIG)

    def get(self, key: str) -> Optional[Dict]:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_CONFIG)
        if not rows:
            return None
        for r in rows:
            if r.get("key") == key:
                return r
        return None

    def set(self, key: str, value: str, description: str = "") -> Dict:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_CONFIG)
        if not rows:
            # Append header handled elsewhere, append row as a list
            values = {'key': key, 'value': value, 'description': description}
            row = build_row('config', values)
            row = pad_row_to_headers('config', row)
            try:
                self.sc.append_row(self.spreadsheet_id, SHEET_CONFIG, row)
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Failed to append config row; proceeding in best-effort mode")
            return {"key": key, "value": value, "description": description}

        for idx, r in enumerate(rows, start=1):
            if r.get("key") == key:
                # Update row
                values = {'key': key, 'value': value, 'description': description}
                new_row = build_row('config', values)
                new_row = pad_row_to_headers('config', new_row)
                try:
                    self.sc.update_row(self.spreadsheet_id, SHEET_CONFIG, idx, new_row)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("Failed to update config row; proceeding in best-effort mode")
                return {"key": key, "value": value, "description": description}

        # If not found - append
        values = {'key': key, 'value': value, 'description': description}
        row = build_row('config', values)
        row = pad_row_to_headers('config', row)
        try:
            self.sc.append_row(self.spreadsheet_id, SHEET_CONFIG, row)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Failed to append config row; proceeding in best-effort mode")
        return {"key": key, "value": value, "description": description}


__all__ = ["ConfigRepo", "SHEET_CONFIG"]
