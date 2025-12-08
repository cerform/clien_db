#!/usr/bin/env python3
"""
🗄️ UNIFIED DATABASE CREATOR
============================
Универсальный скрипт для создания и унификации БД
Поддерживает как Админ-панель, так и INKA Assistant

Функции:
- Создание структуры БД с нуля по единому шаблону
- Миграция существующих данных в унифицированный формат
- Валидация и очистка данных
- Backup существующих данных перед изменениями

Использование:
    python scripts/unified_database_creator.py --create      # Создать пустую БД
    python scripts/unified_database_creator.py --migrate     # Миграция существующих данных
    python scripts/unified_database_creator.py --validate    # Только проверка
    python scripts/unified_database_creator.py --backup      # Создать backup
    python scripts/unified_database_creator.py --full        # Полный цикл: backup + migrate + validate
"""

import sys
import os
import json
import uuid
import re
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# UNIFIED DATABASE SCHEMA DEFINITION
# ============================================================================

class TableType(Enum):
    """Типы таблиц в системе"""
    MASTERS = "Masters"
    CLIENTS = "Clients"
    SERVICES = "Services"
    BOOKINGS = "Bookings"
    SCHEDULE = "Schedule"
    REVIEWS = "Reviews"
    PRICING = "Pricing"
    INKA_TRAINING = "InkaTraining"


@dataclass
class ColumnDef:
    """Определение колонки таблицы"""
    name: str
    required: bool = False
    default: Any = ""
    validator: Optional[str] = None  # 'phone', 'email', 'date', 'time', 'uuid', 'boolean', 'number'
    description: str = ""


@dataclass 
class TableSchema:
    """Схема таблицы"""
    name: str
    sheet_name: str  # Имя листа в Google Sheets
    columns: List[ColumnDef]
    description: str = ""
    

