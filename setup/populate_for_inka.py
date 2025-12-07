#!/usr/bin/env python3
"""
Скрипт для заполнения БД правильными тестовыми данными
Учитывает все требования ИНКА
"""

import sys
import logging
import uuid
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.db.sheets_client import GoogleSheetsClient
from src.config.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def populate_test_data():
    """Заполнить БД тестовыми данными для ИНКА"""
    try:
        logger.info("=" * 70)
        logger.info("ЗАПОЛНЕНИЕ БД ТЕСТОВЫМИ ДАННЫМИ ДЛЯ ИНКА")
        logger.info("=" * 70)
        
        config = get_config()
        sheets_client = GoogleSheetsClient(
            credentials_file=config.google_credentials_json,
            spreadsheet_id=config.google_spreadsheet_id
        )
        
        # ========== МАСТЕРА ==========
        logger.info("\n📝 Добавляю мастеров...")
        
        masters_data = [
            [
                str(uuid.uuid4()),                    # id
                "Анна Леви",                          # name
                "Реалистичные татуировки",           # specialization
                "8",                                  # experience_years
                "4.8",                                # rating
                "+972-50-123-4567",                   # phone
                "@m_anna_levi",                       # instagram
                "250",                                # price_per_session
                "active",                             # status
                "Специалист по реалистичным татуировкам. Портреты, животные, детальные рисунки",  # bio
                "calendar_id_anna_levi",              # calendar_id (КРИТИЧНО!)
                "Реалистичные татуировки высочайшего качества"  # bio (доп)
            ],
            [
                str(uuid.uuid4()),
                "Платон Сосницкий",
                "Минимализм и авторские дизайны",
                "12",
                "4.9",
                "+972-50-987-6543",
                "@m_platon_sosnitsky",
                "250",
                "active",
                "Специалист по минимализму и авторским дизайнам. Линии, геометрия, оригинальные идеи",
                "calendar_id_platon_sosnitsky",
                "Минимализм и авторские дизайны"
            ],
            [
                str(uuid.uuid4()),
                "Мойше (Сара)",
                "Пирсинг",
                "10",
                "4.7",
                "+972-50-555-6666",
                "@m_sarah_moshe",
                "120",
                "active",
                "Сертифицированный мастер пирсинга APP. Микропирсинг, хрящ, сложные зоны",
                "calendar_id_sarah_moshe",
                "Пирсинг сертифицированный"
            ]
        ]
        
        for master_row in masters_data:
            sheets_client.append_row("Мастера", master_row)
            logger.info(f"  ✅ Добавлен мастер: {master_row[1]}")
        
        # Сохраняем UUID мастеров для использования в расписании
        masters_uuids = [m[0] for m in masters_data]
        
        # ========== РАСПИСАНИЕ ==========
        logger.info("\n📅 Добавляю расписание мастеров...")
        
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        working_hours = {
            "monday": ("10:00", "19:00"),
            "tuesday": ("10:00", "19:00"),
            "wednesday": ("10:00", "19:00"),
            "thursday": ("10:00", "19:00"),
            "friday": ("10:00", "19:00"),
            "saturday": ("12:00", "17:00"),
        }
        
        for master_id in masters_uuids:
            for day in days_of_week:
                if day in working_hours:
                    start_time, end_time = working_hours[day]
                    schedule_row = [
                        str(uuid.uuid4()),           # id
                        master_id,                   # master_id (КРИТИЧНО!)
                        day,                         # day_of_week (КРИТИЧНО!)
                        start_time,                  # start_time (КРИТИЧНО!)
                        end_time,                    # end_time (КРИТИЧНО!)
                        "true",                      # is_working (КРИТИЧНО!)
                        "",                          # break_start (опционально)
                        "",                          # break_end (опционально)
                        f"Обычный рабочий день ({day})"  # notes
                    ]
                    sheets_client.append_row("Расписание", schedule_row)
            logger.info(f"  ✅ Добавлено расписание для мастера {master_id[:8]}...")
        
        # ========== УСЛУГИ ==========
        logger.info("\n💼 Добавляю услуги...")
        
        services_data = [
            [
                str(uuid.uuid4()),
                "Надпись на иврите",
                "Простая надпись на иврите до 10 слов",
                "60",
                "250",
                "Татуировка",
                "active",
                ""
            ],
            [
                str(uuid.uuid4()),
                "Маленькая татуировка",
                "Маленькая татуировка до 5см (символ, иконка, минималистика)",
                "60",
                "400",
                "Татуировка",
                "active",
                ""
            ],
            [
                str(uuid.uuid4()),
                "Средняя татуировка",
                "Татуировка 5-15см (животное, портрет, цветная работа)",
                "120",
                "1000",
                "Татуировка",
                "active",
                ""
            ],
            [
                str(uuid.uuid4()),
                "Пирсинг уха",
                "Пирсинг уха (обычный или хрящ)",
                "30",
                "100",
                "Пирсинг",
                "active",
                ""
            ],
            [
                str(uuid.uuid4()),
                "Пирсинг носа",
                "Пирсинг носа",
                "30",
                "150",
                "Пирсинг",
                "active",
                ""
            ],
            [
                str(uuid.uuid4()),
                "Консультация",
                "Бесплатная консультация по дизайну и методу",
                "30",
                "0",
                "Консультация",
                "active",
                ""
            ]
        ]
        
        services_uuids = []
        for service_row in services_data:
            sheets_client.append_row("Услуги", service_row)
            services_uuids.append(service_row[0])
            logger.info(f"  ✅ Добавлена услуга: {service_row[1]}")
        
        # ========== КЛИЕНТЫ (тестовые) ==========
        logger.info("\n👥 Добавляю тестовых клиентов...")
        
        test_clients = [
            [
                str(uuid.uuid4()),
                "123456789",                         # telegram_id
                "Иван Петров",
                "+7-900-123-45-67",
                "ivan@example.com",
                "Первый клиент для тестирования",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ""
            ],
            [
                str(uuid.uuid4()),
                "987654321",
                "Мария Сидорова",
                "+7-900-987-65-43",
                "maria@example.com",
                "",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ""
            ]
        ]
        
        for client_row in test_clients:
            sheets_client.append_row("Клиенты", client_row)
            logger.info(f"  ✅ Добавлен клиент: {client_row[2]}")
        
        # ========== ПРАЙС-ЛИСТ ==========
        logger.info("\n💰 Добавляю прайс-лист...")
        
        pricing_data = []
        for master_idx, master_id in enumerate(masters_uuids):
            for service_idx, service_id in enumerate(services_uuids):
                pricing_row = [
                    str(uuid.uuid4()),
                    master_id,
                    service_id,
                    str(100 + (service_idx * 50)),   # price
                    "20",                             # commission_percent
                    str(80 + (service_idx * 40)),    # net_income
                    datetime.now().strftime("%Y-%m-%d"),
                    "true",
                    ""
                ]
                sheets_client.append_row("Прайс-лист", pricing_row)
        
        logger.info(f"  ✅ Добавлены цены ({len(masters_uuids)} x {len(services_uuids)} записей)")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ УСПЕШНО! БД заполнена тестовыми данными")
        logger.info("=" * 70)
        logger.info("\nСозданные данные:")
        logger.info(f"  📊 Мастеров: {len(masters_uuids)}")
        logger.info(f"  💼 Услуг: {len(services_uuids)}")
        logger.info(f"  📅 Записей расписания: {len(masters_uuids) * len(days_of_week)}")
        logger.info(f"  👥 Клиентов: {len(test_clients)}")
        logger.info(f"  💰 Прайс-лист записей: {len(masters_uuids) * len(services_uuids)}")
        logger.info("\nКритичные поля для ИНКА:")
        logger.info("  ✅ masters.calendar_id - добавлено")
        logger.info("  ✅ schedule.master_id - добавлено")
        logger.info("  ✅ schedule.day_of_week - добавлено")
        logger.info("  ✅ schedule.start_time/end_time - добавлено")
        logger.info("  ✅ schedule.is_working - добавлено")
        logger.info("  ✅ bookings.client_id - добавлено в структуру")
        logger.info("  ✅ bookings.master_id - добавлено в структуру")
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(populate_test_data())
