"""
Admin Database Manager & INKA Learning System
Управление БД и обучение ИНКИ через Telegram админ-меню
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AdminAction(Enum):
    """Действия админа"""
    VIEW_STATS = "view_stats"
    MANAGE_MASTERS = "manage_masters"
    MANAGE_SERVICES = "manage_services"
    MANAGE_CLIENTS = "manage_clients"
    MANAGE_SCHEDULE = "manage_schedule"
    TRAIN_INKA = "train_inka"
    VIEW_LOGS = "view_logs"
    EXPORT_DATA = "export_data"


class DatabaseManager:
    """
    Управление БД из Telegram админ-меню
    - Просмотр/добавление/редактирование данных
    - CRUD операции напрямую из чата
    """
    
    def __init__(self, sheets_client):
        """
        Args:
            sheets_client: GoogleSheetsClient
        """
        self.sheets = sheets_client
        self.validation_rules = self._init_validation_rules()
        
        # Кэш для ID
        self._masters_cache = None
        self._masters_list_cache = None
        self._services_cache = None
        self._cache_time = 0
        self._cache_ttl = 60  # секунд
        # Additional short-term cache for heavy sheet reads
        self._bookings_cache = None
        self._bookings_cache_time = 0
        # Audit sheet name
        self.audit_sheet = "Admin_Audit_Log"
        # Ensure audit sheet exists with headers
        try:
            values = self.sheets.get_sheet_values(self.audit_sheet)
            if not values or len(values) == 0:
                headers = ["timestamp", "admin_id", "action", "sheet", "details"]
                # If append fails because sheet doesn't exist, try to create the sheet first
                created = self.sheets.create_sheet(self.audit_sheet)
                if created:
                    self.sheets.append_rows(self.audit_sheet, [headers])
        except Exception:
            # Not critical if the sheet can't be initialized; will attempt on first log
            pass
    
    # ============ HELPER ФУНКЦИИ ДЛЯ ID ============
    
    def get_master_ids(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Получить словарь ID мастеров {id: name}
        Используй для валидации и динамических списков
        """
        import time
        now = time.time()
        
        if not force_refresh and self._masters_cache and (now - self._cache_time) < self._cache_ttl:
            return self._masters_cache
        
        try:
            masters = self.get_all_masters()
            self._masters_cache = {m["id"]: m["name"] for m in masters if m.get("id")}
            self._cache_time = now
            return self._masters_cache
        except Exception as e:
            logger.error(f"Error getting master IDs: {e}")
            return {}
    
    def get_service_ids(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Получить словарь ID услуг {id: name}
        """
        import time
        now = time.time()
        
        if not force_refresh and self._services_cache and (now - self._cache_time) < self._cache_ttl:
            return self._services_cache
        
        try:
            services = self.get_all_services()
            self._services_cache = {s["id"]: s["name"] for s in services if s.get("id")}
            self._cache_time = now
            return self._services_cache
        except Exception as e:
            logger.error(f"Error getting service IDs: {e}")
            return {}
    
    def validate_master_id(self, master_id: str) -> Tuple[bool, str]:
        """Проверить существует ли мастер с таким ID"""
        masters = self.get_master_ids()
        if master_id in masters:
            return True, masters[master_id]
        return False, f"Мастер с ID '{master_id}' не найден"
    
    def validate_service_id(self, service_id: str) -> Tuple[bool, str]:
        """Проверить существует ли услуга с таким ID"""
        services = self.get_service_ids()
        if service_id in services:
            return True, services[service_id]
        return False, f"Услуга с ID '{service_id}' не найдена"
    
    def find_master_by_name(self, name: str) -> Optional[str]:
        """Найти ID мастера по имени (частичное совпадение)"""
        masters = self.get_master_ids()
        name_lower = name.lower()
        for mid, mname in masters.items():
            if name_lower in mname.lower():
                return mid
        return None
    
    def find_service_by_name(self, name: str) -> Optional[str]:
        """Найти ID услуги по названию (частичное совпадение)"""
        services = self.get_service_ids()
        name_lower = name.lower()
        for sid, sname in services.items():
            if name_lower in sname.lower():
                return sid
        return None
    
    # ============ ВАЛИДАЦИЯ ============
    
    def _init_validation_rules(self) -> Dict[str, callable]:
        """Инициализировать правила валидации"""
        return {
            "phone": self._validate_phone,
            "email": self._validate_email,
            "price": self._validate_price,
            "rating": self._validate_rating,
            "time": self._validate_time,
        }
    
    @staticmethod
    def _validate_phone(phone: str) -> Tuple[bool, str]:
        """Валидировать номер телефона"""
        if not phone or len(phone) < 9:
            return False, "Телефон должен содержать минимум 9 цифр"
        return True, ""
    
    @staticmethod
    def _validate_email(email: str) -> Tuple[bool, str]:
        """Валидировать email"""
        if "@" not in email:
            return False, "Неверный формат email"
        return True, ""
    
    @staticmethod
    def _validate_price(price: str) -> Tuple[bool, str]:
        """Валидировать цену"""
        try:
            p = int(price)
            if p < 0:
                return False, "Цена не может быть отрицательной"
            return True, ""
        except ValueError:
            return False, "Цена должна быть числом"
    
    @staticmethod
    def _validate_rating(rating: str) -> Tuple[bool, str]:
        """Валидировать рейтинг"""
        try:
            r = float(rating)
            if not 0 <= r <= 5:
                return False, "Рейтинг должен быть от 0 до 5"
            return True, ""
        except ValueError:
            return False, "Рейтинг должен быть числом"
    
    @staticmethod
    def _validate_time(time_str: str) -> Tuple[bool, str]:
        """Валидировать время (HH:MM)"""
        try:
            datetime.strptime(time_str, "%H:%M")
            return True, ""
        except ValueError:
            return False, "Используй формат HH:MM (например: 14:30)"
    
    # ============ МАСТЕРА ============
    
    def get_all_masters(self) -> List[Dict[str, Any]]:
        """Получить ВСЕ мастеров (для API)"""
        # use cached list if available (avoid frequent Sheets reads)
        import time
        if self._masters_list_cache:
            return self._masters_list_cache
        result = self.get_masters_list()
        if "error" in result:
            return []
        masters = result.get("masters", [])
        # cache briefly to avoid rate limits
        try:
            self._masters_list_cache = masters
            # schedule a simple TTL clear (non-blocking)
            def _clear_cache():
                import time
                time.sleep(1)
                self._masters_list_cache = None
            import threading
            t = threading.Thread(target=_clear_cache, daemon=True)
            t.start()
        except Exception:
            pass
        return masters
    
    def get_all_services(self) -> List[Dict[str, Any]]:
        """Получить ВСЕ услуги (для API)"""
        result = self.get_services_list()
        if "error" in result:
            return []
        return result.get("services", [])
    
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Получить ВСЕХ клиентов (для API)"""
        result = self.get_clients_list()
        if "error" in result:
            return []
        return result.get("clients", [])
    
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Получить ВСЕ записи (для API)"""
        import time
        now = time.time()
        # micro cache for bookings to avoid frequent Sheets reads
        if getattr(self, '_bookings_cache', None) and (now - getattr(self, '_bookings_cache_time', 0)) < 1:
            return self._bookings_cache
        try:
            data = self.sheets.get_sheet_values("Bookings", "A:K")
            if not data:
                return []
            
            bookings = []
            for row in data[1:]:  # Пропустить заголовок
                bookings.append({
                    "id": row[0] if len(row) > 0 else "",
                    "client_id": row[1] if len(row) > 1 else "",
                    "master_id": row[2] if len(row) > 2 else "",
                    "service_id": row[3] if len(row) > 3 else "",
                    "date": row[4] if len(row) > 4 else "",
                    "time": row[5] if len(row) > 5 else "",
                    "duration_min": row[6] if len(row) > 6 else "",
                    "price": row[7] if len(row) > 7 else "",
                    "status": row[8] if len(row) > 8 else "",
                    "notes": row[9] if len(row) > 9 else "",
                })
            
            self._bookings_cache = bookings
            self._bookings_cache_time = now
            return bookings
        except Exception as e:
            logger.error(f"Error getting bookings: {e}")
            return []
    
    def get_masters_list(self, search: str = "") -> Dict[str, Any]:
        """Получить список мастеров"""
        try:
            data = self.sheets.get_sheet_values("Masters", "A:K")
            if not data:
                return {"error": "Нет мастеров в БД"}
            
            masters = []
            for row in data[1:]:  # Пропустить заголовок
                if search.lower() in str(row).lower():
                    masters.append({
                        "id": row[0] if len(row) > 0 else "",
                        "name": row[1] if len(row) > 1 else "",
                        "phone": row[2] if len(row) > 2 else "",
                        "telegram_id": row[3] if len(row) > 3 else "",
                        "specialization": row[4] if len(row) > 4 else "",
                        "rating": row[5] if len(row) > 5 else "0",
                        "experience": row[6] if len(row) > 6 else "",
                        "instagram": row[7] if len(row) > 7 else "",
                        "status": row[8] if len(row) > 8 else "active",
                        "bio": row[9] if len(row) > 9 else "",
                        "calendar_id": row[10] if len(row) > 10 else ""
                    })
            
            return {
                "total": len(masters),
                "masters": masters[:10]  # Макс 10 на экран
            }
        except Exception as e:
            logger.error(f"Error getting masters: {e}")
            return {"error": str(e)}
    
    def add_master(self, master_data: Dict[str, str]) -> Tuple[bool, str]:
        """Добавить нового мастера"""
        try:
            # Валидация
            required_fields = ["name", "specialization", "phone"]
            for field in required_fields:
                if not master_data.get(field):
                    return False, f"Обязательное поле: {field}"
            
            is_valid, msg = self._validate_phone(master_data.get("phone", ""))
            if not is_valid:
                return False, msg
            
            # Подготовка данных - ПРАВИЛЬНЫЙ ПОРЯДОК СТОЛБЦОВ:
            # A: id, B: name, C: phone, D: telegram_id, E: specialization, 
            # F: rating, G: experience, H: instagram, I: status, J: bio, K: calendar_id
            new_master = [
                str(uuid.uuid4()),              # A: id
                master_data.get("name", ""),   # B: name
                master_data.get("phone", ""),  # C: phone
                master_data.get("telegram_id", ""),  # D: telegram_id
                master_data.get("specialization", ""),  # E: specialization
                master_data.get("rating", "0"),  # F: rating
                master_data.get("experience", "0"),  # G: experience
                master_data.get("instagram", ""),  # H: instagram
                "active",  # I: status
                master_data.get("bio", ""),  # J: bio
                master_data.get("calendar_id", ""),  # K: calendar_id
            ]
            
            # Добавить в БД
            self.sheets.append_rows("Masters", [new_master])
            return True, f"✅ Мастер {master_data['name']} добавлен!"
        
        except Exception as e:
            logger.error(f"Error adding master: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def edit_master(self, master_id: str, updates: Dict[str, str]) -> Tuple[bool, str]:
        """Отредактировать мастера"""
        try:
            # Получить текущие данные
            data = self.sheets.get_sheet_values("Masters", "A:K")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == master_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Мастер не найден"
            
            # Обновить поля
            row = list(data[row_idx])
            # Ensure row has enough columns
            while len(row) < 11:
                row.append("")
            
            # Проверяем, нужно ли изменить ID
            new_id = updates.pop("new_id", None)
            if new_id and new_id != master_id:
                # Проверяем формат нового ID
                if not new_id.startswith("m_"):
                    return False, "❌ ID должен начинаться с 'm_'"
                # Проверяем что новый ID не занят
                for check_row in data:
                    if len(check_row) > 0 and check_row[0] == new_id:
                        return False, f"❌ ID '{new_id}' уже используется"
                # Обновляем ID
                row[0] = new_id
                logger.info(f"Changing master ID from {master_id} to {new_id}")
            
            field_map = {
                "name": 1, "phone": 2, "telegram_id": 3, "specialization": 4,
                "rating": 5, "experience": 6, "instagram": 7, "status": 8,
                "bio": 9, "calendar_id": 10
            }
            
            for field, value in updates.items():
                if field in field_map:
                    idx = field_map[field]
                    row[idx] = value
            
            # Сохранить
            self.sheets.update_range("Masters", f"A{row_idx+1}:K{row_idx+1}", [row])
            return True, f"✅ Мастер обновлен!"
        
        except Exception as e:
            logger.error(f"Error editing master: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def delete_master(self, master_id: str) -> Tuple[bool, str]:
        """Удалить мастера (пометить как неактивного)"""
        try:
            data = self.sheets.get_sheet_values("Masters", "A:K")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == master_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Мастер не найден"
            
            # Помечаем как неактивного вместо удаления
            row = list(data[row_idx])
            while len(row) < 9:
                row.append("")
            row[8] = "inactive"
            
            self.sheets.update_range("Masters", f"A{row_idx+1}:K{row_idx+1}", [row])
            return True, f"✅ Мастер удален!"
        
        except Exception as e:
            logger.error(f"Error deleting master: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    # ============ УСЛУГИ ============
    
    def get_services_list(self, search: str = "") -> Dict[str, Any]:
        """Получить список услуг"""
        try:
            data = self.sheets.get_sheet_values("Services", "A:H")
            if not data:
                return {"error": "Нет услуг в БД"}
            
            services = []
            for row in data[1:]:
                if search.lower() in str(row).lower():
                    services.append({
                        "id": row[0] if len(row) > 0 else "",
                        "name": row[1] if len(row) > 1 else "",
                        "description": row[2] if len(row) > 2 else "",
                        "duration_min": row[3] if len(row) > 3 else "0",
                        "price_from": row[4] if len(row) > 4 else "0",
                        "price_to": row[5] if len(row) > 5 else "0",
                        "category": row[6] if len(row) > 6 else "",
                        "active": row[7] if len(row) > 7 else "TRUE"
                    })
            
            return {
                "total": len(services),
                "services": services[:10]
            }
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return {"error": str(e)}
    
    def add_service(self, service_data: Dict[str, str]) -> Tuple[bool, str]:
        """Добавить новую услугу"""
        try:
            required_fields = ["name", "duration", "price"]
            for field in required_fields:
                if not service_data.get(field):
                    return False, f"Обязательное поле: {field}"
            
            # Валидация
            is_valid, msg = self._validate_price(service_data.get("price", "0"))
            if not is_valid:
                return False, msg
            
            new_service = [
                str(uuid.uuid4()),
                service_data.get("name", ""),
                service_data.get("description", ""),
                service_data.get("duration", "0"),
                service_data.get("price", "0"),
                service_data.get("price_to", service_data.get("price", "0")),
                service_data.get("category", "other"),
                "TRUE",  # active
            ]
            
            self.sheets.append_rows("Services", [new_service])
            return True, f"✅ Услуга {service_data['name']} добавлена!"
        
        except Exception as e:
            logger.error(f"Error adding service: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def edit_service(self, service_id: str, updates: Dict[str, str]) -> Tuple[bool, str]:
        """Редактировать услугу"""
        try:
            data = self.sheets.get_sheet_values("Services", "A:H")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == service_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Услуга не найдена"
            
            row = list(data[row_idx])
            while len(row) < 8:
                row.append("")
            
            field_map = {
                "name": 1, "description": 2, "duration_min": 3, "duration": 3,
                "price_from": 4, "price": 4, "price_to": 5, "category": 6, "active": 7
            }
            
            for field, value in updates.items():
                if field in field_map:
                    idx = field_map[field]
                    row[idx] = value
            
            self.sheets.update_range("Services", f"A{row_idx+1}:H{row_idx+1}", [row])
            return True, f"✅ Услуга обновлена!"
        
        except Exception as e:
            logger.error(f"Error editing service: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def delete_service(self, service_id: str) -> Tuple[bool, str]:
        """Удалить услугу (пометить как неактивную)"""
        try:
            data = self.sheets.get_sheet_values("Services", "A:H")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == service_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Услуга не найдена"
            
            row = list(data[row_idx])
            while len(row) < 8:
                row.append("")
            row[7] = "FALSE"  # active = false
            
            self.sheets.update_range("Services", f"A{row_idx+1}:H{row_idx+1}", [row])
            return True, f"✅ Услуга удалена!"
        
        except Exception as e:
            logger.error(f"Error deleting service: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    # ============ КЛИЕНТЫ ============
    
    def get_clients_list(self, search: str = "") -> Dict[str, Any]:
        """Получить список клиентов"""
        try:
            data = self.sheets.get_sheet_values("Clients", "A:H")
            if not data:
                return {"error": "Нет клиентов в БД"}
            
            clients = []
            for row in data[1:]:
                if search.lower() in str(row).lower():
                    clients.append({
                        "client_id": row[0] if len(row) > 0 else "",
                        "id": row[0] if len(row) > 0 else "",
                        "telegram_id": row[1] if len(row) > 1 else "",
                        "user_id": (int(row[1]) if len(row) > 1 and str(row[1]).strip().isdigit() else row[1] if len(row) > 1 else ""),
                        "name": row[2] if len(row) > 2 else "",
                        "phone": row[3] if len(row) > 3 else "",
                        "email": row[4] if len(row) > 4 else "",
                        "notes": row[5] if len(row) > 5 else "",
                        "created_at": row[6] if len(row) > 6 else "",
                        "last_visit": row[7] if len(row) > 7 else ""
                    })
            
            return {
                "total": len(clients),
                "clients": clients  # Возвращаем всех клиентов
            }
        except Exception as e:
            logger.error(f"Error getting clients: {e}")
            return {"error": str(e)}
    
    def add_client(self, client_data: Dict[str, str], actor: str = 'web') -> Tuple[bool, str]:
        """Добавить нового клиента"""
        try:
            required_fields = ["name", "phone"]
            for field in required_fields:
                if not client_data.get(field):
                    return False, f"Обязательное поле: {field}"
            
            is_valid, msg = self._validate_phone(client_data.get("phone", ""))
            if not is_valid:
                return False, msg
            
            new_client = [
                str(uuid.uuid4()),
                client_data.get("telegram_id", ""),
                client_data.get("name", ""),
                client_data.get("phone", ""),
                client_data.get("email", ""),
                client_data.get("notes", ""),
                datetime.now().isoformat(),
                "",  # last_visit
            ]
            
            self.sheets.append_rows("Clients", [new_client])
            # Audit log
            try:
                self.add_audit_log(actor or 'web', 'add_client', 'Clients', f"Added client {client_data.get('name')}")
            except Exception:
                pass
            return True, f"✅ Клиент {client_data['name']} добавлен!"
        
        except Exception as e:
            logger.error(f"Error adding client: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def edit_client(self, client_id: str, updates: Dict[str, str], actor: str = 'web') -> Tuple[bool, str]:
        """Редактировать клиента"""
        try:
            data = self.sheets.get_sheet_values("Clients", "A:H")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == client_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Клиент не найден"
            
            row = list(data[row_idx])
            while len(row) < 8:
                row.append("")
            
            field_map = {
                "telegram_id": 1, "name": 2, "phone": 3,
                "email": 4, "notes": 5
            }
            
            for field, value in updates.items():
                if field in field_map:
                    idx = field_map[field]
                    row[idx] = value
            
            self.sheets.update_range("Clients", f"A{row_idx+1}:H{row_idx+1}", [row])
            try:
                self.add_audit_log(actor or 'web', 'edit_client', 'Clients', f"Edited client {client_id}")
            except Exception:
                pass
            return True, f"✅ Клиент обновлен!"
        
        except Exception as e:
            logger.error(f"Error editing client: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def delete_client(self, client_id: str) -> Tuple[bool, str]:
        """Удалить клиента"""
        try:
            data = self.sheets.get_sheet_values("Clients", "A:H")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == client_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Клиент не найден"
            
            # Удаляем строку (перезаписываем пустой)
            # Или помечаем как удаленного добавив статус
            row = list(data[row_idx])
            while len(row) < 8:
                row.append("")
            row[5] = "[DELETED] " + row[5]  # Помечаем в notes
            
            self.sheets.update_range("Clients", f"A{row_idx+1}:H{row_idx+1}", [row])
            return True, f"✅ Клиент удален!"
        
        except Exception as e:
            logger.error(f"Error deleting client: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    # ============ РАСПИСАНИЕ ============
    
    def add_booking(self, booking_data: Dict[str, str], actor: str = 'web') -> Tuple[bool, str]:
        """Добавить новую запись"""
        try:
            required_fields = ["client_id", "master_id", "service_id", "date", "time"]
            for field in required_fields:
                if not booking_data.get(field):
                    return False, f"Обязательное поле: {field}"
            
            # Валидация времени
            is_valid, msg = self._validate_time(booking_data.get("time", ""))
            if not is_valid:
                return False, msg
            
            # Получить информацию об услуге для цены и длительности
            services = self.get_all_services()
            service = next((s for s in services if s.get("id") == booking_data.get("service_id")), None)
            
            price = booking_data.get("price", "0")
            duration = booking_data.get("duration_min", "60")
            if service:
                price = service.get("price_from", price)
                duration = service.get("duration_min", duration)
            
            new_booking = [
                str(uuid.uuid4()),
                booking_data.get("client_id", ""),
                booking_data.get("master_id", ""),
                booking_data.get("service_id", ""),
                booking_data.get("date", ""),
                booking_data.get("time", ""),
                duration,
                price,
                "pending",  # status
                booking_data.get("notes", ""),
                datetime.now().isoformat(),  # created_at
            ]
            
            self.sheets.append_rows("Bookings", [new_booking])
            try:
                self.add_audit_log(actor or 'web', 'add_booking', 'Bookings', f"Added booking {new_booking[0]} for client {new_booking[1]}")
            except Exception:
                pass
            return True, f"✅ Запись создана!"
        
        except Exception as e:
            logger.error(f"Error adding booking: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def edit_booking(self, booking_id: str, updates: Dict[str, str]) -> Tuple[bool, str]:
        """Редактировать запись"""
        try:
            data = self.sheets.get_sheet_values("Bookings", "A:K")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == booking_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Запись не найдена"
            
            row = list(data[row_idx])
            while len(row) < 11:
                row.append("")
            
            field_map = {
                "client_id": 1, "master_id": 2, "service_id": 3,
                "date": 4, "time": 5, "duration_min": 6,
                "price": 7, "status": 8, "notes": 9
            }
            
            for field, value in updates.items():
                if field in field_map:
                    idx = field_map[field]
                    row[idx] = value
            
            self.sheets.update_range("Bookings", f"A{row_idx+1}:K{row_idx+1}", [row])
            return True, f"✅ Запись обновлена!"
        
        except Exception as e:
            logger.error(f"Error editing booking: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def cancel_booking(self, booking_id: str, reason: str = "", actor: str = 'web') -> Tuple[bool, str]:
        """Отменить запись"""
        try:
            data = self.sheets.get_sheet_values("Bookings", "A:K")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == booking_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Запись не найдена"
            
            row = list(data[row_idx])
            while len(row) < 11:
                row.append("")
            
            row[8] = "cancelled"  # status
            if reason:
                row[9] = f"[ОТМЕНА: {reason}] " + (row[9] if row[9] else "")
            
            self.sheets.update_range("Bookings", f"A{row_idx+1}:K{row_idx+1}", [row])
            try:
                self.add_audit_log(actor or 'web', 'cancel_booking', 'Bookings', f"Cancelled booking {booking_id} reason={reason}")
            except Exception:
                pass
            return True, f"✅ Запись отменена!"
        
        except Exception as e:
            logger.error(f"Error canceling booking: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def confirm_booking(self, booking_id: str, actor: str = 'web') -> Tuple[bool, str]:
        """Подтвердить запись"""
        try:
            data = self.sheets.get_sheet_values("Bookings", "A:K")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == booking_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Запись не найдена"
            
            row = list(data[row_idx])
            while len(row) < 11:
                row.append("")
            
            row[8] = "confirmed"  # status
            
            self.sheets.update_range("Bookings", f"A{row_idx+1}:K{row_idx+1}", [row])
            try:
                self.add_audit_log(actor or 'web', 'confirm_booking', 'Bookings', f"Confirmed booking {booking_id}")
            except Exception:
                pass
            return True, f"✅ Запись подтверждена!"
        
        except Exception as e:
            logger.error(f"Error confirming booking: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def complete_booking(self, booking_id: str, actor: str = 'web') -> Tuple[bool, str]:
        """Отметить запись как выполненную"""
        try:
            data = self.sheets.get_sheet_values("Bookings", "A:K")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == booking_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Запись не найдена"
            
            row = list(data[row_idx])
            while len(row) < 11:
                row.append("")
            
            row[8] = "completed"  # status
            
            self.sheets.update_range("Bookings", f"A{row_idx+1}:K{row_idx+1}", [row])
            try:
                self.add_audit_log(actor or 'web', 'complete_booking', 'Bookings', f"Completed booking {booking_id}")
            except Exception:
                pass
            
            # Обновить last_visit для клиента
            client_id = row[1]
            if client_id:
                try:
                    self.edit_client(client_id, {"last_visit": datetime.now().isoformat()})
                except:
                    pass
            
            return True, f"✅ Запись выполнена!"
        
        except Exception as e:
            logger.error(f"Error completing booking: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    # ============ РАСПИСАНИЕ МАСТЕРА ============
    
    def get_schedule(self, master_id: str = "") -> Dict[str, Any]:
        """Получить расписание мастера"""
        try:
            data = self.sheets.get_sheet_values("Расписание", "A:I")
            if not data:
                return {"error": "Нет расписания в БД"}
            
            schedule = []
            for row in data[1:]:
                if not master_id or (len(row) > 1 and row[1] == master_id):
                    schedule.append({
                        "id": row[0] if len(row) > 0 else "",
                        "master_id": row[1] if len(row) > 1 else "",
                        "day_of_week": row[2] if len(row) > 2 else "",
                        "start_time": row[3] if len(row) > 3 else "",
                        "end_time": row[4] if len(row) > 4 else "",
                        "is_working": row[5] if len(row) > 5 else "true"
                    })
            
            return {
                "total": len(schedule),
                "schedule": schedule
            }
        except Exception as e:
            logger.error(f"Error getting schedule: {e}")
            return {"error": str(e)}
    
    def add_schedule_entry(self, schedule_data: Dict[str, str]) -> Tuple[bool, str]:
        """Добавить запись расписания"""
        try:
            required_fields = ["master_id", "day_of_week", "start_time", "end_time"]
            for field in required_fields:
                if not schedule_data.get(field):
                    return False, f"Обязательное поле: {field}"
            
            # Валидация времени
            for time_field in ["start_time", "end_time"]:
                is_valid, msg = self._validate_time(schedule_data.get(time_field, ""))
                if not is_valid:
                    return False, msg
            
            new_entry = [
                str(uuid.uuid4()),
                schedule_data.get("master_id", ""),
                schedule_data.get("day_of_week", ""),
                schedule_data.get("start_time", ""),
                schedule_data.get("end_time", ""),
                schedule_data.get("is_working", "true"),
                schedule_data.get("break_start", ""),
                schedule_data.get("break_end", ""),
                schedule_data.get("notes", ""),
            ]
            
            self.sheets.append_rows("Расписание", [new_entry])
            return True, f"✅ Запись расписания добавлена!"
        
        except Exception as e:
            logger.error(f"Error adding schedule entry: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def update_schedule_entry(self, entry_id: str, updates: Dict[str, str]) -> Tuple[bool, str]:
        """Обновить запись расписания"""
        try:
            data = self.sheets.get_sheet_values("Расписание", "A:I")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == entry_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Запись расписания не найдена"
            
            row = list(data[row_idx])
            while len(row) < 9:
                row.append("")
            
            field_map = {
                "master_id": 1, "day_of_week": 2, "start_time": 3, "end_time": 4,
                "is_working": 5, "break_start": 6, "break_end": 7, "notes": 8
            }
            
            for field, value in updates.items():
                if field in field_map:
                    row[field_map[field]] = value
            
            self.sheets.update_range("Расписание", f"A{row_idx+1}:I{row_idx+1}", [row])
            return True, f"✅ Запись расписания обновлена!"
        
        except Exception as e:
            logger.error(f"Error updating schedule entry: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def delete_schedule_entry(self, entry_id: str) -> Tuple[bool, str]:
        """Удалить запись расписания"""
        try:
            data = self.sheets.get_sheet_values("Расписание", "A:I")
            
            row_idx = None
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == entry_id:
                    row_idx = i
                    break
            
            if row_idx is None:
                return False, "Запись расписания не найдена"
            
            # Помечаем как не рабочий вместо удаления
            row = list(data[row_idx])
            while len(row) < 6:
                row.append("")
            row[5] = "FALSE"
            
            self.sheets.update_range("Расписание", f"A{row_idx+1}:I{row_idx+1}", [row])
            return True, f"✅ Запись расписания удалена!"
        
        except Exception as e:
            logger.error(f"Error deleting schedule entry: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    # ============ СТАТИСТИКА ============
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить общую статистику"""
        try:
            masters_data = self.sheets.get_sheet_values("Мастера", "A:K")
            services_data = self.sheets.get_sheet_values("Услуги", "A:H")
            clients_data = self.sheets.get_sheet_values("Клиенты", "A:H")
            bookings_data = self.sheets.get_sheet_values("Записи", "A:K")
            
            return {
                "total_masters": len(masters_data) - 1 if masters_data else 0,
                "total_services": len(services_data) - 1 if services_data else 0,
                "total_clients": len(clients_data) - 1 if clients_data else 0,
                "total_bookings": len(bookings_data) - 1 if bookings_data else 0,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

    # ============ SHEET MANAGEMENT (EXPORT/IMPORT/BACKUP) ============

    def list_sheets(self) -> List[str]:
        """Return list of sheet names in the spreadsheet"""
        try:
            # GoogleSheetsClient.get_sheets_list if available
            if hasattr(self.sheets, 'get_sheets_list'):
                return self.sheets.get_sheets_list()
            # fallback: return commonly used sheet names
            return ["Masters", "Services", "Clients", "Bookings", "Расписание", "INKA_Training"]
        except Exception as e:
            logger.error(f"Error listing sheets: {e}")
            return []

    def export_sheet(self, sheet_name: str) -> Dict[str, Any]:
        """Export sheet content as JSON-friendly structure (headers + rows)"""
        try:
            values = self.sheets.get_sheet_values(sheet_name)
            if not values:
                return {"headers": [], "rows": []}
            headers = values[0]
            rows = [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in values[1:]]
            return {"headers": headers, "rows": rows}
        except Exception as e:
            logger.error(f"Error exporting sheet {sheet_name}: {e}")
            return {"error": str(e)}

    def import_sheet(self, sheet_name: str, rows: List[Dict[str, Any]], mode: str = "append") -> Tuple[bool, str]:
        """Import rows to a sheet. mode: append|replace
        rows: list of dicts mapping header -> value
        """
        try:
            if not rows:
                return False, "Нет данных для импорта"

            # Get current headers if exist
            current = self.sheets.get_sheet_values(sheet_name)
            if current and len(current) > 0:
                headers = current[0]
            else:
                headers = list(rows[0].keys())

            # Convert dict rows to list rows following headers
            list_rows = []
            for r in rows:
                list_rows.append([r.get(h, "") for h in headers])

            if mode == 'append':
                self.sheets.append_rows(sheet_name, list_rows)
                return True, f"✅ Импортировано {len(list_rows)} строк (append)"
            else:
                # Replace: overwrite sheet data by writing headers + rows starting A1
                data = [headers] + list_rows
                # Attempt to write by replacing a big range
                # Assuming update_range works for large ranges
                end_col = 'Z'
                end_row = len(data)
                range_spec = f"A1:{end_col}{end_row}"
                self.sheets.update_range(sheet_name, range_spec, data)
                return True, f"✅ Импортировано {len(list_rows)} строк (replace)"
        except Exception as e:
            logger.error(f"Error importing sheet {sheet_name}: {e}")
            return False, str(e)

    def backup_db(self) -> Dict[str, Any]:
        """Return backup data for all sheets as JSON (dict sheet_name -> headers + rows)"""
        try:
            sheets = self.list_sheets()
            backup = {}
            for s in sheets:
                export = self.export_sheet(s)
                if 'error' in export:
                    backup[s] = {"error": export['error']}
                else:
                    backup[s] = export
            return backup
        except Exception as e:
            logger.error(f"Error creating DB backup: {e}")
            return {"error": str(e)}

    def restore_db(self, backup_data: Dict[str, Any], mode: str = 'replace') -> Tuple[bool, str]:
        """Restore DB from backup_data structure. mode: replace|merge
           backup_data should be {sheet_name: {headers:[], rows:[{...}]}}
        """
        try:
            for sname, sheet in backup_data.items():
                if 'headers' not in sheet or 'rows' not in sheet:
                    continue
                rows = sheet['rows']
                headers = sheet['headers']
                # Convert rows of dicts back to list rows
                list_rows = [[r.get(h, '') for h in headers] for r in rows]
                data = [headers] + list_rows
                end_col = 'Z'
                end_row = len(data)
                range_spec = f"A1:{end_col}{end_row}"
                if mode == 'replace':
                    self.sheets.update_range(sname, range_spec, data)
                else:
                    # Append merging
                    self.sheets.append_rows(sname, list_rows)
            return True, "✅ DB restored"
        except Exception as e:
            logger.error(f"Error restoring DB: {e}")
            return False, str(e)

    def add_audit_log(self, admin_id: int, action: str, sheet: str, details: str = "") -> bool:
        """Append an audit log row to Admin_Audit_Log sheet"""
        try:
            from datetime import datetime
            row = [datetime.now().isoformat(), str(admin_id), action, sheet, details]
            self.sheets.append_rows(self.audit_sheet, [row])
            return True
            try:
                # Ensure audit sheet exists
                if not self.sheets.get_sheet_values(self.audit_sheet):
                    headers = ["timestamp", "admin_id", "action", "sheet", "details"]
                    self.sheets.append_rows(self.audit_sheet, [headers])
                row = [datetime.now().isoformat(), str(admin_id), action, sheet, details]
                self.sheets.append_rows(self.audit_sheet, [row])
                return True
            except Exception:
                return False
        except Exception as e:
            logger.error(f"Error adding audit log: {e}")
            return False

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return audit logs as list of dicts"""
        try:
            data = self.sheets.get_sheet_values(self.audit_sheet)
            if not data or len(data) <= 1:
                return []
            headers = data[0]
            rows = data[1:limit+1]
            return [dict(zip(headers, r + [""] * (len(headers) - len(r)))) for r in rows]
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []


class InkaLearningSystem:
    """
    Система обучения ИНКИ через чат
    - Добавлять примеры разговоров
    - Обучать новым сценариям
    - Сохранять обучающие данные
    """
    
    def __init__(self, sheets_client):
        """
        Args:
            sheets_client: GoogleSheetsClient
        """
        self.sheets = sheets_client
        self.learning_sheet = "INKA_Training"  # Специальный лист для обучения
        self._ensure_training_sheet_exists()
    
    def _ensure_training_sheet_exists(self):
        """Убедиться что лист обучения существует"""
        try:
            # Попытка получить данные - если ошибка, создать лист
            self.sheets.get_sheet_values(self.learning_sheet, "A1")
        except Exception as e:
            try:
                # Создать новый лист с заголовками
                headers = [
                    "id", "timestamp", "category", "user_input", "inka_response",
                    "admin_correction", "improvement", "tags", "status"
                ]
                self.sheets.append_rows(self.learning_sheet, [headers])
            except Exception as init_error:
                logger.warning(f"Could not ensure INKA_Training sheet exists: {init_error}")
                # Это не критично - будет создано при первом использовании
    
    def add_training_example(self, category: str, user_input: str,
                            inka_response: str, correction: str = "",
                            tags: str = "") -> Tuple[bool, str]:
        """
        Добавить пример для обучения ИНКИ
        
        Args:
            category: Категория (greeting, booking, question и т.д.)
            user_input: Входящее сообщение от пользователя
            inka_response: Текущий ответ ИНКИ
            correction: Правильный ответ (если нужна коррекция)
            tags: Теги (comma-separated)
        """
        try:
            training_entry = [
                str(uuid.uuid4()),
                datetime.now().isoformat(),
                category,
                user_input,
                inka_response,
                correction,
                "yes" if correction else "no",
                tags,
                "active"
            ]
            
            self.sheets.append_rows(self.learning_sheet, [training_entry])
            return True, "✅ Пример обучения сохранен!"
        except Exception as e:
            logger.error(f"Error adding training example: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def get_training_examples(self, category: str = "", tag: str = "") -> Dict[str, Any]:
        """Получить примеры для обучения"""
        try:
            data = self.sheets.get_sheet_values(self.learning_sheet, "A:I")
            if not data:
                return {"error": "Нет примеров обучения"}
            
            examples = []
            for row in data[1:]:
                if (not category or (len(row) > 2 and row[2] == category)) and \
                   (not tag or (len(row) > 7 and tag in str(row[7]))):
                    examples.append({
                        "id": row[0] if len(row) > 0 else "",
                        "timestamp": row[1] if len(row) > 1 else "",
                        "category": row[2] if len(row) > 2 else "",
                        "user_input": row[3] if len(row) > 3 else "",
                        "inka_response": row[4] if len(row) > 4 else "",
                        "correction": row[5] if len(row) > 5 else "",
                        "improvement": row[6] if len(row) > 6 else "",
                        "tags": row[7] if len(row) > 7 else ""
                    })
            
            return {
                "total": len(examples),
                "examples": examples[:20]
            }
        except Exception as e:
            logger.error(f"Error getting training examples: {e}")
            return {"error": str(e)}
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Получить предложения по улучшению"""
        try:
            data = self.sheets.get_sheet_values(self.learning_sheet, "A:I")
            if not data:
                return []
            
            suggestions = []
            for row in data[1:]:
                # Строки где есть коррекция (improvement = "yes")
                if len(row) > 6 and row[6] == "yes":
                    suggestions.append({
                        "user_input": row[3] if len(row) > 3 else "",
                        "wrong_response": row[4] if len(row) > 4 else "",
                        "correct_response": row[5] if len(row) > 5 else "",
                        "category": row[2] if len(row) > 2 else "",
                    })
            
            return suggestions[:10]
        except Exception as e:
            logger.error(f"Error getting improvement suggestions: {e}")
            return []
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Получить статистику обучения"""
        try:
            data = self.sheets.get_sheet_values(self.learning_sheet, "A:I")
            if not data:
                return {"error": "Нет данных обучения"}
            
            total = len(data) - 1
            improvements = sum(1 for row in data[1:] if len(row) > 6 and row[6] == "yes")
            
            categories = {}
            for row in data[1:]:
                if len(row) > 2:
                    cat = row[2]
                    categories[cat] = categories.get(cat, 0) + 1
            
            return {
                "total_examples": total,
                "total_improvements": improvements,
                "improvement_rate": f"{(improvements/total*100):.1f}%" if total > 0 else "0%",
                "categories": categories,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting training stats: {e}")
            return {"error": str(e)}


def create_admin_manager(sheets_client) -> Tuple[DatabaseManager, InkaLearningSystem]:
    """Фабрика для создания админ-менеджера и системы обучения"""
    return DatabaseManager(sheets_client), InkaLearningSystem(sheets_client)