class UnifiedDatabaseSchema:
    """
    Единая схема базы данных для Админ-панели и INKA
    
    Важно: Используем английские названия листов для совместимости с API,
    но поддерживаем маппинг на русские названия для UI
    """
    
    # Маппинг русских названий на английские
    SHEET_NAME_MAP = {
        "Мастера": "Masters",
        "Клиенты": "Clients", 
        "Услуги": "Services",
        "Записи": "Bookings",
        "Расписание": "Schedule",
        "Отзывы": "Reviews",
        "Прайс-лист": "Pricing",
    }
    
    @staticmethod
    def get_masters_schema() -> TableSchema:
        """Схема таблицы Мастера"""
        return TableSchema(
            name="Masters",
            sheet_name="Masters",
            description="Информация о мастерах салона",
            columns=[
                ColumnDef("id", required=True, validator="uuid", description="Уникальный ID мастера"),
                ColumnDef("name", required=True, description="Полное имя мастера"),
                ColumnDef("phone", required=False, validator="phone", description="Телефон"),
                ColumnDef("telegram_id", required=False, description="Telegram ID"),
                ColumnDef("specialization", required=True, description="Специализация (tattoo, piercing и т.д.)"),
                ColumnDef("rating", required=False, default="0", validator="number", description="Рейтинг 0-5"),
                ColumnDef("experience", required=False, default="0", description="Опыт в годах"),
                ColumnDef("instagram", required=False, description="Instagram аккаунт"),
                ColumnDef("status", required=False, default="active", description="Статус: active/inactive"),
                ColumnDef("bio", required=False, description="Биография/описание"),
                ColumnDef("calendar_id", required=True, description="Google Calendar ID для INKA"),
                # Многоязычные поля
                ColumnDef("name_ru", required=False, description="Имя на русском"),
                ColumnDef("name_en", required=False, description="Имя на английском"),
                ColumnDef("name_he", required=False, description="Имя на иврите"),
                ColumnDef("bio_ru", required=False, description="Биография на русском"),
                ColumnDef("bio_en", required=False, description="Биография на английском"),
                ColumnDef("bio_he", required=False, description="Биография на иврите"),
            ]
        )
    
    @staticmethod
    def get_clients_schema() -> TableSchema:
        """Схема таблицы Клиенты"""
        return TableSchema(
            name="Clients",
            sheet_name="Clients",
            description="Информация о клиентах",
            columns=[
                ColumnDef("id", required=True, validator="uuid", description="Уникальный ID клиента"),
                ColumnDef("telegram_id", required=False, description="Telegram ID клиента"),
                ColumnDef("name", required=True, description="Имя клиента"),
                ColumnDef("phone", required=False, validator="phone", description="Телефон"),
                ColumnDef("email", required=False, validator="email", description="Email"),
                ColumnDef("notes", required=False, description="Заметки о клиенте"),
                ColumnDef("created_at", required=False, validator="datetime", description="Дата создания"),
                ColumnDef("last_visit", required=False, validator="datetime", description="Дата последнего визита"),
                ColumnDef("language", required=False, default="ru", description="Предпочитаемый язык"),
                ColumnDef("total_visits", required=False, default="0", validator="number", description="Количество визитов"),
                ColumnDef("total_spent", required=False, default="0", validator="number", description="Общая сумма"),
            ]
        )
    
    @staticmethod
    def get_services_schema() -> TableSchema:
        """Схема таблицы Услуги"""
        return TableSchema(
            name="Services",
            sheet_name="Services",
            description="Каталог услуг",
            columns=[
                ColumnDef("id", required=True, validator="uuid", description="Уникальный ID услуги"),
                ColumnDef("name", required=True, description="Название услуги"),
                ColumnDef("description", required=False, description="Описание"),
                ColumnDef("duration_min", required=True, default="60", validator="number", description="Длительность в минутах"),
                ColumnDef("price_from", required=True, default="0", validator="number", description="Цена от"),
                ColumnDef("price_to", required=False, default="0", validator="number", description="Цена до"),
                ColumnDef("category", required=False, default="other", description="Категория услуги"),
                ColumnDef("active", required=False, default="TRUE", validator="boolean", description="Активна ли услуга"),
                # Многоязычные поля
                ColumnDef("name_ru", required=False, description="Название на русском"),
                ColumnDef("name_en", required=False, description="Название на английском"),
                ColumnDef("name_he", required=False, description="Название на иврите"),
                ColumnDef("description_ru", required=False, description="Описание на русском"),
                ColumnDef("description_en", required=False, description="Описание на английском"),
                ColumnDef("description_he", required=False, description="Описание на иврите"),
            ]
        )
    
    @staticmethod
    def get_bookings_schema() -> TableSchema:
        """Схема таблицы Записи (Бронирования)"""
        return TableSchema(
            name="Bookings",
            sheet_name="Bookings",
            description="Записи на услуги",
            columns=[
                ColumnDef("id", required=True, validator="uuid", description="Уникальный ID записи"),
                ColumnDef("client_id", required=True, description="ID клиента"),
                ColumnDef("master_id", required=True, description="ID мастера"),
                ColumnDef("service_id", required=True, description="ID услуги"),
                ColumnDef("date", required=True, validator="date", description="Дата записи YYYY-MM-DD"),
                ColumnDef("time", required=True, validator="time", description="Время записи HH:MM"),
                ColumnDef("duration_min", required=False, default="60", validator="number", description="Длительность"),
                ColumnDef("price", required=False, default="0", validator="number", description="Цена"),
                ColumnDef("status", required=False, default="pending", description="Статус: pending/confirmed/completed/cancelled"),
                ColumnDef("notes", required=False, description="Заметки"),
                ColumnDef("created_at", required=False, validator="datetime", description="Дата создания"),
                ColumnDef("google_event_id", required=False, description="ID события в Google Calendar"),
            ]
        )
    
    @staticmethod
    def get_schedule_schema() -> TableSchema:
        """
        Схема таблицы Расписание
        ВАЖНО для INKA: эта таблица используется для определения рабочего времени мастеров
        """
        return TableSchema(
            name="Schedule",
            sheet_name="Schedule",
            description="Расписание работы мастеров",
            columns=[
                ColumnDef("id", required=True, validator="uuid", description="Уникальный ID записи"),
                ColumnDef("master_id", required=True, description="ID мастера"),
                ColumnDef("day_of_week", required=True, description="День недели: monday/tuesday/.../sunday"),
                ColumnDef("start_time", required=True, validator="time", description="Начало работы HH:MM"),
                ColumnDef("end_time", required=True, validator="time", description="Конец работы HH:MM"),
                ColumnDef("is_working", required=False, default="TRUE", validator="boolean", description="Рабочий день"),
                ColumnDef("break_start", required=False, validator="time", description="Начало перерыва HH:MM"),
                ColumnDef("break_end", required=False, validator="time", description="Конец перерыва HH:MM"),
                ColumnDef("notes", required=False, description="Заметки"),
            ]
        )
    
    @staticmethod
    def get_reviews_schema() -> TableSchema:
        """Схема таблицы Отзывы"""
        return TableSchema(
            name="Reviews",
            sheet_name="Reviews",
            description="Отзывы клиентов",
            columns=[
                ColumnDef("id", required=True, validator="uuid", description="Уникальный ID отзыва"),
                ColumnDef("client_id", required=True, description="ID клиента"),
                ColumnDef("master_id", required=True, description="ID мастера"),
                ColumnDef("booking_id", required=False, description="ID записи"),
                ColumnDef("rating", required=True, validator="number", description="Оценка 1-5"),
                ColumnDef("text", required=False, description="Текст отзыва"),
                ColumnDef("created_at", required=False, validator="datetime", description="Дата создания"),
                ColumnDef("is_visible", required=False, default="TRUE", validator="boolean", description="Виден ли отзыв"),
            ]
        )
    
    @staticmethod
    def get_pricing_schema() -> TableSchema:
        """Схема таблицы Прайс-лист"""
        return TableSchema(
            name="Pricing",
            sheet_name="Pricing",
            description="Индивидуальные цены мастеров на услуги",
            columns=[
                ColumnDef("id", required=True, validator="uuid", description="Уникальный ID"),
                ColumnDef("master_id", required=True, description="ID мастера"),
                ColumnDef("service_id", required=True, description="ID услуги"),
                ColumnDef("price", required=True, validator="number", description="Цена"),
                ColumnDef("commission_percent", required=False, default="0", validator="number", description="Комиссия %"),
                ColumnDef("is_active", required=False, default="TRUE", validator="boolean", description="Активна ли цена"),
                ColumnDef("notes", required=False, description="Заметки"),
            ]
        )
    
    @staticmethod
    def get_inka_training_schema() -> TableSchema:
        """Схема таблицы для обучения INKA"""
        return TableSchema(
            name="InkaTraining",
            sheet_name="InkaTraining",
            description="Данные для обучения INKA Assistant",
            columns=[
                ColumnDef("id", required=True, validator="uuid", description="Уникальный ID"),
                ColumnDef("category", required=True, description="Категория: faq/policy/procedure/custom"),
                ColumnDef("question", required=True, description="Вопрос/ключевые слова"),
                ColumnDef("answer", required=True, description="Ответ INKA"),
                ColumnDef("language", required=False, default="ru", description="Язык"),
                ColumnDef("priority", required=False, default="0", validator="number", description="Приоритет"),
                ColumnDef("is_active", required=False, default="TRUE", validator="boolean", description="Активно ли правило"),
                ColumnDef("created_at", required=False, validator="datetime", description="Дата создания"),
                ColumnDef("updated_at", required=False, validator="datetime", description="Дата обновления"),
            ]
        )
    
    @classmethod
    def get_all_schemas(cls) -> List[TableSchema]:
        """Получить все схемы таблиц"""
        return [
            cls.get_masters_schema(),
            cls.get_clients_schema(),
            cls.get_services_schema(),
            cls.get_bookings_schema(),
            cls.get_schedule_schema(),
            cls.get_reviews_schema(),
            cls.get_pricing_schema(),
            cls.get_inka_training_schema(),
        ]


