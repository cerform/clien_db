"""
Compatibility layer: INKA admin tools for our project's services
This adapts the ADMIN_FUNCTIONS definitions from the `fix-e2e-test` branch
and maps the tool execution to our current AdminService / repos.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Copy a subset of ADMIN_FUNCTIONS definitions needed for remote tooling
ADMIN_FUNCTIONS = [
    {
        "name": "get_all_masters",
        "description": "Получить список всех мастеров салона с их данными",
        "parameters": {"type": "object", "properties": {"status_filter": {"type": "string", "enum": ["all", "active", "inactive"]}}, "required": []},
    },
    {
        "name": "add_master",
        "description": "Добавить нового мастера в салон",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "phone": {"type": "string"}, "specialization": {"type": "string"}, "telegram_id": {"type": "string"}, "experience": {"type": "string"}, "instagram": {"type": "string"}, "bio": {"type": "string"}, "calendar_id": {"type": "string"}}, "required": ["name", "specialization"]},
    },
    {
        "name": "edit_master",
        "description": "Редактировать данные мастера",
        "parameters": {"type": "object", "properties": {"master_id": {"type": "string"}, "name": {"type": "string"}, "phone": {"type": "string"}, "specialization": {"type": "string"}, "status": {"type": "string", "enum": ["active", "inactive"]}}, "required": ["master_id"]},
    },
    {
        "name": "get_all_services",
        "description": "Получить список всех услуг салона",
        "parameters": {"type": "object", "properties": {"category": {"type": "string"}}, "required": []},
    },
    {
        "name": "add_service",
        "description": "Добавить новую услугу в прайс-лист",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}, "price": {"type": "number"}, "duration": {"type": "integer"}, "category": {"type": "string"}}, "required": ["name", "price", "duration"]},
    },
    {
        "name": "get_all_clients",
        "description": "Получить список всех клиентов",
        "parameters": {"type": "object", "properties": {"search": {"type": "string"}, "limit": {"type": "integer"}}, "required": []},
    },
    {
        "name": "get_all_bookings",
        "description": "Получить список всех записей",
        "parameters": {"type": "object", "properties": {"status": {"type": "string", "enum": ["all", "pending", "confirmed", "completed", "cancelled"]}, "master_id": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}}, "required": []},
    },
    {
        "name": "create_booking",
        "description": "Создать новую запись клиента",
        "parameters": {"type": "object", "properties": {"client_id": {"type": "string"}, "client_name": {"type": "string"}, "client_phone": {"type": "string"}, "master_id": {"type": "string"}, "service_id": {"type": "string"}, "date": {"type": "string"}, "time": {"type": "string"}, "notes": {"type": "string"}}, "required": ["master_id", "service_id", "date", "time"]},
    },
    {
        "name": "get_master_availability",
        "description": "Проверить доступность мастера на определенную дату",
        "parameters": {"type": "object", "properties": {"master_id": {"type": "string"}, "date": {"type": "string"}}, "required": ["master_id", "date"]},
    },
    {
        "name": "get_statistics",
        "description": "Получить статистику салона",
        "parameters": {"type": "object", "properties": {"period": {"type": "string", "enum": ["today", "week", "month", "year", "all"]}}, "required": []},
    }
]


class INKAAdminTools:
    """Bridge adapter — map ADMIN_FUNCTIONS to local AdminService/MasterService/BookingService handlers"""
    def __init__(self, admin_services=None):
        # admin_services expects dict-like service instances (masters_service, services_service, clients_service, booking_service, calendar_service)
        self.services = admin_services or {}

    def execute_function(self, function_name: str, arguments: Dict) -> Dict[str, Any]:
        """Execute function by name using mapped services"""
        try:
            if function_name == "get_all_masters":
                masters = self.services.get("masters_service").list_masters()
                status_filter = arguments.get("status_filter", "all")
                if status_filter != "all":
                    masters = [m for m in masters if (m.get("active") == ("yes" if status_filter == "active" else "no")) or (m.get("status") == status_filter)]
                return masters

            if function_name == "add_master":
                ms = self.services.get("masters_service")
                args = arguments
                # masters_service.add_master(name, calendar_id='')
                name = args.get("name")
                calendar_id = args.get("calendar_id", "")
                res = ms.add_master(name, calendar_id)
                return {"success": True, "message": f"Created master {res.get('id', res.get('name'))}"}

            if function_name == "edit_master":
                ms = self.services.get("masters_service")
                master_id = arguments.get("master_id")
                updates = {k: v for k, v in arguments.items() if k != "master_id"}
                success = ms.repo.update_master(master_id, updates) if hasattr(ms, 'repo') else False
                return {"success": success}

            if function_name == "get_all_services":
                services = self.services.get("services_service").list_services()
                category = arguments.get("category")
                if category:
                    services = [s for s in services if s.get("category") == category]
                return services

            if function_name == "add_service":
                svc = self.services.get("services_service")
                name = arguments.get("name")
                description = arguments.get("description", "")
                price = arguments.get("price", 0)
                duration = arguments.get("duration", 60)
                res = svc.create_service(name, description, duration, price, 0, arguments.get("category", 'tattoo'))
                return {"success": True, "message": f"Service created: {res.get('id')}", "service": res}

            if function_name == "get_all_clients":
                clients = self.services.get("clients_service").repo.list_clients()
                search = arguments.get("search", "").lower()
                limit = arguments.get("limit", 100)
                if search:
                    clients = [c for c in clients if search in c.get("name", "").lower() or search in c.get("phone", "").lower()]
                return clients[:limit]

            if function_name == "get_all_bookings":
                bookings = self.services.get("bookings_service").repo.list_bookings()
                status = arguments.get("status", "all")
                master_id = arguments.get("master_id")
                date_from = arguments.get("date_from")
                date_to = arguments.get("date_to")
                if status != "all":
                    bookings = [b for b in bookings if b.get("status") == status]
                if master_id:
                    bookings = [b for b in bookings if b.get("master_id") == master_id]
                if date_from:
                    bookings = [b for b in bookings if b.get("date", "") >= date_from]
                if date_to:
                    bookings = [b for b in bookings if b.get("date", "") <= date_to]
                # enrich
                masters_map = {m.get('id'): m for m in self.services.get('masters_service').repo.list_masters()}
                services_map = {s.get('id'): s for s in self.services.get('services_service').list_services()}
                clients_map = {c.get('id'): c for c in self.services.get('clients_service').repo.list_clients()}
                for b in bookings:
                    b['master_name'] = masters_map.get(b.get('master_id', ''), {}).get('name', 'Неизвестный')
                    b['service_name'] = services_map.get(b.get('service_id', ''), {}).get('name', 'Неизвестная')
                    b['client_name'] = clients_map.get(b.get('client_id', ''), {}).get('name', 'Клиент')
                return bookings

            if function_name == "create_booking":
                bs = self.services.get("booking_service")
                # expected fields: client_id or client_name/phone, master_id, service_id, date, time
                args = arguments
                client_id = args.get("client_id")
                client_name = args.get("client_name") or "Client"
                client_phone = args.get("client_phone") or ""
                if not client_id and client_name and client_phone:
                    c_res = self.services.get("clients_service").repo.create_client(client_phone, client_name, client_phone)
                    client_id = c_res.get('id')
                # slot start & end
                slot_start = args.get("time")
                duration_mins = args.get("duration", 60)
                # compute slot end
                try:
                    hh, mm = map(int, slot_start.split(":"))
                    from datetime import datetime, timedelta
                    dt = datetime.strptime(args.get("date"), "%Y-%m-%d").replace(hour=hh, minute=mm)
                    slot_end = (dt + timedelta(minutes=duration_mins)).strftime("%H:%M")
                except Exception:
                    slot_end = args.get('end_time', slot_start)
                # Use INKAProcessor S3 path via AdvancedINKA wrapper (already in advanced_inka)
                # If booking service isn't present, fallback to direct call
                if bs:
                    try:
                        from src.ai.inka_processor import INKAProcessor
                        ip = INKAProcessor(None, services={'booking_service': bs})
                        slot = {'date': args.get('date'), 'time': slot_start, 'end_time': slot_end, 'master_id': args.get('master_id'), 'service': args.get('service_id') or args.get('service')}
                        out = ip.stage_3_reserve_slot(slot, int(client_id) if client_id else 0, client_name, client_phone, args.get('notes', ''))
                        return out
                    except Exception:
                        pass
                res = bs.create_booking(int(client_id) if client_id else 0, client_name, client_phone, args.get("date"), args.get("master_id"), slot_start, slot_end or slot_start, args.get("notes", ""))
                return {"success": bool(res.get('booking_id')), "booking_id": res.get('booking_id'), "event_id": res.get('event_id'), "message": "Created via fallback"}

            if function_name == "get_master_availability":
                bs = self.services.get("booking_service")
                res = bs.list_available_slots(arguments.get("date"), arguments.get("master_id"))
                return {"available_slots": res}

            if function_name == "get_statistics":
                # Basic stats using admin_service
                admin = self.services.get("admin_service")
                period = arguments.get("period", "all")
                # re-use aggregator from ai_orchestrator if present
                try:
                    # Fallback to admin quick stats
                    result = admin.list_bookings()
                    # compute simple statistics
                    from collections import Counter
                    completed = [b for b in result if b.get('status') == 'completed']
                    revenue = sum(float(b.get('price', 0) or 0) for b in completed)
                    return {"period": period, "total_bookings": len(result), "completed_bookings": len(completed), "total_revenue": revenue}
                except Exception as ex:
                    return {"error": str(ex)}

            return {"error": f"Unknown function: {function_name}"}

        except Exception as e:
            logger.error(f"INKAAdminTools execute error: {e}")
            return {"error": str(e)}


# Factory

def get_admin_tools(admin_services: Dict[str, Any] = None):
    if admin_services is None:
        # initialize minimal services by default
        from src.config.config import Config
        from src.services.admin_service import AdminService
        from src.services.master_service import MasterService
        from src.services.client_service import ClientService
        from src.services.booking_service import BookingService
        from src.db.repositories.services_repo import ServicesRepo
        from src.config.config import Config as ProjectConfig
        cfg = ProjectConfig.from_env()
        # create services using sheets client - use the global sheets_client from web.app or build new
        try:
            from src.web.app import db_manager, sheets_client
            spreadsheet_id = cfg.SPREADSHEET_ID
            services = {}
            services['masters_service'] = MasterService(sheets_client, spreadsheet_id)
            services['clients_service'] = ClientService(sheets_client, spreadsheet_id)
            services['services_service'] = ServicesRepo(sheets_client, spreadsheet_id)
            services['bookings_service'] = BookingService(sheets_client, spreadsheet_id)
            services['admin_service'] = AdminService(sheets_client, spreadsheet_id)
            return INKAAdminTools(services)
        except Exception as _e:
            logger.warning(f"Failed to init admin services: {_e}")
            return INKAAdminTools(admin_services)

    return INKAAdminTools(admin_services)
