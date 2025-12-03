"""
Модуль для инициализации и форматирования полноценной БД в Google Sheets
Создает структурированную таблицу со всеми необходимыми листами
"""

import logging
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Инициализация и структурирование БД в Google Sheets"""
    
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        Инициализация инициализатора БД
        
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
            raise
    
    def initialize_database(self) -> bool:
        """
        Инициализация всей БД - создание всех необходимых листов
        """
        try:
            sheets_to_create = [
                self._create_masters_sheet,
                self._create_clients_sheet,
                self._create_bookings_sheet,
                self._create_services_sheet,
                self._create_calendar_sheet,
                self._create_reviews_sheet,
                self._create_pricing_sheet,
            ]
            
            for sheet_creator in sheets_to_create:
                if not sheet_creator():
                    logger.warning(f"Failed to create {sheet_creator.__name__}")
            
            logger.info("Database initialization completed")
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def _sheet_exists(self, sheet_name: str) -> bool:
        """Проверить существование листа"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking sheet existence: {e}")
            return False
    
    def _create_sheet(self, sheet_name: str, row_count: int = 100, column_count: int = 10) -> bool:
        """Создать новый лист"""
        if self._sheet_exists(sheet_name):
            logger.info(f"Sheet '{sheet_name}' already exists")
            return True
        
        try:
            requests = [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": {
                                "rowCount": row_count,
                                "columnCount": column_count
                            }
                        }
                    }
                }
            ]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests}
            ).execute()
            
            logger.info(f"Sheet '{sheet_name}' created")
            return True
        except Exception as e:
            logger.error(f"Error creating sheet '{sheet_name}': {e}")
            return False
    
    def _add_headers(self, sheet_name: str, headers: List[str]) -> bool:
        """Добавить заголовки в лист"""
        try:
            cell_range = f"{sheet_name}!A1:{chr(64 + len(headers))}{1}"
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=cell_range,
                valueInputOption="RAW",
                body={"values": [headers]}
            ).execute()
            
            logger.info(f"Headers added to '{sheet_name}'")
            return True
        except Exception as e:
            logger.error(f"Error adding headers to '{sheet_name}': {e}")
            return False
    
    def _format_headers(self, sheet_name: str, column_count: int) -> bool:
        """Форматировать заголовки (жирный текст, фон)"""
        try:
            end_col = chr(64 + column_count)
            requests = [
                {
                    "updateCells": {
                        "range": {
                            "sheetId": self._get_sheet_id(sheet_name),
                            "startRowIndex": 0,
                            "endRowIndex": 1
                        },
                        "rows": [
                            {
                                "values": [
                                    {
                                        "userEnteredFormat": {
                                            "textFormat": {
                                                "bold": True,
                                                "fontSize": 11,
                                                "foregroundColor": {
                                                    "red": 1,
                                                    "green": 1,
                                                    "blue": 1
                                                }
                                            },
                                            "backgroundColor": {
                                                "red": 0.2,
                                                "green": 0.2,
                                                "blue": 0.2
                                            }
                                        }
                                    }
                                ] * column_count
                            }
                        ],
                        "fields": "userEnteredFormat"
                    }
                }
            ]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests}
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error formatting headers in '{sheet_name}': {e}")
            return False
    
    def _get_sheet_id(self, sheet_name: str) -> Optional[int]:
        """Получить ID листа по его имени"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            return None
        except Exception as e:
            logger.error(f"Error getting sheet ID: {e}")
            return None
    
    # ============ СОЗДАНИЕ КОНКРЕТНЫХ ЛИСТОВ ============
    
    def _create_masters_sheet(self) -> bool:
        """Создать лист 'Мастера'"""
        sheet_name = "Мастера"
        headers = [
            "ID", "Имя", "Специальность", "Опыт (лет)", "Рейтинг",
            "Телефон", "Instagram", "Цена за сеанс (руб)", "Статус", "Описание"
        ]
        
        if not self._create_sheet(sheet_name, 100, len(headers)):
            return False
        
        if not self._add_headers(sheet_name, headers):
            return False
        
        return self._format_headers(sheet_name, len(headers))
    
    def _create_clients_sheet(self) -> bool:
        """Создать лист 'Клиенты'"""
        sheet_name = "Клиенты"
        headers = [
            "ID", "Telegram ID", "Имя", "Телефон", "Email",
            "Дата регистрации", "Статус", "Всего визитов", "Общая потрачено (руб)", "Примечания"
        ]
        
        if not self._create_sheet(sheet_name, 200, len(headers)):
            return False
        
        if not self._add_headers(sheet_name, headers):
            return False
        
        return self._format_headers(sheet_name, len(headers))
    
    def _create_bookings_sheet(self) -> bool:
        """Создать лист 'Записи'"""
        sheet_name = "Записи"
        headers = [
            "ID", "Telegram ID Клиента", "Имя клиента", "Telegram ID Мастера", "Имя мастера",
            "Услуга", "Дата/Время", "Длительность (мин)", "Цена (руб)", "Статус",
            "Дата создания", "Примечания"
        ]
        
        if not self._create_sheet(sheet_name, 300, len(headers)):
            return False
        
        if not self._add_headers(sheet_name, headers):
            return False
        
        return self._format_headers(sheet_name, len(headers))
    
    def _create_services_sheet(self) -> bool:
        """Создать лист 'Услуги'"""
        sheet_name = "Услуги"
        headers = [
            "ID", "Название", "Описание", "Длительность (мин)",
            "Базовая цена (руб)", "Категория", "Статус", "Изображение URL"
        ]
        
        if not self._create_sheet(sheet_name, 100, len(headers)):
            return False
        
        if not self._add_headers(sheet_name, headers):
            return False
        
        return self._format_headers(sheet_name, len(headers))
    
    def _create_calendar_sheet(self) -> bool:
        """Создать лист 'Расписание'"""
        sheet_name = "Расписание"
        headers = [
            "ID", "Telegram ID Мастера", "Имя мастера", "Дата", "Время начала",
            "Время окончания", "Занято/Свободно", "Тип события", "Примечания"
        ]
        
        if not self._create_sheet(sheet_name, 500, len(headers)):
            return False
        
        if not self._add_headers(sheet_name, headers):
            return False
        
        return self._format_headers(sheet_name, len(headers))
    
    def _create_reviews_sheet(self) -> bool:
        """Создать лист 'Отзывы'"""
        sheet_name = "Отзывы"
        headers = [
            "ID", "Telegram ID Клиента", "Имя клиента", "Telegram ID Мастера", "Имя мастера",
            "Оценка (1-5)", "Текст отзыва", "Дата отзыва", "ID записи", "Полезно"
        ]
        
        if not self._create_sheet(sheet_name, 200, len(headers)):
            return False
        
        if not self._add_headers(sheet_name, headers):
            return False
        
        return self._format_headers(sheet_name, len(headers))
    
    def _create_pricing_sheet(self) -> bool:
        """Создать лист 'Прайс-лист'"""
        sheet_name = "Прайс-лист"
        headers = [
            "ID", "Мастер", "Услуга", "Цена (руб)", "Комиссия (%), Чистый доход",
            "Дата добавления", "Активна", "Примечания"
        ]
        
        if not self._create_sheet(sheet_name, 150, len(headers)):
            return False
        
        if not self._add_headers(sheet_name, headers):
            return False
        
        return self._format_headers(sheet_name, len(headers))