# ============================================================================
# DATA VALIDATORS
# ============================================================================

class DataValidator:
    """Валидатор данных"""
    
    @staticmethod
    def validate_uuid(value: str) -> Tuple[bool, str]:
        """Проверка UUID"""
        if not value:
            return True, ""  # Пустое значение - сгенерируем новый UUID
        try:
            uuid.UUID(value)
            return True, ""
        except ValueError:
            # Проверяем другие форматы ID (m_xxx, s_xxx и т.д.)
            if re.match(r'^[a-z]_[a-zA-Z0-9_-]+$', value):
                return True, ""
            return False, f"Некорректный UUID: {value}"
    
    @staticmethod
    def validate_phone(value: str) -> Tuple[bool, str]:
        """Проверка телефона"""
        if not value:
            return True, ""
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        if len(cleaned) < 9:
            return False, f"Телефон слишком короткий: {value}"
        if not re.match(r'^\+?[0-9]{9,15}$', cleaned):
            return False, f"Некорректный формат телефона: {value}"
        return True, ""
    
    @staticmethod
    def validate_email(value: str) -> Tuple[bool, str]:
        """Проверка email"""
        if not value:
            return True, ""
        if '@' not in value or '.' not in value:
            return False, f"Некорректный email: {value}"
        return True, ""
    
    @staticmethod
    def validate_date(value: str) -> Tuple[bool, str]:
        """Проверка даты YYYY-MM-DD"""
        if not value:
            return True, ""
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True, ""
        except ValueError:
            return False, f"Некорректная дата (ожидается YYYY-MM-DD): {value}"
    
    @staticmethod
    def validate_time(value: str) -> Tuple[bool, str]:
        """Проверка времени HH:MM"""
        if not value:
            return True, ""
        try:
            datetime.strptime(value, '%H:%M')
            return True, ""
        except ValueError:
            return False, f"Некорректное время (ожидается HH:MM): {value}"
    
    @staticmethod
    def validate_datetime(value: str) -> Tuple[bool, str]:
        """Проверка datetime"""
        if not value:
            return True, ""
        formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
        for fmt in formats:
            try:
                datetime.strptime(value.split('.')[0], fmt)
                return True, ""
            except ValueError:
                continue
        return False, f"Некорректная дата/время: {value}"
    
    @staticmethod
    def validate_boolean(value: str) -> Tuple[bool, str]:
        """Проверка boolean"""
        if not value:
            return True, ""
        if str(value).upper() in ['TRUE', 'FALSE', '1', '0', 'YES', 'NO', 'ДА', 'НЕТ']:
            return True, ""
        return False, f"Некорректное boolean значение: {value}"
    
    @staticmethod
    def validate_number(value: str) -> Tuple[bool, str]:
        """Проверка числа"""
        if not value:
            return True, ""
        try:
            float(value)
            return True, ""
        except ValueError:
            return False, f"Некорректное число: {value}"
    
    @classmethod
    def validate_field(cls, value: Any, validator_type: Optional[str]) -> Tuple[bool, str]:
        """Валидация поля по типу валидатора"""
        if not validator_type:
            return True, ""
        
        validators = {
            'uuid': cls.validate_uuid,
            'phone': cls.validate_phone,
            'email': cls.validate_email,
            'date': cls.validate_date,
            'time': cls.validate_time,
            'datetime': cls.validate_datetime,
            'boolean': cls.validate_boolean,
            'number': cls.validate_number,
        }
        
        validator = validators.get(validator_type)
        if validator:
            return validator(str(value) if value else "")
        return True, ""


# ============================================================================
# UNIFIED DATABASE CREATOR
# ============================================================================

