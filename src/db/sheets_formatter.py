"""
Модуль для работы и форматирования Google Sheets таблицы
"""

import logging
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

class SheetsFormatter:
    """Форматирование и управление Google Sheets таблицей"""
    
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        Инициализация форматировщика Sheets
        
        Args:
            credentials_file: Путь до файла credentials.json
            spreadsheet_id: ID таблицы Google Sheets
        """
        self.spreadsheet_id = spreadsheet_id
        self.credentials_file = credentials_file
        self.service = None
        self._init_service()
    
    def _init_service(self):
        """Инициализация Google Sheets API"""
        try:
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Google Sheets API initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
    
    def create_masters_sheet(self):
        """Создать и отформатировать лист 'Мастера'"""
        if not self.service:
            return False
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Мастера",
                            "gridProperties": {
                                "rowCount": 100,
                                "columnCount": 10
                            }
                        }
                    }
                }
            ]
            
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Добавить заголовки
            headers = [
                ["ID", "Имя", "Специальность", "Опыт (лет)", "Рейтинг", 
                 "Телефон", "Instagram", "Цена (руб)", "Доступность", "Описание"]
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Мастера!A1:J1",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()
            
            logger.info("Masters sheet created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating masters sheet: {e}")
            return False
    
    def create_bookings_sheet(self):
        """Создать и отформатировать лист 'Записи'"""
        if not self.service:
            return False
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Записи",
                            "gridProperties": {
                                "rowCount": 500,
                                "columnCount": 12
                            }
                        }
                    }
                }
            ]
            
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Добавить заголовки
            headers = [
                ["ID Записи", "ID Клиента", "Имя клиента", "Телефон", "Email", 
                 "Мастер", "Процедура", "Дата", "Время", "Продолжительность (мин)", 
                 "Статус", "Сумма (руб)"]
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Записи!A1:L1",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()
            
            logger.info("Bookings sheet created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating bookings sheet: {e}")
            return False
    
    def create_clients_sheet(self):
        """Создать и отформатировать лист 'Клиенты'"""
        if not self.service:
            return False
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Клиенты",
                            "gridProperties": {
                                "rowCount": 1000,
                                "columnCount": 10
                            }
                        }
                    }
                }
            ]
            
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Добавить заголовки
            headers = [
                ["ID Клиента", "Телефон", "Имя", "Email", "Telegram ID", 
                 "Дата регистрации", "Всего записей", "Всего потрачено", "Последняя запись", "Примечания"]
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Клиенты!A1:J1",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()
            
            logger.info("Clients sheet created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating clients sheet: {e}")
            return False
    
    def create_procedures_sheet(self):
        """Создать и отформатировать лист 'Услуги'"""
        if not self.service:
            return False
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Услуги",
                            "gridProperties": {
                                "rowCount": 100,
                                "columnCount": 8
                            }
                        }
                    }
                }
            ]
            
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Добавить заголовки
            headers = [
                ["ID", "Название услуги", "Описание", "Базовая цена (руб)", 
                 "Продолжительность (мин)", "Категория", "Популярность", "Активна"]
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Услуги!A1:H1",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()
            
            logger.info("Procedures sheet created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating procedures sheet: {e}")
            return False
    
    def create_reviews_sheet(self):
        """Создать и отформатировать лист 'Отзывы'"""
        if not self.service:
            return False
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Отзывы",
                            "gridProperties": {
                                "rowCount": 200,
                                "columnCount": 9
                            }
                        }
                    }
                }
            ]
            
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Добавить заголовки
            headers = [
                ["ID", "ID Клиента", "Имя клиента", "Мастер", "Услуга", 
                 "Рейтинг", "Дата", "Отзыв", "Ответ мастера"]
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Отзывы!A1:I1",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()
            
            logger.info("Reviews sheet created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating reviews sheet: {e}")
            return False
    
    def create_schedule_sheet(self):
        """Создать и отформатировать лист 'Расписание'"""
        if not self.service:
            return False
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Расписание",
                            "gridProperties": {
                                "rowCount": 500,
                                "columnCount": 8
                            }
                        }
                    }
                }
            ]
            
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Добавить заголовки
            headers = [
                ["ID", "Мастер", "День недели", "Время начала", "Время окончания", 
                 "Статус", "Перерыв", "Примечания"]
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Расписание!A1:H1",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()
            
            logger.info("Schedule sheet created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating schedule sheet: {e}")
            return False
    
    def create_prices_sheet(self):
        """Создать и отформатировать лист 'Прайс-лист'"""
        if not self.service:
            return False
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Прайс-лист",
                            "gridProperties": {
                                "rowCount": 100,
                                "columnCount": 8
                            }
                        }
                    }
                }
            ]
            
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Добавить заголовки
            headers = [
                ["ID", "Услуга", "Мастер", "Базовая цена", "Цена для постоянных", 
                 "Продолжительность", "Дополнительные услуги", "Статус"]
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Прайс-лист!A1:H1",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()
            
            logger.info("Prices sheet created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating prices sheet: {e}")
            return False
    
    def create_statistics_sheet(self):
        """Создать и отформатировать лист 'Статистика'"""
        if not self.service:
            return False
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Статистика",
                            "gridProperties": {
                                "rowCount": 200,
                                "columnCount": 10
                            }
                        }
                    }
                }
            ]
            
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Добавить заголовки
            headers = [
                ["ID", "Мастер", "Дата", "Количество записей", "Общий доход", 
                 "Средняя оценка", "Новых клиентов", "Повторных клиентов", 
                 "Отмены", "Просмотры профиля"]
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Статистика!A1:J1",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()
            
            logger.info("Statistics sheet created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating statistics sheet: {e}")
            return False
    
    def create_settings_sheet(self):
        """Создать и отформатировать лист 'Настройки'"""
        if not self.service:
            return False
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Настройки",
                            "gridProperties": {
                                "rowCount": 100,
                                "columnCount": 3
                            }
                        }
                    }
                }
            ]
            
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Добавить заголовки и базовые настройки
            headers = [
                ["Параметр", "Значение", "Описание"],
                ["Название салона", "Beauty Studio", "Наименование вашего бизнеса"],
                ["Режим работы", "09:00-21:00", "Часы работы по умолчанию"],
                ["Валюта", "RUB", "Валюта для расчётов"],
                ["Минимальное время до записи", "1", "В часах"],
                ["Макс дней бронирования вперёд", "30", "Максимум дней для записи"],
                ["SMS уведомления", "Включены", "Отправка уведомлений клиентам"],
                ["Email уведомления", "Включены", "Отправка уведомлений по email"],
                ["Комиссия платежей (%)", "2.5", "Процент комиссии за платежи"],
                ["Форма платежа", "Яндекс.Касса", "По умолчанию"]
            ]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Настройки!A1:C10",
                valueInputOption="RAW",
                body={"values": headers}
            ).execute()
            
            logger.info("Settings sheet created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating settings sheet: {e}")
            return False
    
    def format_all_sheets(self) -> bool:
        """Создать и отформатировать все листы"""
        results = []
        results.append(self.create_masters_sheet())
        results.append(self.create_bookings_sheet())
        results.append(self.create_clients_sheet())
        results.append(self.create_procedures_sheet())
        results.append(self.create_reviews_sheet())
        results.append(self.create_schedule_sheet())
        results.append(self.create_prices_sheet())
        results.append(self.create_statistics_sheet())
        results.append(self.create_settings_sheet())
        
        return all(results)
    
    def add_master(self, master_data: Dict) -> bool:
        """Добавить мастера в таблицу"""
        if not self.service:
            return False
        
        try:
            row = [
                master_data.get("id", ""),
                master_data.get("name", ""),
                master_data.get("specialty", ""),
                master_data.get("experience", ""),
                master_data.get("rating", ""),
                master_data.get("phone", ""),
                master_data.get("instagram", ""),
                master_data.get("price", ""),
                master_data.get("availability", ""),
                master_data.get("description", "")
            ]
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Мастера!A:J",
                valueInputOption="RAW",
                body={"values": [row]}
            ).execute()
            
            logger.info(f"Master added: {master_data.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding master: {e}")
            return False
    
    def add_booking(self, booking_data: Dict) -> bool:
        """Добавить запись в таблицу"""
        if not self.service:
            return False
        
        try:
            row = [
                booking_data.get("booking_id", ""),
                booking_data.get("client_id", ""),
                booking_data.get("client_name", ""),
                booking_data.get("phone", ""),
                booking_data.get("email", ""),
                booking_data.get("master", ""),
                booking_data.get("procedure", ""),
                booking_data.get("date", ""),
                booking_data.get("time", ""),
                booking_data.get("duration", ""),
                booking_data.get("status", "confirmed"),
                booking_data.get("price", "")
            ]
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Записи!A:L",
                valueInputOption="RAW",
                body={"values": [row]}
            ).execute()
            
            logger.info(f"Booking added: {booking_data.get('booking_id', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding booking: {e}")
            return False
    
    def get_masters_list(self) -> List[Dict]:
        """Получить список всех мастеров"""
        if not self.service:
            return []
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Мастера!A2:J"
            ).execute()
            
            values = result.get('values', [])
            masters = []
            
            for row in values:
                if len(row) >= 2:
                    masters.append({
                        "id": row[0] if len(row) > 0 else "",
                        "name": row[1] if len(row) > 1 else "",
                        "specialty": row[2] if len(row) > 2 else "",
                        "experience": row[3] if len(row) > 3 else "",
                        "rating": row[4] if len(row) > 4 else "",
                        "phone": row[5] if len(row) > 5 else "",
                        "instagram": row[6] if len(row) > 6 else "",
                        "price": row[7] if len(row) > 7 else "",
                    })
            
            return masters
            
        except Exception as e:
            logger.error(f"Error getting masters list: {e}")
            return []
    
    def get_clients_list(self) -> List[Dict]:
        """Получить список всех клиентов"""
        if not self.service:
            return []
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Клиенты!A2:J"
            ).execute()
            
            values = result.get('values', [])
            clients = []
            
            for row in values:
                if len(row) >= 2:
                    clients.append({
                        "id": row[0] if len(row) > 0 else "",
                        "phone": row[1] if len(row) > 1 else "",
                        "name": row[2] if len(row) > 2 else "",
                        "email": row[3] if len(row) > 3 else "",
                        "telegram_id": row[4] if len(row) > 4 else "",
                        "registered": row[5] if len(row) > 5 else "",
                        "total_bookings": row[6] if len(row) > 6 else "",
                        "total_spent": row[7] if len(row) > 7 else "",
                    })
            
            return clients
            
        except Exception as e:
            logger.error(f"Error getting clients list: {e}")
            return []
    
    def add_review(self, review_data: Dict) -> bool:
        """Добавить отзыв в таблицу"""
        if not self.service:
            return False
        
        try:
            row = [
                review_data.get("id", ""),
                review_data.get("client_id", ""),
                review_data.get("client_name", ""),
                review_data.get("master", ""),
                review_data.get("procedure", ""),
                review_data.get("rating", ""),
                review_data.get("date", ""),
                review_data.get("review", ""),
                review_data.get("master_response", "")
            ]
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Отзывы!A:I",
                valueInputOption="RAW",
                body={"values": [row]}
            ).execute()
            
            logger.info(f"Review added: {review_data.get('id', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding review: {e}")
            return False
    
    def add_schedule(self, schedule_data: Dict) -> bool:
        """Добавить расписание мастера"""
        if not self.service:
            return False
        
        try:
            row = [
                schedule_data.get("id", ""),
                schedule_data.get("master", ""),
                schedule_data.get("day_of_week", ""),
                schedule_data.get("start_time", ""),
                schedule_data.get("end_time", ""),
                schedule_data.get("status", "active"),
                schedule_data.get("break_time", ""),
                schedule_data.get("notes", "")
            ]
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Расписание!A:H",
                valueInputOption="RAW",
                body={"values": [row]}
            ).execute()
            
            logger.info(f"Schedule added: {schedule_data.get('master', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding schedule: {e}")
            return False
    
    def add_price(self, price_data: Dict) -> bool:
        """Добавить цену в прайс-лист"""
        if not self.service:
            return False
        
        try:
            row = [
                price_data.get("id", ""),
                price_data.get("procedure", ""),
                price_data.get("master", ""),
                price_data.get("base_price", ""),
                price_data.get("loyalty_price", ""),
                price_data.get("duration", ""),
                price_data.get("additional_services", ""),
                price_data.get("status", "active")
            ]
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Прайс-лист!A:H",
                valueInputOption="RAW",
                body={"values": [row]}
            ).execute()
            
            logger.info(f"Price added: {price_data.get('procedure', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding price: {e}")
            return False
    
    def add_statistics(self, stats_data: Dict) -> bool:
        """Добавить статистику"""
        if not self.service:
            return False
        
        try:
            row = [
                stats_data.get("id", ""),
                stats_data.get("master", ""),
                stats_data.get("date", ""),
                stats_data.get("bookings_count", ""),
                stats_data.get("total_income", ""),
                stats_data.get("avg_rating", ""),
                stats_data.get("new_clients", ""),
                stats_data.get("repeat_clients", ""),
                stats_data.get("cancellations", ""),
                stats_data.get("profile_views", "")
            ]
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Статистика!A:J",
                valueInputOption="RAW",
                body={"values": [row]}
            ).execute()
            
            logger.info(f"Statistics added: {stats_data.get('master', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding statistics: {e}")
            return False
    
    def update_setting(self, parameter: str, value: str) -> bool:
        """Обновить настройку в листе Настройки"""
        if not self.service:
            return False
        
        try:
            # Найти строку с параметром и обновить значение
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Настройки!A:B"
            ).execute()
            
            values = result.get('values', [])
            
            for idx, row in enumerate(values, 1):
                if len(row) > 0 and row[0] == parameter:
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"Настройки!B{idx}",
                        valueInputOption="RAW",
                        body={"values": [[value]]}
                    ).execute()
                    
                    logger.info(f"Setting updated: {parameter} = {value}")
                    return True
            
            # Если параметр не найден, добавить новый
            new_row = [parameter, value, ""]
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Настройки!A:C",
                valueInputOption="RAW",
                body={"values": [new_row]}
            ).execute()
            
            logger.info(f"New setting added: {parameter} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating setting: {e}")
            return False
    
    def get_setting(self, parameter: str) -> Optional[str]:
        """Получить значение настройки"""
        if not self.service:
            return None
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Настройки!A:B"
            ).execute()
            
            values = result.get('values', [])
            
            for row in values:
                if len(row) > 0 and row[0] == parameter:
                    return row[1] if len(row) > 1 else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting setting: {e}")
            return None


def get_sheets_formatter(credentials_file: str, spreadsheet_id: str) -> SheetsFormatter:
    """Создать экземпляр форматировщика Sheets"""
    return SheetsFormatter(credentials_file, spreadsheet_id)
