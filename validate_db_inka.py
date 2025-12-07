#!/usr/bin/env python3
"""
Проверка совместимости БД со всеми сервисами и ИНКА
Валидирует наличие всех критичных полей
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from src.db.sheets_client import GoogleSheetsClient
from src.config.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseValidator:
    """Валидатор структуры БД для ИНКА"""
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets_client = sheets_client
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.success_count = 0
    
    def validate_all(self) -> bool:
        """Проверить все таблицы"""
        logger.info("=" * 70)
        logger.info("ПРОВЕРКА СОВМЕСТИМОСТИ БД С ИНКА")
        logger.info("=" * 70)
        
        # Проверки по таблицам
        self._validate_masters_table()
        self._validate_clients_table()
        self._validate_bookings_table()
        self._validate_services_table()
        self._validate_schedule_table()
        self._validate_reviews_table()
        self._validate_pricing_table()
        
        # Отчёт
        self._print_report()
        
        return len(self.errors) == 0
    
    def _validate_masters_table(self):
        """Проверить таблицу Мастера"""
        logger.info("\n👥 Проверяю таблицу 'Мастера'...")
        
        required_fields = ["id", "name", "specialization", "calendar_id", "bio"]
        
        data = self.sheets_client.get_all_rows("Мастера")
        if not data:
            self.errors.append("❌ Таблица 'Мастера' пуста или не существует")
            return
        
        headers = data[0] if data else []
        logger.debug(f"   Найденные колонки: {headers}")
        
        missing_fields = []
        for field in required_fields:
            if field not in headers:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append(f"❌ Таблица 'Мастера': отсутствуют поля {missing_fields}")
        else:
            self.success_count += 1
            logger.info(f"   ✅ Все критичные поля присутствуют")
        
        # Проверить данные
        if len(data) > 1:
            for row_idx, row in enumerate(data[1:3], 1):  # Проверить первые 2 записи
                if len(row) > headers.index("calendar_id"):
                    calendar_id = row[headers.index("calendar_id")]
                    if not calendar_id or calendar_id.strip() == "":
                        self.warnings.append(f"⚠️  Мастер (строка {row_idx+1}): calendar_id не заполнен")
    
    def _validate_clients_table(self):
        """Проверить таблицу Клиенты"""
        logger.info("\n👤 Проверяю таблицу 'Клиенты'...")
        
        required_fields = ["id", "telegram_id", "name"]
        
        data = self.sheets_client.get_all_rows("Клиенты")
        if not data:
            self.errors.append("❌ Таблица 'Клиенты' пуста или не существует")
            return
        
        headers = data[0] if data else []
        logger.debug(f"   Найденные колонки: {headers}")
        
        missing_fields = []
        for field in required_fields:
            if field not in headers:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append(f"❌ Таблица 'Клиенты': отсутствуют поля {missing_fields}")
        else:
            self.success_count += 1
            logger.info(f"   ✅ Все критичные поля присутствуют")
    
    def _validate_bookings_table(self):
        """Проверить таблицу Записи"""
        logger.info("\n📝 Проверяю таблицу 'Записи'...")
        
        required_fields = ["id", "client_id", "master_id", "service_id", "date", "time", "status"]
        
        data = self.sheets_client.get_all_rows("Записи")
        if not data:
            self.warnings.append("⚠️  Таблица 'Записи' пуста (это нормально для новой БД)")
            return
        
        headers = data[0] if data else []
        logger.debug(f"   Найденные колонки: {headers}")
        
        missing_fields = []
        for field in required_fields:
            if field not in headers:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append(f"❌ Таблица 'Записи': отсутствуют поля {missing_fields}")
        else:
            self.success_count += 1
            logger.info(f"   ✅ Все критичные поля присутствуют")
    
    def _validate_services_table(self):
        """Проверить таблицу Услуги"""
        logger.info("\n💼 Проверяю таблицу 'Услуги'...")
        
        required_fields = ["id", "name", "duration_min"]
        
        data = self.sheets_client.get_all_rows("Услуги")
        if not data:
            self.errors.append("❌ Таблица 'Услуги' пуста или не существует")
            return
        
        headers = data[0] if data else []
        logger.debug(f"   Найденные колонки: {headers}")
        
        missing_fields = []
        for field in required_fields:
            if field not in headers:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append(f"❌ Таблица 'Услуги': отсутствуют поля {missing_fields}")
        else:
            self.success_count += 1
            logger.info(f"   ✅ Все критичные поля присутствуют")
    
    def _validate_schedule_table(self):
        """Проверить таблицу Расписание - КРИТИЧНАЯ ПРОВЕРКА"""
        logger.info("\n📅 Проверяю таблицу 'Расписание'...")
        
        required_fields = ["id", "master_id", "day_of_week", "start_time", "end_time", "is_working"]
        
        data = self.sheets_client.get_all_rows("Расписание")
        if not data:
            self.warnings.append("⚠️  Таблица 'Расписание' пуста (нужно заполнить для работы ИНКА)")
            return
        
        headers = data[0] if data else []
        logger.debug(f"   Найденные колонки: {headers}")
        
        missing_fields = []
        for field in required_fields:
            if field not in headers:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append(f"❌ Таблица 'Расписание': отсутствуют КРИТИЧНЫЕ поля {missing_fields}")
            logger.error("   ИНКА НЕ БУДЕТ РАБОТАТЬ БЕЗ ЭТИХ ПОЛЕЙ!")
        else:
            self.success_count += 1
            logger.info(f"   ✅ Все критичные поля присутствуют")
        
        # Проверить формат данных
        if len(data) > 1 and "day_of_week" in headers:
            valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for row_idx, row in enumerate(data[1:3], 1):
                if len(row) > headers.index("day_of_week"):
                    day = row[headers.index("day_of_week")]
                    if day and day not in valid_days:
                        self.warnings.append(f"⚠️  Расписание (строка {row_idx+1}): неправильное значение day_of_week='{day}'")
    
    def _validate_reviews_table(self):
        """Проверить таблицу Отзывы"""
        logger.info("\n⭐ Проверяю таблицу 'Отзывы'...")
        
        required_fields = ["id", "client_id", "master_id", "rating"]
        
        data = self.sheets_client.get_all_rows("Отзывы")
        if not data:
            self.warnings.append("⚠️  Таблица 'Отзывы' пуста (это нормально для новой БД)")
            return
        
        headers = data[0] if data else []
        logger.debug(f"   Найденные колонки: {headers}")
        
        missing_fields = []
        for field in required_fields:
            if field not in headers:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append(f"❌ Таблица 'Отзывы': отсутствуют поля {missing_fields}")
        else:
            self.success_count += 1
            logger.info(f"   ✅ Все критичные поля присутствуют")
    
    def _validate_pricing_table(self):
        """Проверить таблицу Прайс-лист"""
        logger.info("\n💰 Проверяю таблицу 'Прайс-лист'...")
        
        required_fields = ["id", "master_id", "service_id", "price"]
        
        data = self.sheets_client.get_all_rows("Прайс-лист")
        if not data:
            self.warnings.append("⚠️  Таблица 'Прайс-лист' пуста (это нормально для новой БД)")
            return
        
        headers = data[0] if data else []
        logger.debug(f"   Найденные колонки: {headers}")
        
        missing_fields = []
        for field in required_fields:
            if field not in headers:
                missing_fields.append(field)
        
        if missing_fields:
            self.errors.append(f"❌ Таблица 'Прайс-лист': отсутствуют поля {missing_fields}")
        else:
            self.success_count += 1
            logger.info(f"   ✅ Все критичные поля присутствуют")
    
    def _print_report(self):
        """Вывести отчёт"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 ОТЧЁТ О СОВМЕСТИМОСТИ")
        logger.info("=" * 70)
        
        if self.errors:
            logger.error("\n❌ ОШИБКИ (ИНКА НЕ БУДЕТ РАБОТАТЬ):")
            for error in self.errors:
                logger.error(f"   {error}")
        else:
            logger.info("\n✅ ОШИБОК НЕ НАЙДЕНО")
        
        if self.warnings:
            logger.warning("\n⚠️  ПРЕДУПРЕЖДЕНИЯ:")
            for warning in self.warnings:
                logger.warning(f"   {warning}")
        else:
            logger.info("\n✅ ПРЕДУПРЕЖДЕНИЙ НЕ НАЙДЕНО")
        
        logger.info(f"\n✅ Успешных проверок: {self.success_count}/7")
        
        logger.info("\n" + "=" * 70)
        if not self.errors:
            logger.info("✅ БД ПОЛНОСТЬЮ СОВМЕСТИМА С ИНКА! 🎉")
        else:
            logger.error("❌ БД НЕ СОВМЕСТИМА! ТРЕБУЮТСЯ ИЗМЕНЕНИЯ!")
        logger.info("=" * 70)

def main():
    try:
        config = get_config()
        sheets_client = GoogleSheetsClient(
            credentials_file=config.google_credentials_json,
            spreadsheet_id=config.google_spreadsheet_id
        )
        
        validator = DatabaseValidator(sheets_client)
        is_valid = validator.validate_all()
        
        return 0 if is_valid else 1
    
    except Exception as e:
        logger.error(f"❌ Ошибка валидации: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
