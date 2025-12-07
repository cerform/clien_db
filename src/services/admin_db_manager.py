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
        result = self.get_masters_list()
        if "error" in result:
            return []
        return result.get("masters", [])
    
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
            
            # Подготовка данных
            new_master = [
                str(uuid.uuid4()),  # id
                master_data.get("name", ""),
                master_data.get("specialization", ""),
                master_data.get("experience", "0"),
                master_data.get("rating", "0"),
                master_data.get("phone", ""),
                master_data.get("instagram", ""),
                master_data.get("price", "0"),
                "active",  # status
                master_data.get("bio", ""),
                master_data.get("calendar_id", ""),
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
                        "id": row[0] if len(row) > 0 else "",
                        "telegram_id": row[1] if len(row) > 1 else "",
                        "name": row[2] if len(row) > 2 else "",
                        "phone": row[3] if len(row) > 3 else "",
                        "email": row[4] if len(row) > 4 else "",
                        "notes": row[5] if len(row) > 5 else "",
                        "created_at": row[6] if len(row) > 6 else "",
                        "last_visit": row[7] if len(row) > 7 else ""
                    })
            
            return {
                "total": len(clients),
                "clients": clients[:10]
            }
        except Exception as e:
            logger.error(f"Error getting clients: {e}")
            return {"error": str(e)}
    
    def add_client(self, client_data: Dict[str, str]) -> Tuple[bool, str]:
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
            return True, f"✅ Клиент {client_data['name']} добавлен!"
        
        except Exception as e:
            logger.error(f"Error adding client: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def edit_client(self, client_id: str, updates: Dict[str, str]) -> Tuple[bool, str]:
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
    
    def add_booking(self, booking_data: Dict[str, str]) -> Tuple[bool, str]:
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
    
    def cancel_booking(self, booking_id: str, reason: str = "") -> Tuple[bool, str]:
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
            return True, f"✅ Запись отменена!"
        
        except Exception as e:
            logger.error(f"Error canceling booking: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def confirm_booking(self, booking_id: str) -> Tuple[bool, str]:
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
            return True, f"✅ Запись подтверждена!"
        
        except Exception as e:
            logger.error(f"Error confirming booking: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def complete_booking(self, booking_id: str) -> Tuple[bool, str]:
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