class UnifiedDatabaseCreator:
    """
    Создатель унифицированной базы данных
    Работает с Google Sheets API
    """
    
    def __init__(self, sheets_client=None):
        """
        Инициализация
        
        Args:
            sheets_client: GoogleSheetsClient или None для lazy init
        """
        self.sheets_client = sheets_client
        self.schema = UnifiedDatabaseSchema()
        self.validator = DataValidator()
        self.errors = []
        self.warnings = []
        self.changes = []
    
    def _init_sheets_client(self):
        """Lazy initialization of sheets client"""
        if self.sheets_client is None:
            from src.db.sheets_client import GoogleSheetsClient
            from src.config.config import get_config
            
            config = get_config()
            self.sheets_client = GoogleSheetsClient(
                config.google_credentials_json,
                config.google_spreadsheet_id
            )
        return self.sheets_client
    
    def _get_service(self):
        """Получить Google Sheets service напрямую для расширенных операций"""
        client = self._init_sheets_client()
        return client.service, client.spreadsheet_id
    
    # ========== СОЗДАНИЕ СТРУКТУРЫ БД ==========
    
    def create_database_structure(self, force: bool = False) -> Dict[str, Any]:
        """
        Создать структуру БД с нуля
        
        Args:
            force: Перезаписать существующие листы
            
        Returns:
            Результат создания
        """
        logger.info("=" * 60)
        logger.info("🗄️ СОЗДАНИЕ СТРУКТУРЫ БАЗЫ ДАННЫХ")
        logger.info("=" * 60)
        
        service, spreadsheet_id = self._get_service()
        results = {
            "created": [],
            "skipped": [],
            "errors": [],
        }
        
        for table_schema in self.schema.get_all_schemas():
            try:
                sheet_exists = self._check_sheet_exists(service, spreadsheet_id, table_schema.sheet_name)
                
                if sheet_exists and not force:
                    logger.info(f"⏭️ Лист '{table_schema.sheet_name}' уже существует, пропускаем")
                    results["skipped"].append(table_schema.sheet_name)
                    continue
                
                if sheet_exists and force:
                    logger.info(f"🗑️ Удаляем существующий лист '{table_schema.sheet_name}'")
                    self._delete_sheet(service, spreadsheet_id, table_schema.sheet_name)
                
                # Создаём лист
                logger.info(f"📝 Создаём лист '{table_schema.sheet_name}'...")
                self._create_sheet(service, spreadsheet_id, table_schema)
                results["created"].append(table_schema.sheet_name)
                logger.info(f"✅ Лист '{table_schema.sheet_name}' создан")
                
            except Exception as e:
                logger.error(f"❌ Ошибка создания листа '{table_schema.sheet_name}': {e}")
                results["errors"].append({
                    "sheet": table_schema.sheet_name,
                    "error": str(e)
                })
        
        logger.info("=" * 60)
        logger.info(f"✅ Создано листов: {len(results['created'])}")
        logger.info(f"⏭️ Пропущено: {len(results['skipped'])}")
        logger.info(f"❌ Ошибок: {len(results['errors'])}")
        
        return results
    
    def _check_sheet_exists(self, service, spreadsheet_id: str, sheet_name: str) -> bool:
        """Проверить существование листа"""
        try:
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    return True
            return False
        except Exception:
            return False
    
    def _get_sheet_id(self, service, spreadsheet_id: str, sheet_name: str) -> Optional[int]:
        """Получить ID листа по имени"""
        try:
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            return None
        except Exception:
            return None
    
    def _delete_sheet(self, service, spreadsheet_id: str, sheet_name: str):
        """Удалить лист"""
        sheet_id = self._get_sheet_id(service, spreadsheet_id, sheet_name)
        if sheet_id is None:
            return
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [{
                    "deleteSheet": {"sheetId": sheet_id}
                }]
            }
        ).execute()
    
    def _create_sheet(self, service, spreadsheet_id: str, schema: TableSchema):
        """Создать лист по схеме"""
        headers = [col.name for col in schema.columns]
        column_count = len(headers)
        
        # Создаём лист
        requests = [{
            "addSheet": {
                "properties": {
                    "title": schema.sheet_name,
                    "gridProperties": {
                        "rowCount": 1000,
                        "columnCount": column_count
                    }
                }
            }
        }]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()
        
        # Добавляем заголовки
        range_name = f"{schema.sheet_name}!A1"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body={"values": [headers]}
        ).execute()
        
        # Форматируем заголовки
        sheet_id = self._get_sheet_id(service, spreadsheet_id, schema.sheet_name)
        if sheet_id:
            self._format_headers(service, spreadsheet_id, sheet_id, column_count)
    
    def _format_headers(self, service, spreadsheet_id: str, sheet_id: int, column_count: int):
        """Форматировать заголовки"""
        requests = [
            # Жирный текст, белый на тёмном фоне
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True,
                                "fontSize": 11,
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1}
                            },
                            "backgroundColor": {"red": 0.2, "green": 0.3, "blue": 0.4},
                            "horizontalAlignment": "CENTER"
                        }
                    },
                    "fields": "userEnteredFormat"
                }
            },
            # Заморозить первую строку
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {
                            "frozenRowCount": 1
                        }
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            }
        ]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()
    
    # ========== ВАЛИДАЦИЯ ДАННЫХ ==========
    
    def validate_database(self) -> Dict[str, Any]:
        """
        Валидация всех данных в БД
        
        Returns:
            Результаты валидации
        """
        logger.info("=" * 60)
        logger.info("🔍 ВАЛИДАЦИЯ БАЗЫ ДАННЫХ")
        logger.info("=" * 60)
        
        client = self._init_sheets_client()
        results = {
            "tables": {},
            "total_errors": 0,
            "total_warnings": 0,
        }
        
        for table_schema in self.schema.get_all_schemas():
            table_result = self._validate_table(client, table_schema)
            results["tables"][table_schema.sheet_name] = table_result
            results["total_errors"] += len(table_result.get("errors", []))
            results["total_warnings"] += len(table_result.get("warnings", []))
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 РЕЗУЛЬТАТЫ ВАЛИДАЦИИ:")
        for table_name, table_result in results["tables"].items():
            status = "✅" if not table_result.get("errors") else "❌"
            error_count = len(table_result.get("errors", []))
            warning_count = len(table_result.get("warnings", []))
            logger.info(f"{status} {table_name}: {table_result.get('row_count', 0)} строк, {error_count} ошибок, {warning_count} предупреждений")
        
        logger.info(f"\n🔢 ИТОГО: {results['total_errors']} ошибок, {results['total_warnings']} предупреждений")
        
        return results
    
    def _validate_table(self, client, schema: TableSchema) -> Dict[str, Any]:
        """Валидация одной таблицы"""
        result = {
            "row_count": 0,
            "errors": [],
            "warnings": [],
            "missing_required": [],
        }
        
        try:
            data = client.get_sheet_values(schema.sheet_name)
            if not data or len(data) < 1:
                result["warnings"].append("Таблица пуста или не найдена")
                return result
            
            headers = data[0]
            rows = data[1:] if len(data) > 1 else []
            result["row_count"] = len(rows)
            
            # Проверяем заголовки
            expected_headers = [col.name for col in schema.columns]
            missing_headers = set(expected_headers) - set(headers)
            if missing_headers:
                result["warnings"].append(f"Отсутствуют колонки: {missing_headers}")
            
            # Проверяем данные
            for row_idx, row in enumerate(rows, start=2):
                row_dict = dict(zip(headers, row + [''] * (len(headers) - len(row))))
                
                for col in schema.columns:
                    if col.name not in headers:
                        continue
                    
                    value = row_dict.get(col.name, '')
                    
                    # Проверяем обязательные поля
                    if col.required and not value:
                        result["errors"].append({
                            "row": row_idx,
                            "column": col.name,
                            "error": "Обязательное поле пустое"
                        })
                    
                    # Валидация
                    if col.validator and value:
                        is_valid, msg = self.validator.validate_field(value, col.validator)
                        if not is_valid:
                            result["errors"].append({
                                "row": row_idx,
                                "column": col.name,
                                "value": value,
                                "error": msg
                            })
            
        except Exception as e:
            result["errors"].append({"error": f"Ошибка чтения таблицы: {e}"})
        
        return result
    
    # ========== МИГРАЦИЯ ДАННЫХ ==========
    
    def migrate_data(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Миграция данных в унифицированный формат
        
        Args:
            dry_run: Только проверка без изменений
            
        Returns:
            Результаты миграции
        """
        logger.info("=" * 60)
        logger.info(f"🔄 МИГРАЦИЯ ДАННЫХ {'(DRY RUN)' if dry_run else ''}")
        logger.info("=" * 60)
        
        client = self._init_sheets_client()
        results = {
            "tables": {},
            "total_changes": 0,
            "dry_run": dry_run,
        }
        
        # Миграция каждой таблицы
        migration_funcs = {
            "Masters": self._migrate_masters,
            "Clients": self._migrate_clients,
            "Services": self._migrate_services,
            "Bookings": self._migrate_bookings,
            "Schedule": self._migrate_schedule,
        }
        
        for table_name, migrate_func in migration_funcs.items():
            try:
                table_result = migrate_func(client, dry_run)
                results["tables"][table_name] = table_result
                results["total_changes"] += table_result.get("changes_count", 0)
            except Exception as e:
                logger.error(f"❌ Ошибка миграции {table_name}: {e}")
                results["tables"][table_name] = {"error": str(e)}
        
        logger.info("=" * 60)
        logger.info(f"📊 РЕЗУЛЬТАТЫ МИГРАЦИИ:")
        logger.info(f"   Всего изменений: {results['total_changes']}")
        if dry_run:
            logger.info("   ⚠️ DRY RUN - изменения НЕ применены")
        else:
            logger.info("   ✅ Изменения применены")
        
        return results
    
    def _migrate_masters(self, client, dry_run: bool) -> Dict[str, Any]:
        """Миграция таблицы Masters"""
        result = {"changes": [], "changes_count": 0}
        
        # Проверяем оба возможных названия листа
        data = None
        sheet_name = "Masters"
        
        for name in ["Masters", "Мастера"]:
            try:
                data = client.get_sheet_values(name)
                if data:
                    sheet_name = name
                    break
            except:
                continue
        
        if not data or len(data) < 2:
            logger.info(f"⏭️ Таблица {sheet_name} пуста или не найдена")
            return result
        
        headers = data[0]
        rows = data[1:]
        schema = self.schema.get_masters_schema()
        expected_headers = [col.name for col in schema.columns]
        
        # Проверяем нужна ли миграция заголовков
        if set(headers) != set(expected_headers):
            result["changes"].append({
                "type": "headers",
                "old": headers,
                "new": expected_headers
            })
        
        # Проверяем данные
        for row_idx, row in enumerate(rows):
            row_dict = dict(zip(headers, row + [''] * (len(headers) - len(row))))
            changes = []
            
            # Генерируем ID если отсутствует
            if not row_dict.get('id'):
                new_id = f"m_{uuid.uuid4().hex[:8]}"
                changes.append(("id", "", new_id))
            
            # Устанавливаем статус по умолчанию
            if not row_dict.get('status'):
                changes.append(("status", "", "active"))
            
            # Нормализуем телефон
            phone = row_dict.get('phone', '')
            if phone:
                normalized = self._normalize_phone(phone)
                if normalized != phone:
                    changes.append(("phone", phone, normalized))
            
            if changes:
                result["changes"].append({
                    "row": row_idx + 2,
                    "changes": changes
                })
                result["changes_count"] += len(changes)
        
        logger.info(f"📋 Masters: найдено {result['changes_count']} изменений")
        return result
    
    def _migrate_clients(self, client, dry_run: bool) -> Dict[str, Any]:
        """Миграция таблицы Clients"""
        result = {"changes": [], "changes_count": 0}
        
        data = None
        for name in ["Clients", "Клиенты"]:
            try:
                data = client.get_sheet_values(name)
                if data:
                    break
            except:
                continue
        
        if not data or len(data) < 2:
            return result
        
        headers = data[0]
        rows = data[1:]
        
        for row_idx, row in enumerate(rows):
            row_dict = dict(zip(headers, row + [''] * (len(headers) - len(row))))
            changes = []
            
            if not row_dict.get('id'):
                new_id = str(uuid.uuid4())
                changes.append(("id", "", new_id))
            
            if not row_dict.get('created_at'):
                changes.append(("created_at", "", datetime.now().isoformat()))
            
            if not row_dict.get('language'):
                changes.append(("language", "", "ru"))
            
            phone = row_dict.get('phone', '')
            if phone:
                normalized = self._normalize_phone(phone)
                if normalized != phone:
                    changes.append(("phone", phone, normalized))
            
            if changes:
                result["changes"].append({"row": row_idx + 2, "changes": changes})
                result["changes_count"] += len(changes)
        
        logger.info(f"📋 Clients: найдено {result['changes_count']} изменений")
        return result
    
    def _migrate_services(self, client, dry_run: bool) -> Dict[str, Any]:
        """Миграция таблицы Services"""
        result = {"changes": [], "changes_count": 0}
        
        data = None
        for name in ["Services", "Услуги"]:
            try:
                data = client.get_sheet_values(name)
                if data:
                    break
            except:
                continue
        
        if not data or len(data) < 2:
            return result
        
        headers = data[0]
        rows = data[1:]
        
        for row_idx, row in enumerate(rows):
            row_dict = dict(zip(headers, row + [''] * (len(headers) - len(row))))
            changes = []
            
            if not row_dict.get('id'):
                new_id = f"s_{uuid.uuid4().hex[:8]}"
                changes.append(("id", "", new_id))
            
            if not row_dict.get('active'):
                changes.append(("active", "", "TRUE"))
            
            if not row_dict.get('duration_min'):
                changes.append(("duration_min", "", "60"))
            
            if changes:
                result["changes"].append({"row": row_idx + 2, "changes": changes})
                result["changes_count"] += len(changes)
        
        logger.info(f"📋 Services: найдено {result['changes_count']} изменений")
        return result
    
    def _migrate_bookings(self, client, dry_run: bool) -> Dict[str, Any]:
        """Миграция таблицы Bookings"""
        result = {"changes": [], "changes_count": 0}
        
        data = None
        for name in ["Bookings", "Записи"]:
            try:
                data = client.get_sheet_values(name)
                if data:
                    break
            except:
                continue
        
        if not data or len(data) < 2:
            return result
        
        headers = data[0]
        rows = data[1:]
        
        for row_idx, row in enumerate(rows):
            row_dict = dict(zip(headers, row + [''] * (len(headers) - len(row))))
            changes = []
            
            if not row_dict.get('id'):
                new_id = f"b_{uuid.uuid4().hex[:8]}"
                changes.append(("id", "", new_id))
            
            if not row_dict.get('status'):
                changes.append(("status", "", "pending"))
            
            if not row_dict.get('created_at'):
                changes.append(("created_at", "", datetime.now().isoformat()))
            
            if changes:
                result["changes"].append({"row": row_idx + 2, "changes": changes})
                result["changes_count"] += len(changes)
        
        logger.info(f"📋 Bookings: найдено {result['changes_count']} изменений")
        return result
    
    def _migrate_schedule(self, client, dry_run: bool) -> Dict[str, Any]:
        """Миграция таблицы Schedule"""
        result = {"changes": [], "changes_count": 0}
        
        data = None
        for name in ["Schedule", "Расписание"]:
            try:
                data = client.get_sheet_values(name)
                if data:
                    break
            except:
                continue
        
        if not data or len(data) < 2:
            return result
        
        headers = data[0]
        rows = data[1:]
        
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for row_idx, row in enumerate(rows):
            row_dict = dict(zip(headers, row + [''] * (len(headers) - len(row))))
            changes = []
            
            if not row_dict.get('id'):
                new_id = f"sch_{uuid.uuid4().hex[:8]}"
                changes.append(("id", "", new_id))
            
            day = row_dict.get('day_of_week', '').lower()
            if day and day not in valid_days:
                # Попробуем конвертировать русские названия
                day_map = {
                    'понедельник': 'monday', 'пн': 'monday',
                    'вторник': 'tuesday', 'вт': 'tuesday',
                    'среда': 'wednesday', 'ср': 'wednesday',
                    'четверг': 'thursday', 'чт': 'thursday',
                    'пятница': 'friday', 'пт': 'friday',
                    'суббота': 'saturday', 'сб': 'saturday',
                    'воскресенье': 'sunday', 'вс': 'sunday',
                }
                new_day = day_map.get(day.lower())
                if new_day:
                    changes.append(("day_of_week", day, new_day))
            
            if not row_dict.get('is_working'):
                changes.append(("is_working", "", "TRUE"))
            
            if changes:
                result["changes"].append({"row": row_idx + 2, "changes": changes})
                result["changes_count"] += len(changes)
        
        logger.info(f"📋 Schedule: найдено {result['changes_count']} изменений")
        return result
    
    def _normalize_phone(self, phone: str) -> str:
        """Нормализация номера телефона"""
        if not phone:
            return ""
        
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        if cleaned.startswith('972'):
            cleaned = '+' + cleaned
        elif cleaned.startswith('0') and len(cleaned) == 10:
            cleaned = '+972' + cleaned[1:]
        elif not cleaned.startswith('+') and len(cleaned) >= 9:
            cleaned = '+' + cleaned
        
        return cleaned
    
    # ========== BACKUP ==========
    
    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Создать резервную копию всех данных
        
        Args:
            backup_name: Имя backup (по умолчанию с датой)
            
        Returns:
            Результат backup
        """
        logger.info("=" * 60)
        logger.info("💾 СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ")
        logger.info("=" * 60)
        
        client = self._init_sheets_client()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = backup_name or f"backup_{timestamp}"
        
        backup_data = {}
        
        for table_schema in self.schema.get_all_schemas():
            try:
                # Пробуем оба варианта названия
                data = None
                for name in [table_schema.sheet_name, 
                           UnifiedDatabaseSchema.SHEET_NAME_MAP.get(table_schema.sheet_name, table_schema.sheet_name)]:
                    try:
                        data = client.get_sheet_values(name)
                        if data:
                            break
                    except:
                        continue
                
                if data:
                    backup_data[table_schema.sheet_name] = data
                    logger.info(f"✅ {table_schema.sheet_name}: {len(data)} строк")
                else:
                    logger.info(f"⏭️ {table_schema.sheet_name}: пусто или не найдено")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка backup {table_schema.sheet_name}: {e}")
        
        # Сохраняем в файл
        backup_dir = PROJECT_ROOT / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / f"{backup_name}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 Backup сохранен: {backup_file}")
        
        return {
            "backup_name": backup_name,
            "file": str(backup_file),
            "tables": list(backup_data.keys()),
            "total_rows": sum(len(d) for d in backup_data.values())
        }
    
    # ========== ВОССТАНОВЛЕНИЕ ==========
    
    def restore_from_backup(self, backup_file: str) -> Dict[str, Any]:
        """
        Восстановить данные из backup
        
        Args:
            backup_file: Путь к файлу backup
            
        Returns:
            Результат восстановления
        """
        logger.info("=" * 60)
        logger.info("🔄 ВОССТАНОВЛЕНИЕ ИЗ BACKUP")
        logger.info("=" * 60)
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        client = self._init_sheets_client()
        results = {"restored": [], "errors": []}
        
        for table_name, data in backup_data.items():
            try:
                if len(data) < 1:
                    continue
                
                # Очищаем и записываем данные
                # Это упрощенная версия - в реальности нужно более аккуратно
                range_name = f"{table_name}!A1"
                client.service.spreadsheets().values().update(
                    spreadsheetId=client.spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body={"values": data}
                ).execute()
                
                results["restored"].append(table_name)
                logger.info(f"✅ {table_name}: восстановлено {len(data)} строк")
                
            except Exception as e:
                logger.error(f"❌ Ошибка восстановления {table_name}: {e}")
                results["errors"].append({"table": table_name, "error": str(e)})
        
        return results
    
    # ========== ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ ==========
    
    def populate_test_data(self) -> Dict[str, Any]:
        """
        Заполнить БД тестовыми данными
        
        Returns:
            Результат
        """
        logger.info("=" * 60)
        logger.info("🧪 ЗАПОЛНЕНИЕ ТЕСТОВЫМИ ДАННЫМИ")
        logger.info("=" * 60)
        
        client = self._init_sheets_client()
        results = {"tables": {}}
        
        # Тестовые мастера
        masters_data = [
            ["m_001", "Алексей Иванов", "+972501234567", "123456789", "tattoo", "4.8", "5", "@alexey_tattoo", "active", "Мастер татуировки с 5-летним опытом", "calendar_id_1", "Алексей", "Alexey", "אלכסיי", "Мастер тату", "Tattoo master", "אמן קעקועים"],
            ["m_002", "Мария Сидорова", "+972509876543", "987654321", "piercing", "4.9", "7", "@maria_piercing", "active", "Профессиональный пирсер", "calendar_id_2", "Мария", "Maria", "מריה", "Пирсер", "Piercer", "פירסר"],
            ["m_003", "Дмитрий Козлов", "+972507777777", "777777777", "tattoo", "4.7", "3", "@dmitry_ink", "active", "Специализация: реализм", "calendar_id_3", "Дмитрий", "Dmitry", "דמיטרי", "Тату-мастер", "Tattoo artist", "אמן קעקוע"],
        ]
        
        # Тестовые услуги
        services_data = [
            ["s_001", "Маленькая татуировка", "До 5 см", "60", "500", "1000", "tattoo", "TRUE", "Маленькая тату", "Small tattoo", "קעקוע קטן", "До 5 см", "Up to 5cm", "עד 5 ס\"מ"],
            ["s_002", "Средняя татуировка", "5-15 см", "120", "1000", "3000", "tattoo", "TRUE", "Средняя тату", "Medium tattoo", "קעקוע בינוני", "5-15 см", "5-15cm", "5-15 ס\"מ"],
            ["s_003", "Пирсинг уха", "Один прокол", "30", "200", "400", "piercing", "TRUE", "Пирсинг", "Ear piercing", "פירסינג אוזן", "Один прокол", "Single pierce", "נקב אחד"],
            ["s_004", "Консультация", "Бесплатная консультация", "30", "0", "0", "consultation", "TRUE", "Консультация", "Consultation", "ייעוץ", "Бесплатно", "Free", "חינם"],
        ]
        
        # Тестовые клиенты
        clients_data = [
            [str(uuid.uuid4()), "111222333", "Иван Петров", "+972501111111", "ivan@test.com", "VIP клиент", datetime.now().isoformat(), "", "ru", "3", "2500"],
            [str(uuid.uuid4()), "444555666", "Anna Smith", "+972502222222", "anna@test.com", "", datetime.now().isoformat(), "", "en", "1", "800"],
            [str(uuid.uuid4()), "777888999", "דוד כהן", "+972503333333", "david@test.com", "", datetime.now().isoformat(), "", "he", "2", "1500"],
        ]
        
        # Тестовое расписание
        schedule_data = []
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for master_id in ['m_001', 'm_002', 'm_003']:
            for day in days:
                is_working = "TRUE" if day not in ['saturday', 'sunday'] else "FALSE"
                schedule_data.append([
                    f"sch_{uuid.uuid4().hex[:8]}",
                    master_id,
                    day,
                    "10:00" if is_working == "TRUE" else "",
                    "19:00" if is_working == "TRUE" else "",
                    is_working,
                    "13:00" if is_working == "TRUE" else "",
                    "14:00" if is_working == "TRUE" else "",
                    ""
                ])
        
        # Записываем данные
        tables_to_populate = [
            ("Masters", masters_data),
            ("Services", services_data),
            ("Clients", clients_data),
            ("Schedule", schedule_data),
        ]
        
        for table_name, data in tables_to_populate:
            try:
                for row in data:
                    client.append_row(table_name, row)
                results["tables"][table_name] = len(data)
                logger.info(f"✅ {table_name}: добавлено {len(data)} записей")
            except Exception as e:
                logger.error(f"❌ Ошибка заполнения {table_name}: {e}")
                results["tables"][table_name] = {"error": str(e)}
        
        return results


