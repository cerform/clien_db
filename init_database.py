#!/usr/bin/env python3
"""
Скрипт для инициализации полноценной БД в Google Sheets
Создает всю необходимую структуру таблиц с заголовками и форматированием
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.db_initializer import DatabaseInitializer
from src.config.config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Главная функция инициализации"""
    try:
        logger.info("=" * 60)
        logger.info("ИНИЦИАЛИЗАЦИЯ ПОЛНОЦЕННОЙ БД")
        logger.info("=" * 60)
        
        # Получить конфиг
        config = get_config()
        logger.info(f"Using spreadsheet ID: {config.google_spreadsheet_id}")
        logger.info(f"Using credentials from: {config.google_credentials_json}")
        
        # Инициализировать БД
        db_init = DatabaseInitializer(
            credentials_file=config.google_credentials_json,
            spreadsheet_id=config.google_spreadsheet_id
        )
        
        logger.info("\nНачинаю создание структуры БД...")
        if db_init.initialize_database():
            logger.info("\n✅ УСПЕШНО! База данных инициализирована")
            logger.info("\nСозданные листы:")
            logger.info("  1. Мастера - информация о мастерах")
            logger.info("  2. Клиенты - список клиентов")
            logger.info("  3. Записи - записи на услуги")
            logger.info("  4. Услуги - каталог услуг")
            logger.info("  5. Расписание - график работы мастеров")
            logger.info("  6. Отзывы - отзывы клиентов")
            logger.info("  7. Прайс-лист - цены на услуги")
            logger.info("\n" + "=" * 60)
            return 0
        else:
            logger.error("❌ Инициализация БД не удалась")
            return 1
    
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
