import uuid
import datetime
from src.config.constants import SHEET_SERVICES
from src.db.schemas import build_row, pad_row_to_headers

class ServicesRepo:
    def __init__(self, sheets_client, spreadsheet_id):
        self.sc = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def list_services(self):
        return self.sc.read_sheet(self.spreadsheet_id, SHEET_SERVICES)

    def create_service(self, name: str, description: str, duration_min: int = 60, price_from: int = 0, price_to: int = 0, category: str = 'tattoo', active: bool = True):
        sid = str(uuid.uuid4())
        values = {
            'id': sid,
            'name': name,
            'description': description,
            'duration_min': duration_min,
            'price_from': price_from,
            'price_to': price_to,
            'category': category,
            'active': 'yes' if active else 'no'
        }
        row = build_row('services', values)
        row = pad_row_to_headers('services', row)
        try:
            self.sc.append_row(self.spreadsheet_id, SHEET_SERVICES, row)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Failed to append service row; proceeding in best-effort mode")
        return {"id": sid, "name": name}

    def update_service(self, service_id: str, data: dict) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_SERVICES)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == service_id:
                values = {
                    'id': r.get('id'),
                    'name': data.get('name', r.get('name')),
                    'description': data.get('description', r.get('description')),
                    'duration_min': data.get('duration_min', r.get('duration_min')),
                    'price_from': data.get('price_from', r.get('price_from')),
                    'price_to': data.get('price_to', r.get('price_to')),
                    'category': data.get('category', r.get('category')),
                    'active': data.get('active', r.get('active'))
                }
                new_row = build_row('services', values)
                new_row = pad_row_to_headers('services', new_row)
                try:
                    self.sc.update_row(self.spreadsheet_id, SHEET_SERVICES, idx, new_row)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("Failed to update service; proceeding in best-effort mode")
                return True
        return False

    def delete_service(self, service_id: str) -> bool:
        rows = self.sc.read_sheet(self.spreadsheet_id, SHEET_SERVICES)
        if not rows:
            return False
        for idx, r in enumerate(rows, start=1):
            if r.get('id') == service_id:
                try:
                    # Archive service row to deleted sheet
                    from src.services.db_admin import append_row
                    import json, datetime
                    archive_values = {
                        'sheet': 'services', 'row_id': service_id,
                        'deleted_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'deleted_by': '', 'data': json.dumps(r)
                    }
                    try:
                        from src.db.schemas import headers_for, build_row, pad_row_to_headers
                        hdrs = headers_for('deleted')
                        if hdrs:
                            r = build_row('deleted', archive_values)
                            r = pad_row_to_headers('deleted', r)
                            self.sc.append_row(self.spreadsheet_id, 'deleted', r)
                        else:
                            self.sc.append_row(self.spreadsheet_id, 'deleted', [archive_values['sheet'], archive_values['row_id'], archive_values['deleted_at'], archive_values['deleted_by'], archive_values['data']])
                    except Exception:
                        try:
                            append_row('deleted', archive_values)
                        except Exception:
                            self.sc.append_row(self.spreadsheet_id, 'deleted', [archive_values['sheet'], archive_values['row_id'], archive_values['deleted_at'], archive_values['deleted_by'], archive_values['data']])
                    # delete row
                    if hasattr(self.sc, 'delete_row'):
                        self.sc.delete_row(self.spreadsheet_id, SHEET_SERVICES, idx)
                    else:
                        blank_row = ['' for _ in range(len(r))]
                        self.sc.update_row(self.spreadsheet_id, SHEET_SERVICES, idx, blank_row)
                    return True
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception("Failed to delete/ archive service row; proceeding in best-effort mode")
                    return False
        return False
