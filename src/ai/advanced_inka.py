"""
Compatibility wrapper: AdvancedINKA to provide remote branch's Assistant-style tools but delegate to our local services.
This enables the LLM function calling definitions used in the fix-e2e-test branch while routing actual operations to our services.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from src.ai.inka_admin_tools import get_admin_tools, ADMIN_FUNCTIONS


class AdvancedINKA:
    def __init__(self, admin_services: Dict[str, Any] = None, sheets_client=None, calendar_service=None):
        self.admin_tools = get_admin_tools(admin_services)
        self.sheets_client = sheets_client
        self.calendar_service = calendar_service

    def create_tools_config(self, is_admin: bool = False) -> List[Dict]:
        # Minimal compatibility: include admin tools + common functions
        tools = []
        # Basic data retrieval
        tools.append({
            "type": "function",
            "function": {
                "name": "get_database_info",
                "description": "Get table rows or query by field (clients, masters, bookings, services)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string"},
                        "filter_field": {"type": "string"},
                        "filter_value": {"type": "string"},
                        "limit": {"type": "integer"}
                    },
                    "required": ["table"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "get_calendar_slots",
                "description": "Get calendar slots for master (uses Google Calendar + bookings)",
                "parameters": {"type": "object", "properties": {"master_id": {"type": "string"}, "start_date": {"type": "string"}}}
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "LLM-based web search (fallback)",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}}
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "create_booking",
                "description": "Create booking (delegates to BookingService)",
                "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}, "master_id": {"type": "string"}, "date": {"type": "string"}, "time": {"type": "string"}, "service": {"type": "string"}, "client_name": {"type": "string"}, "client_phone": {"type": "string"}}}
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "create_client",
                "description": "Create or update client profile",
                "parameters": {"type": "object", "properties": {"telegram_id": {"type": "string"}, "name": {"type": "string"}, "phone": {"type": "string"}}}
            }
        })

        # Admin tools: embed ADMIN_FUNCTIONS if admin
        if is_admin:
            for func in ADMIN_FUNCTIONS:
                tools.append({"type": "function", "function": func})

        return tools

    def handle_function_call(self, function_name: str, arguments: Dict) -> Dict:
        """Dispatch function to underlying services — most operations are handled by admin_tools where applicable"""
        logger.info(f"AdvancedINKA.handle_function_call: {function_name} - args: {arguments}")
        try:
            if function_name == "get_database_info":
                # Try using admin_tools to fetch masters/clients/bookings
                table = arguments.get("table")
                table_lower = table.lower() if table else ""
                if table_lower in ("masters", "мастера"):
                    result = self.admin_tools.execute_function("get_all_masters", {})
                    return {"data": result}
                if table_lower in ("clients", "клиенты"):
                    result = self.admin_tools.execute_function("get_all_clients", {"limit": arguments.get("limit", 100)})
                    return {"data": result}
                if table_lower in ("bookings", "записи"):
                    result = self.admin_tools.execute_function("get_all_bookings", {})
                    return {"data": result}
                if table_lower in ("services", "услуги"):
                    result = self.admin_tools.execute_function("get_all_services", {})
                    return {"data": result}
                # else fallback: read raw from sheets_client
                if self.sheets_client:
                    rows = self.sheets_client.get_all_rows(table)
                    headers = rows[0] if rows and len(rows) else []
                    data = []
                    for r in (rows[1:] if rows else []):
                        d = {headers[i]: r[i] if i < len(r) else "" for i in range(len(headers))}
                        data.append(d)
                    return {"data": data}
                return {"error": "No data source available"}

            if function_name == "get_calendar_slots":
                master_id = arguments.get("master_id")
                start_date = arguments.get("start_date") or datetime.now().strftime("%Y-%m-%d")
                # booking service via admin_tools
                res = self.admin_tools.execute_function("get_master_availability", {"master_id": master_id, "date": start_date})
                return res

            if function_name == "search_web":
                # Use LLM fallback if needed
                query = arguments.get("query")
                # Simple LLM-based reply using chat completions if present
                try:
                    from src.services.inka_ai import INKAConsultant
                    consultant = INKAConsultant(api_key=None)
                    ans = consultant._rule_based_response(query)
                    return {"query": query, "answer": ans, "source": "LLM-Fallback"}
                except Exception:
                    return {"query": query, "answer": "", "source": "none"}

            if function_name == "create_client":
                # args: telegram_id, name, phone
                svc = self.admin_tools.services.get("clients_service") if hasattr(self.admin_tools, 'services') else None
                if svc:
                    telegram_id = arguments.get("telegram_id")
                    name = arguments.get("name")
                    phone = arguments.get("phone", "")
                    created = svc.repo.create_client(telegram_id, name, phone)
                    return {"success": True, "client": created}
                return {"error": "Client service not found"}

            if function_name == "create_booking":
                svc = self.admin_tools.services.get("booking_service") if hasattr(self.admin_tools, 'services') else None
                if svc:
                    # arguments mapping
                    user_id = arguments.get("user_id") or arguments.get("client_id")
                    client_name = arguments.get("client_name") or "Client"
                    client_phone = arguments.get("client_phone") or ""
                    date = arguments.get("date")
                    time = arguments.get("time")
                    master_id = arguments.get("master_id")
                    service_name = arguments.get("service") or arguments.get("service_id")
                    # Use INKAProcessor style Stage-3 reservation if available to get structured outcome
                    try:
                        from src.ai.inka_processor import INKAProcessor
                        ip = INKAProcessor(None, services={'booking_service': svc})
                        slot = {'date': date, 'time': time, 'end_time': arguments.get('end_time', time), 'master_id': master_id, 'service': service_name}
                        out = ip.stage_3_reserve_slot(slot, int(user_id) if user_id else 0, client_name, client_phone, arguments.get('notes', ''))
                        # Normalize returned structure
                        return out
                    except Exception:
                        # Fallback to direct booking_service call
                        res = svc.create_booking(int(user_id) if user_id else 0, client_name, client_phone, date, master_id, time, arguments.get("end_time", time))
                        return {"success": bool(res.get('booking_id')), "booking_id": res.get('booking_id'), "event_id": res.get('event_id'), "message": "Created via fallback"}
                return {"error": "Booking service not found"}

            # Admin functions: delegate to admin_tools (get_all_masters, add_master, edit_master, etc.)
            if hasattr(self.admin_tools, 'execute_function'):
                if function_name in [f['name'] for f in ADMIN_FUNCTIONS]:
                    res = self.admin_tools.execute_function(function_name, arguments or {})
                    return res

            return {"error": f"Unknown function: {function_name}"}

        except Exception as e:
            logger.error(f"AdvancedINKA.handle_function_call error: {e}")
            return {"error": str(e)}


# Factory

def get_advanced_inka(admin_services: Dict[str, Any] = None, sheets_client=None, calendar_service=None):
    return AdvancedINKA(admin_services=admin_services, sheets_client=sheets_client, calendar_service=calendar_service)