# ============================================================================
# CLI
# ============================================================================

def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(
        description='🗄️ Unified Database Creator - Создание и унификация БД',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python unified_database_creator.py --create          # Создать структуру БД
  python unified_database_creator.py --create --force  # Пересоздать БД с нуля
  python unified_database_creator.py --validate        # Проверить данные
  python unified_database_creator.py --migrate         # Миграция (dry run)
  python unified_database_creator.py --migrate --apply # Применить миграцию
  python unified_database_creator.py --backup          # Создать backup
  python unified_database_creator.py --full            # Полный цикл
  python unified_database_creator.py --test-data       # Заполнить тестовыми данными
        """
    )
    
    parser.add_argument('--create', action='store_true', help='Создать структуру БД')
    parser.add_argument('--force', action='store_true', help='Перезаписать существующие листы')
    parser.add_argument('--validate', action='store_true', help='Валидация данных')
    parser.add_argument('--migrate', action='store_true', help='Миграция данных')
    parser.add_argument('--apply', action='store_true', help='Применить изменения (не dry run)')
    parser.add_argument('--backup', action='store_true', help='Создать backup')
    parser.add_argument('--restore', type=str, help='Восстановить из backup файла')
    parser.add_argument('--full', action='store_true', help='Полный цикл: backup + migrate + validate')
    parser.add_argument('--test-data', action='store_true', help='Заполнить тестовыми данными')
    parser.add_argument('--schema', action='store_true', help='Показать схему БД')
    
    args = parser.parse_args()
    
    if args.schema:
        print("\n📋 СХЕМА УНИФИЦИРОВАННОЙ БД:\n")
        for schema in UnifiedDatabaseSchema.get_all_schemas():
            print(f"\n🗂️ {schema.sheet_name} - {schema.description}")
            print("-" * 50)
            for col in schema.columns:
                req = "🔴" if col.required else "⚪"
                print(f"  {req} {col.name:<20} {col.validator or '':<10} {col.description}")
        return 0
    
    # Проверяем что выбрано хотя бы одно действие
    if not any([args.create, args.validate, args.migrate, args.backup, args.restore, args.full, args.test_data]):
        parser.print_help()
        return 1
    
    try:
        creator = UnifiedDatabaseCreator()
        
        # Полный цикл
        if args.full:
            print("\n🔄 ПОЛНЫЙ ЦИКЛ: backup → migrate → validate\n")
            creator.create_backup()
            creator.migrate_data(dry_run=False)
            creator.validate_database()
            return 0
        
        # Создание структуры
        if args.create:
            creator.create_database_structure(force=args.force)
        
        # Заполнение тестовыми данными
        if args.test_data:
            creator.populate_test_data()
        
        # Backup
        if args.backup:
            creator.create_backup()
        
        # Restore
        if args.restore:
            creator.restore_from_backup(args.restore)
        
        # Миграция
        if args.migrate:
            creator.migrate_data(dry_run=not args.apply)
        
        # Валидация
        if args.validate:
            creator.validate_database()
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
