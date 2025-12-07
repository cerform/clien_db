#!/usr/bin/env python3
"""
Скрипт для заполнения БД примерами данных
Добавляет мастеров, клиентов, услуги и прочие данные для демонстрации
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.sheets_client import GoogleSheetsClient
from src.config.config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Примеры данных для мастеров (в формате строк для Google Sheets)
SAMPLE_MASTERS = [
    ['1', 'Алексей Волков', 'Тату - Портреты', '8', '4.9', '+7-999-123-45-67', '@alexey_tattoo', '3500', 'active', 'Специалист по реалистичным портретам'],
    ['2', 'Мария Петрова', 'Тату - Минимализм', '5', '4.8', '+7-999-234-56-78', '@maria_minimal_tattoo', '2500', 'active', 'Мастер минималистичных тату'],
    ['3', 'Иван Сидоров', 'Тату - Цветная классика', '10', '5.0', '+7-999-345-67-89', '@ivan_classic_color', '4000', 'active', 'Специалист по цветным тату'],
    ['4', 'Елена Морозова', 'Тату - Орнаменты', '6', '4.7', '+7-999-456-78-90', '@elena_ornament', '3000', 'active', 'Специалист по ornament-работам']
]

# Примеры услуг
SAMPLE_SERVICES = [
    ['1', 'Портретное тату', 'Реалистичный портрет человека', '120', '3500', 'Портреты', 'active', ''],
    ['2', 'Минималистичное тату', 'Простой и стильный дизайн', '60', '2500', 'Минимализм', 'active', ''],
    ['3', 'Цветное классическое тату', 'Яркое классическое тату', '90', '4000', 'Классика', 'active', ''],
    ['4', 'Орнамент/Мандала', 'Сложный узор или мандала', '150', '3000', 'Орнаменты', 'active', ''],
    ['5', 'Маленькое черно-белое тату', 'Небольшое тату размером 5х5см', '30', '1500', 'Маленькие', 'active', ''],
    ['6', 'Консультация дизайна', 'Обсуждение эскиза и деталей', '30', '500', 'Услуги', 'active', ''],
]

# Примеры клиентов
SAMPLE_CLIENTS = [
    ['1001', '123456789', 'Петр Иванов', '+7-900-111-22-33', 'petr@example.com', '01.12.2025', 'active', '3', '8500', ''],
    ['1002', '987654321', 'Ольга Сергеева', '+7-900-222-33-44', 'olga@example.com', '28.11.2025', 'active', '1', '3500', ''],
    ['1003', '555666777', 'Дмитрий Козлов', '+7-900-333-44-55', 'dmitry@example.com', '25.11.2025', 'active', '2', '5000', ''],
]

def populate_masters(sheets_client: GoogleSheetsClient) -> bool:
    """Добавить мастеров"""
    try:
        logger.info("Adding sample masters...")
        
        for master_row in SAMPLE_MASTERS:
            success = sheets_client.append_row("Мастера", master_row)
            if success:
                logger.info(f"✓ Added master: {master_row[1]}")
            else:
                logger.warning(f"Failed to add master: {master_row[1]}")
        
        return True
    except Exception as e:
        logger.error(f"Error populating masters: {e}")
        return False

def populate_services(sheets_client: GoogleSheetsClient) -> bool:
    """Добавить услуги"""
    try:
        logger.info("Adding sample services...")
        
        for service_row in SAMPLE_SERVICES:
            success = sheets_client.append_row("Услуги", service_row)
            if success:
                logger.info(f"✓ Added service: {service_row[1]}")
            else:
                logger.warning(f"Failed to add service: {service_row[1]}")
        
        return True
    except Exception as e:
        logger.error(f"Error populating services: {e}")
        return False

def populate_clients(sheets_client: GoogleSheetsClient) -> bool:
    """Добавить клиентов"""
    try:
        logger.info("Adding sample clients...")
        
        for client_row in SAMPLE_CLIENTS:
            success = sheets_client.append_row("Клиенты", client_row)
            if success:
                logger.info(f"✓ Added client: {client_row[2]}")
            else:
                logger.warning(f"Failed to add client: {client_row[2]}")
        
        return True
    except Exception as e:
        logger.error(f"Error populating clients: {e}")
        return False

def main():
    """Главная функция заполнения БД"""
    try:
        logger.info("=" * 60)
        logger.info("ЗАПОЛНЕНИЕ БД ПРИМЕРАМИ ДАННЫХ")
        logger.info("=" * 60)
        
        # Получить конфиг и создать клиент
        config = get_config()
        sheets_client = GoogleSheetsClient(
            credentials_file=config.google_credentials_json,
            spreadsheet_id=config.google_spreadsheet_id
        )
        
        logger.info("\nПодполнение БД примерами данных...\n")
        
        populate_masters(sheets_client)
        logger.info("")
        populate_services(sheets_client)
        logger.info("")
        populate_clients(sheets_client)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ УСПЕШНО! БД заполнена примерами данных")
        logger.info("=" * 60)
        return 0
    
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
