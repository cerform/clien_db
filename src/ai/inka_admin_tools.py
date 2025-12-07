"""
INKA Admin Tools - Инструменты администрирования для ИНКИ
Позволяет ИНКЕ управлять всеми аспектами салона через естественный язык
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ================== ОПРЕДЕЛЕНИЯ ФУНКЦИЙ ДЛЯ OPENAI ==================

ADMIN_FUNCTIONS = [
    # ========== МАСТЕРА ==========
    {
        "name": "get_all_masters",
        "description": "Получить список всех мастеров салона с их данными",
        "parameters": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["all", "active", "inactive"],
                    "description": "Фильтр по статусу мастера"
                }
            },
            "required": []
        }
    },
    {
        "name": "add_master",
        "description": "Добавить нового мастера в салон",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Имя мастера"},
                "phone": {"type": "string", "description": "Телефон мастера"},
                "specialization": {"type": "string", "description": "Специализация (татуировки, пирсинг и т.д.)"},
                "telegram_id": {"type": "string", "description": "Telegram ID мастера"},
                "experience": {"type": "string", "description": "Опыт работы в годах"},
                "instagram": {"type": "string", "description": "Instagram аккаунт"},
                "bio": {"type": "string", "description": "Краткое описание мастера"},
                "calendar_id": {"type": "string", "description": "ID Google Calendar мастера"}
            },
            "required": ["name", "specialization"]
        }
    },
    {
        "name": "edit_master",
        "description": "Редактировать данные мастера",
        "parameters": {
            "type": "object",
            "properties": {
                "master_id": {"type": "string", "description": "ID мастера"},
                "name": {"type": "string", "description": "Новое имя"},
                "phone": {"type": "string", "description": "Новый телефон"},
                "specialization": {"type": "string", "description": "Новая специализация"},
                "status": {"type": "string", "enum": ["active", "inactive"], "description": "Статус"},
                "experience": {"type": "string", "description": "Опыт работы"},
                "instagram": {"type": "string", "description": "Instagram"},
                "bio": {"type": "string", "description": "Описание"},
                "calendar_id": {"type": "string", "description": "ID Google Calendar"}
            },
            "required": ["master_id"]
        }
    },
    {
        "name": "delete_master",
        "description": "Удалить мастера (пометить как неактивного)",
        "parameters": {
            "type": "object",
            "properties": {
                "master_id": {"type": "string", "description": "ID мастера для удаления"}
            },
            "required": ["master_id"]
        }
    },
    
    # ========== УСЛУГИ ==========
    {
        "name": "get_all_services",
        "description": "Получить список всех услуг салона",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Фильтр по категории"}
            },
            "required": []
        }
    },
    {
        "name": "add_service",
        "description": "Добавить новую услугу в прайс-лист",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Название услуги"},
                "description": {"type": "string", "description": "Описание услуги"},
                "price": {"type": "number", "description": "Цена в рублях"},
                "duration": {"type": "integer", "description": "Длительность в минутах"},
                "category": {"type": "string", "description": "Категория услуги"}
            },
            "required": ["name", "price", "duration"]
        }
    },
    {
        "name": "edit_service",
        "description": "Редактировать услугу",
        "parameters": {
            "type": "object",
            "properties": {
                "service_id": {"type": "string", "description": "ID услуги"},
                "name": {"type": "string", "description": "Новое название"},
                "description": {"type": "string", "description": "Новое описание"},
                "price": {"type": "number", "description": "Новая цена"},
                "duration": {"type": "integer", "description": "Новая длительность"},
                "status": {"type": "string", "enum": ["active", "inactive"], "description": "Статус"}
            },
            "required": ["service_id"]
        }
    },
    {
        "name": "delete_service",
        "description": "Удалить услугу",
        "parameters": {
            "type": "object",
            "properties": {
                "service_id": {"type": "string", "description": "ID услуги для удаления"}
            },
            "required": ["service_id"]
        }
    },
    
    # ========== КЛИЕНТЫ ==========
    {
        "name": "get_all_clients",
        "description": "Получить список всех клиентов",
        "parameters": {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Поиск по имени или телефону"},
                "limit": {"type": "integer", "description": "Максимальное количество результатов"}
            },
            "required": []
        }
    },
    {
        "name": "get_client_info",
        "description": "Получить подробную информацию о клиенте",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "ID клиента"},
                "phone": {"type": "string", "description": "Телефон клиента (альтернатива ID)"}
            },
            "required": []
        }
    },
    {
        "name": "add_client",
        "description": "Добавить нового клиента",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Имя клиента"},
                "phone": {"type": "string", "description": "Телефон клиента"},
                "telegram_id": {"type": "string", "description": "Telegram ID"},
                "notes": {"type": "string", "description": "Заметки о клиенте"}
            },
            "required": ["name", "phone"]
        }
    },
    {
        "name": "edit_client",
        "description": "Редактировать данные клиента",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "ID клиента"},
                "name": {"type": "string", "description": "Новое имя"},
                "phone": {"type": "string", "description": "Новый телефон"},
                "notes": {"type": "string", "description": "Новые заметки"}
            },
            "required": ["client_id"]
        }
    },
    
    # ========== ЗАПИСИ ==========
    {
        "name": "get_all_bookings",
        "description": "Получить список всех записей",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["all", "pending", "confirmed", "completed", "cancelled"], "description": "Фильтр по статусу"},
                "master_id": {"type": "string", "description": "Фильтр по мастеру"},
                "date_from": {"type": "string", "description": "Дата начала периода (YYYY-MM-DD)"},
                "date_to": {"type": "string", "description": "Дата конца периода (YYYY-MM-DD)"}
            },
            "required": []
        }
    },
    {
        "name": "create_booking",
        "description": "Создать новую запись клиента",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "ID клиента"},
                "client_name": {"type": "string", "description": "Имя клиента (если нет ID)"},
                "client_phone": {"type": "string", "description": "Телефон клиента (если нет ID)"},
                "master_id": {"type": "string", "description": "ID мастера"},
                "service_id": {"type": "string", "description": "ID услуги"},
                "date": {"type": "string", "description": "Дата записи (YYYY-MM-DD)"},
                "time": {"type": "string", "description": "Время записи (HH:MM)"},
                "notes": {"type": "string", "description": "Примечания к записи"}
            },
            "required": ["master_id", "service_id", "date", "time"]
        }
    },
    {
        "name": "edit_booking",
        "description": "Редактировать запись",
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {"type": "string", "description": "ID записи"},
                "date": {"type": "string", "description": "Новая дата"},
                "time": {"type": "string", "description": "Новое время"},
                "master_id": {"type": "string", "description": "Новый мастер"},
                "service_id": {"type": "string", "description": "Новая услуга"},
                "notes": {"type": "string", "description": "Новые примечания"}
            },
            "required": ["booking_id"]
        }
    },
    {
        "name": "confirm_booking",
        "description": "Подтвердить запись",
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {"type": "string", "description": "ID записи для подтверждения"}
            },
            "required": ["booking_id"]
        }
    },
    {
        "name": "complete_booking",
        "description": "Завершить запись (клиент пришел)",
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {"type": "string", "description": "ID записи"},
                "final_price": {"type": "number", "description": "Итоговая стоимость"}
            },
            "required": ["booking_id"]
        }
    },
    {
        "name": "cancel_booking",
        "description": "Отменить запись",
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {"type": "string", "description": "ID записи"},
                "reason": {"type": "string", "description": "Причина отмены"}
            },
            "required": ["booking_id"]
        }
    },
    
    # ========== РАСПИСАНИЕ И ДОСТУПНОСТЬ ==========
    {
        "name": "get_master_availability",
        "description": "Проверить доступность мастера на определенную дату",
        "parameters": {
            "type": "object",
            "properties": {
                "master_id": {"type": "string", "description": "ID мастера"},
                "date": {"type": "string", "description": "Дата (YYYY-MM-DD)"}
            },
            "required": ["master_id", "date"]
        }
    },
    {
        "name": "get_schedule_overview",
        "description": "Получить обзор расписания на период",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Дата начала"},
                "date_to": {"type": "string", "description": "Дата конца"},
                "master_id": {"type": "string", "description": "Фильтр по мастеру (опционально)"}
            },
            "required": []
        }
    },
    {
        "name": "add_calendar_event",
        "description": "Добавить событие в Google Calendar мастера",
        "parameters": {
            "type": "object",
            "properties": {
                "master_id": {"type": "string", "description": "ID мастера"},
                "title": {"type": "string", "description": "Название события"},
                "start_time": {"type": "string", "description": "Время начала (ISO формат)"},
                "duration": {"type": "integer", "description": "Длительность в минутах"}
            },
            "required": ["master_id", "title", "start_time"]
        }
    },
    
    # ========== АНАЛИТИКА ==========
    {
        "name": "get_statistics",
        "description": "Получить статистику салона",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["today", "week", "month", "year", "all"], "description": "Период статистики"}
            },
            "required": []
        }
    },
    {
        "name": "get_revenue_report",
        "description": "Получить отчет о доходах",
        "parameters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Начало периода"},
                "date_to": {"type": "string", "description": "Конец периода"},
                "group_by": {"type": "string", "enum": ["day", "week", "month", "master", "service"], "description": "Группировка"}
            },
            "required": []
        }
    }
]


class INKAAdminTools:
    """Исполнитель административных функций для ИНКИ"""
    
    def __init__(self, db_manager=None):
        """
        Args:
            db_manager: DatabaseManager для работы с БД
        """
        self.db = db_manager
        self._init_db_manager()
    
    def _init_db_manager(self):
        """Инициализировать db_manager если не передан"""
        if self.db is None:
            try:
                from src.config import get_config
                from src.db.sheets_client import GoogleSheetsClient
                from src.services.admin_db_manager import DatabaseManager
                import os
                
                config = get_config()
                creds_file = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")
                
                sheets_client = GoogleSheetsClient(
                    credentials_file=creds_file,
                    spreadsheet_id=config.google_spreadsheet_id
                )
                self.db = DatabaseManager(sheets_client)
                logger.info("✅ INKAAdminTools: Database manager initialized")
            except Exception as e:
                logger.error(f"❌ INKAAdminTools: Failed to init db_manager: {e}")
                self.db = None
    
    def execute_function(self, function_name: str, arguments: Dict) -> Dict[str, Any]:
        """
        Выполнить функцию по имени
        
        Args:
            function_name: Имя функции
            arguments: Аргументы функции
            
        Returns:
            Результат выполнения
        """
        if self.db is None:
            return {"success": False, "error": "База данных не инициализирована"}
        
        method = getattr(self, f"_func_{function_name}", None)
        if method is None:
            return {"success": False, "error": f"Функция {function_name} не найдена"}
        
        try:
            result = method(arguments)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Error executing {function_name}: {e}")
            return {"success": False, "error": str(e)}
    
    # ================== МАСТЕРА ==================
    
    def _func_get_all_masters(self, args: Dict) -> List[Dict]:
        """Получить список мастеров"""
        masters = self.db.get_all_masters()
        status_filter = args.get("status_filter", "all")
        
        if status_filter != "all":
            masters = [m for m in masters if m.get("status") == status_filter]
        
        return masters
    
    def _func_add_master(self, args: Dict) -> str:
        """Добавить мастера"""
        success, message = self.db.add_master(args)
        return message
    
    def _func_edit_master(self, args: Dict) -> str:
        """Редактировать мастера"""
        master_id = args.pop("master_id")
        success, message = self.db.edit_master(master_id, args)
        return message
    
    def _func_delete_master(self, args: Dict) -> str:
        """Удалить мастера"""
        success, message = self.db.delete_master(args["master_id"])
        return message
    
    # ================== УСЛУГИ ==================
    
    def _func_get_all_services(self, args: Dict) -> List[Dict]:
        """Получить список услуг"""
        services = self.db.get_all_services()
        category = args.get("category")
        
        if category:
            services = [s for s in services if s.get("category") == category]
        
        return services
    
    def _func_add_service(self, args: Dict) -> str:
        """Добавить услугу"""
        success, message = self.db.add_service(args)
        return message
    
    def _func_edit_service(self, args: Dict) -> str:
        """Редактировать услугу"""
        service_id = args.pop("service_id")
        success, message = self.db.edit_service(service_id, args)
        return message
    
    def _func_delete_service(self, args: Dict) -> str:
        """Удалить услугу"""
        success, message = self.db.delete_service(args["service_id"])
        return message
    
    # ================== КЛИЕНТЫ ==================
    
    def _func_get_all_clients(self, args: Dict) -> List[Dict]:
        """Получить список клиентов"""
        clients = self.db.get_all_clients()
        search = args.get("search", "").lower()
        limit = args.get("limit", 100)
        
        if search:
            clients = [c for c in clients if 
                       search in c.get("name", "").lower() or 
                       search in c.get("phone", "").lower()]
        
        return clients[:limit]
    
    def _func_get_client_info(self, args: Dict) -> Dict:
        """Получить информацию о клиенте"""
        clients = self.db.get_all_clients()
        bookings = self.db.get_all_bookings()
        
        client_id = args.get("client_id")
        phone = args.get("phone")
        
        client = None
        if client_id:
            client = next((c for c in clients if c.get("id") == client_id), None)
        elif phone:
            client = next((c for c in clients if c.get("phone") == phone), None)
        
        if not client:
            return {"error": "Клиент не найден"}
        
        # Добавляем историю записей
        client_bookings = [b for b in bookings if b.get("client_id") == client.get("id")]
        client["bookings_count"] = len(client_bookings)
        client["completed_bookings"] = len([b for b in client_bookings if b.get("status") == "completed"])
        client["recent_bookings"] = client_bookings[-5:]
        
        return client
    
    def _func_add_client(self, args: Dict) -> str:
        """Добавить клиента"""
        success, message = self.db.add_client(args)
        return message
    
    def _func_edit_client(self, args: Dict) -> str:
        """Редактировать клиента"""
        client_id = args.pop("client_id")
        success, message = self.db.edit_client(client_id, args)
        return message
    
    # ================== ЗАПИСИ ==================
    
    def _func_get_all_bookings(self, args: Dict) -> List[Dict]:
        """Получить список записей"""
        bookings = self.db.get_all_bookings()
        
        status = args.get("status", "all")
        master_id = args.get("master_id")
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        
        if status != "all":
            bookings = [b for b in bookings if b.get("status") == status]
        
        if master_id:
            bookings = [b for b in bookings if b.get("master_id") == master_id]
        
        if date_from:
            bookings = [b for b in bookings if b.get("date", "") >= date_from]
        
        if date_to:
            bookings = [b for b in bookings if b.get("date", "") <= date_to]
        
        # Обогащаем данные
        masters = {m["id"]: m for m in self.db.get_all_masters()}
        services = {s["id"]: s for s in self.db.get_all_services()}
        clients = {c["id"]: c for c in self.db.get_all_clients()}
        
        for b in bookings:
            master = masters.get(b.get("master_id"), {})
            service = services.get(b.get("service_id"), {})
            client = clients.get(b.get("client_id"), {})
            
            b["master_name"] = master.get("name", "Неизвестный")
            b["service_name"] = service.get("name", "Неизвестная")
            b["client_name"] = client.get("name", "Неизвестный")
            b["client_phone"] = client.get("phone", "")
        
        return bookings
    
    def _func_create_booking(self, args: Dict) -> str:
        """Создать запись"""
        # Если нет client_id, создаем или находим клиента
        if not args.get("client_id"):
            client_name = args.get("client_name")
            client_phone = args.get("client_phone")
            
            if client_name and client_phone:
                # Ищем существующего клиента
                clients = self.db.get_all_clients()
                existing = next((c for c in clients if c.get("phone") == client_phone), None)
                
                if existing:
                    args["client_id"] = existing.get("id")
                else:
                    # Создаем нового
                    success, msg = self.db.add_client({"name": client_name, "phone": client_phone})
                    if success:
                        clients = self.db.get_all_clients()
                        new_client = next((c for c in clients if c.get("phone") == client_phone), None)
                        if new_client:
                            args["client_id"] = new_client.get("id")
        
        success, message = self.db.add_booking(args)
        return message
    
    def _func_edit_booking(self, args: Dict) -> str:
        """Редактировать запись"""
        booking_id = args.pop("booking_id")
        success, message = self.db.edit_booking(booking_id, args)
        return message
    
    def _func_confirm_booking(self, args: Dict) -> str:
        """Подтвердить запись"""
        success, message = self.db.confirm_booking(args["booking_id"])
        return message
    
    def _func_complete_booking(self, args: Dict) -> str:
        """Завершить запись"""
        booking_id = args["booking_id"]
        final_price = args.get("final_price")
        
        success, message = self.db.complete_booking(booking_id)
        
        if success and final_price:
            self.db.edit_booking(booking_id, {"price": final_price})
        
        return message
    
    def _func_cancel_booking(self, args: Dict) -> str:
        """Отменить запись"""
        reason = args.get("reason", "")
        success, message = self.db.cancel_booking(args["booking_id"])
        return message
    
    # ================== РАСПИСАНИЕ ==================
    
    def _func_get_master_availability(self, args: Dict) -> Dict:
        """Проверить доступность мастера"""
        master_id = args["master_id"]
        date = args["date"]
        
        # Все слоты рабочего дня
        all_slots = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
        busy_slots = set()
        
        # Проверяем записи
        bookings = self.db.get_all_bookings()
        for b in bookings:
            if b.get("master_id") == master_id and b.get("date") == date:
                if b.get("status") not in ["cancelled"]:
                    time = b.get("time", "")
                    if time:
                        busy_slots.add(time[:5] if len(time) > 5 else time)
        
        # Проверяем Google Calendar
        masters = self.db.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        
        if master and master.get("calendar_id"):
            try:
                from src.calendars.google_calendar_sync import GoogleCalendarSync
                from src.config import get_config
                import os
                
                config = get_config()
                creds_file = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")
                calendar = GoogleCalendarSync(creds_file, master["calendar_id"])
                events = calendar.get_events(date, date)
                
                for event in events:
                    start = event.get("start", {}).get("dateTime", "")
                    if start:
                        hour = start[11:16]
                        busy_slots.add(hour)
            except Exception as e:
                logger.warning(f"Calendar error: {e}")
        
        available_slots = [s for s in all_slots if s not in busy_slots]
        
        return {
            "master_id": master_id,
            "master_name": master.get("name") if master else "Неизвестный",
            "date": date,
            "available_slots": available_slots,
            "busy_slots": list(busy_slots)
        }
    
    def _func_get_schedule_overview(self, args: Dict) -> Dict:
        """Обзор расписания"""
        date_from = args.get("date_from", datetime.now().strftime("%Y-%m-%d"))
        date_to = args.get("date_to", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        master_id = args.get("master_id")
        
        bookings = self.db.get_all_bookings()
        masters = self.db.get_all_masters()
        
        # Фильтруем по датам
        filtered = [b for b in bookings if date_from <= b.get("date", "") <= date_to]
        
        if master_id:
            filtered = [b for b in filtered if b.get("master_id") == master_id]
        
        # Группируем по дням
        by_day = {}
        for b in filtered:
            day = b.get("date", "unknown")
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(b)
        
        # Статистика
        total = len(filtered)
        by_status = {}
        for b in filtered:
            status = b.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "period": f"{date_from} - {date_to}",
            "total_bookings": total,
            "by_status": by_status,
            "by_day": {day: len(bookings) for day, bookings in by_day.items()},
            "masters_count": len(set(b.get("master_id") for b in filtered))
        }
    
    def _func_add_calendar_event(self, args: Dict) -> str:
        """Добавить событие в календарь"""
        master_id = args["master_id"]
        title = args["title"]
        start_time = args["start_time"]
        duration = args.get("duration", 60)
        
        masters = self.db.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        
        if not master:
            return "Мастер не найден"
        
        calendar_id = master.get("calendar_id")
        if not calendar_id:
            return "У мастера не настроен Google Calendar"
        
        try:
            from src.calendars.google_calendar_sync import GoogleCalendarSync
            from src.config import get_config
            import os
            
            config = get_config()
            creds_file = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")
            calendar = GoogleCalendarSync(creds_file, calendar_id)
            
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            success = calendar.create_event(title, start_dt, duration)
            
            if success:
                return f"✅ Событие '{title}' добавлено в календарь {master.get('name')}"
            else:
                return "Ошибка при создании события"
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    # ================== АНАЛИТИКА ==================
    
    def _func_get_statistics(self, args: Dict) -> Dict:
        """Получить статистику"""
        period = args.get("period", "all")
        
        clients = self.db.get_all_clients()
        masters = self.db.get_all_masters()
        services = self.db.get_all_services()
        bookings = self.db.get_all_bookings()
        
        # Фильтр по периоду
        now = datetime.now()
        if period == "today":
            date_filter = now.strftime("%Y-%m-%d")
            bookings = [b for b in bookings if b.get("date") == date_filter]
        elif period == "week":
            week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            bookings = [b for b in bookings if b.get("date", "") >= week_ago]
        elif period == "month":
            month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            bookings = [b for b in bookings if b.get("date", "") >= month_ago]
        elif period == "year":
            year_ago = (now - timedelta(days=365)).strftime("%Y-%m-%d")
            bookings = [b for b in bookings if b.get("date", "") >= year_ago]
        
        completed = [b for b in bookings if b.get("status") == "completed"]
        revenue = sum(float(b.get("price", 0) or 0) for b in completed)
        
        return {
            "period": period,
            "total_clients": len(clients),
            "total_masters": len([m for m in masters if m.get("status") == "active"]),
            "total_services": len([s for s in services if s.get("status") == "active"]),
            "total_bookings": len(bookings),
            "completed_bookings": len(completed),
            "cancelled_bookings": len([b for b in bookings if b.get("status") == "cancelled"]),
            "pending_bookings": len([b for b in bookings if b.get("status") == "pending"]),
            "total_revenue": revenue,
            "average_check": revenue / len(completed) if completed else 0
        }
    
    def _func_get_revenue_report(self, args: Dict) -> Dict:
        """Отчет о доходах"""
        date_from = args.get("date_from", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        date_to = args.get("date_to", datetime.now().strftime("%Y-%m-%d"))
        group_by = args.get("group_by", "day")
        
        bookings = self.db.get_all_bookings()
        masters = {m["id"]: m for m in self.db.get_all_masters()}
        services = {s["id"]: s for s in self.db.get_all_services()}
        
        # Фильтруем завершенные в периоде
        completed = [b for b in bookings 
                     if b.get("status") == "completed" 
                     and date_from <= b.get("date", "") <= date_to]
        
        total_revenue = sum(float(b.get("price", 0) or 0) for b in completed)
        
        # Группировка
        grouped = {}
        for b in completed:
            if group_by == "day":
                key = b.get("date", "unknown")
            elif group_by == "week":
                try:
                    dt = datetime.strptime(b.get("date", ""), "%Y-%m-%d")
                    key = f"Week {dt.isocalendar()[1]}"
                except:
                    key = "unknown"
            elif group_by == "month":
                key = b.get("date", "")[:7]  # YYYY-MM
            elif group_by == "master":
                master = masters.get(b.get("master_id"), {})
                key = master.get("name", "Неизвестный")
            elif group_by == "service":
                service = services.get(b.get("service_id"), {})
                key = service.get("name", "Неизвестная")
            else:
                key = "all"
            
            if key not in grouped:
                grouped[key] = {"count": 0, "revenue": 0}
            grouped[key]["count"] += 1
            grouped[key]["revenue"] += float(b.get("price", 0) or 0)
        
        return {
            "period": f"{date_from} - {date_to}",
            "total_revenue": total_revenue,
            "total_bookings": len(completed),
            "grouped_by": group_by,
            "breakdown": grouped
        }


def get_admin_tools(db_manager=None) -> INKAAdminTools:
    """Фабрика для создания инструментов администрирования"""
    return INKAAdminTools(db_manager)
