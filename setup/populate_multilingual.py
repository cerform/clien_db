#!/usr/bin/env python3
"""
Скрипт для заполнения БД тестовыми данными с поддержкой локализации
Используется для развертывания ИНКА с многоязычной поддержкой (RU, EN, HE)
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

def populate_multilingual_data():
    """Заполнить БД тестовыми многоязычными данными"""
    try:
        logger.info("=" * 70)
        logger.info("ЗАПОЛНЕНИЕ БД МНОГОЯЗЫЧНЫМИ ДАННЫМИ ДЛЯ ИНКА")
        logger.info("=" * 70)
        
        config = get_config()
        sheets_client = GoogleSheetsClient(
            credentials_file=config.google_credentials_json,
            spreadsheet_id=config.google_spreadsheet_id
        )
        
        # ========== МАСТЕРА ==========
        logger.info("\n📝 Добавляю мастеров с поддержкой многоязычия...")
        
        master1_id = str(uuid.uuid4())
        master2_id = str(uuid.uuid4())
        master3_id = str(uuid.uuid4())
        
        masters_data = [
            [
                master1_id,                           # id
                "Анна Леви",                          # name (English base)
                "Realistic Tattoos",                  # specialization (English)
                "8",                                  # experience_years
                "4.8",                                # rating
                "+972-50-123-4567",                   # phone
                "@m_anna_levi",                       # instagram
                "250",                                # price_per_session
                "active",                             # status
                "Специалист по портретам и природе",  # bio
                "calendar-anna-123@group.calendar.google.com",  # calendar_id
                "ru",                                 # language (default: Russian)
                "tattoo,realistic,portraits",         # tags
                # Локализационные данные
                "Анна Леви",                          # name_ru
                "Anna Levi",                          # name_en
                "אנה לוי",                             # name_he
                "Реалистичные татуировки",           # specialization_ru
                "Realistic Tattoos",                  # specialization_en
                "קעקועים אמיתיים",                   # specialization_he
                "Специалист по портретам и природе",  # bio_ru
                "Specialist in portraits and nature", # bio_en
                "מומחה בדיוקנאות וטבע"               # bio_he
            ],
            [
                master2_id,
                "Дэвид Коэн",
                "Minimalist Design",
                "5",
                "4.6",
                "+972-50-234-5678",
                "@david.cohen.ink",
                "200",
                "active",
                "Мастер минималистичного дизайна",
                "calendar-david-456@group.calendar.google.com",
                "ru",
                "tattoo,minimalism,geometric",
                # Локализационные данные
                "Дэвид Коэн",
                "David Cohen",
                "דוד כהן",
                "Минималистичный дизайн",
                "Minimalist Design",
                "עיצוב מינימליסטי",
                "Мастер минималистичного дизайна",
                "Master of minimalist design",
                "מכשיר של עיצוב מינימליסטי"
            ],
            [
                master3_id,
                "Софи Розенберг",
                "Piercing & Jewelry",
                "6",
                "4.9",
                "+972-50-345-6789",
                "@sophie.piercing",
                "150",
                "active",
                "Эксперт по пирсингу и украшениям",
                "calendar-sophie-789@group.calendar.google.com",
                "ru",
                "piercing,jewelry,ears",
                # Локализационные данные
                "Софи Розенберг",
                "Sophie Rosenberg",
                "סופי רוזנברג",
                "Пирсинг и украшения",
                "Piercing & Jewelry",
                "פירסינג וקישוטים",
                "Эксперт по пирсингу и украшениям",
                "Expert in piercing and jewelry",
                "מומחה בפירסינג וקישוטים"
            ]
        ]
        
        sheets_client.append_rows("Мастера", masters_data)
        logger.info(f"✅ Добавлено {len(masters_data)} мастеров")
        
        # ========== УСЛУГИ ==========
        logger.info("\n📝 Добавляю услуги с поддержкой многоязычия...")
        
        service1_id = str(uuid.uuid4())
        service2_id = str(uuid.uuid4())
        service3_id = str(uuid.uuid4())
        service4_id = str(uuid.uuid4())
        service5_id = str(uuid.uuid4())
        service6_id = str(uuid.uuid4())
        
        services_data = [
            [
                service1_id,
                "Portrait Tattoo",
                "Professional portrait tattoo",
                "120",
                "300",
                "tattoo",
                "active",
                "https://example.com/portraits.jpg",
                "ru",
                "tattoo,portrait,realistic",
                # Локализационные данные
                "Портретная татуировка",
                "Portrait Tattoo",
                "קעקוע דיוקנאות",
                "Профессиональная портретная татуировка",
                "Professional portrait tattoo",
                "קעקוע דיוקנאות מקצועי"
            ],
            [
                service2_id,
                "Minimalist Tattoo",
                "Simple geometric minimalist design",
                "60",
                "150",
                "tattoo",
                "active",
                "https://example.com/minimalist.jpg",
                "ru",
                "tattoo,minimalism",
                # Локализационные данные
                "Минималистичная татуировка",
                "Minimalist Tattoo",
                "קעקוע מינימליסטי",
                "Простой геометрический минималистичный дизайн",
                "Simple geometric minimalist design",
                "עיצוב מינימליסטי גיאומטרי פשוט"
            ],
            [
                service3_id,
                "Ear Piercing",
                "Professional ear piercing with sterilized equipment",
                "30",
                "50",
                "piercing",
                "active",
                "https://example.com/ear-piercing.jpg",
                "ru",
                "piercing,ears",
                # Локализационные данные
                "Прокалывание ушей",
                "Ear Piercing",
                "פירסינג אוזניים",
                "Профессиональное прокалывание ушей со стерилизованным оборудованием",
                "Professional ear piercing with sterilized equipment",
                "פירסינג אוזניים מקצועי עם ציוד סטריליזציה"
            ],
            [
                service4_id,
                "Nose Piercing",
                "Nostril and septum piercing",
                "30",
                "60",
                "piercing",
                "active",
                "https://example.com/nose-piercing.jpg",
                "ru",
                "piercing,nose",
                # Локализационные данные
                "Прокалывание носа",
                "Nose Piercing",
                "פירסינג אף",
                "Прокалывание крыльев носа и перегородки",
                "Nostril and septum piercing",
                "פירסינג חודי ובדיקה"
            ],
            [
                service5_id,
                "Consultation",
                "Free design consultation",
                "30",
                "0",
                "consultation",
                "active",
                "",
                "ru",
                "consultation,free",
                # Локализационные данные
                "Консультация",
                "Consultation",
                "ייעוץ",
                "Бесплатная консультация по дизайну",
                "Free design consultation",
                "ייעוץ עיצוב חינם"
            ],
            [
                service6_id,
                "Jewelry Selection",
                "Help choosing and fitting jewelry",
                "20",
                "30",
                "service",
                "active",
                "https://example.com/jewelry.jpg",
                "ru",
                "jewelry,piercing",
                # Локализационные данные
                "Подбор украшений",
                "Jewelry Selection",
                "בחירת תכשיטים",
                "Помощь в выборе и установке украшений",
                "Help choosing and fitting jewelry",
                "עזרה בבחירה והתאמה של תכשיטים"
            ]
        ]
        
        sheets_client.append_rows("Услуги", services_data)
        logger.info(f"✅ Добавлено {len(services_data)} услуг")
        
        # ========== РАСПИСАНИЕ ==========
        logger.info("\n📝 Добавляю расписание мастеров...")
        
        schedule_data = []
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        
        for master_id in [master1_id, master2_id, master3_id]:
            for day in days:
                is_working = "true" if day != "sunday" else "false"
                schedule_data.append([
                    str(uuid.uuid4()),      # id
                    master_id,              # master_id
                    day,                    # day_of_week
                    "09:00",                # start_time
                    "18:00",                # end_time
                    is_working,             # is_working
                    "13:00",                # break_start
                    "14:00",                # break_end
                    ""                      # notes
                ])
        
        sheets_client.append_rows("Расписание", schedule_data)
        logger.info(f"✅ Добавлено {len(schedule_data)} записей расписания")
        
        # ========== КЛИЕНТЫ ==========
        logger.info("\n📝 Добавляю тестовых клиентов...")
        
        client1_id = str(uuid.uuid4())
        client2_id = str(uuid.uuid4())
        
        clients_data = [
            [
                client1_id,
                "123456789",             # telegram_id (example)
                "Мой Браун",             # name
                "+972-55-111-2222",      # phone
                "may.braun@email.com",   # email
                "Интересуется реалистичными татуировками",  # notes
                datetime.now().isoformat(),  # created_at
                "",                      # last_visit
                "Russian",               # preferred_language
                "ru"                     # language_code
            ],
            [
                client2_id,
                "987654321",
                "Yossi Bar",
                "+972-50-333-4444",
                "yossi@email.com",
                "Looking for minimalist design",
                datetime.now().isoformat(),
                "",
                "English",
                "en"
            ]
        ]
        
        sheets_client.append_rows("Клиенты", clients_data)
        logger.info(f"✅ Добавлено {len(clients_data)} клиентов")
        
        # ========== ПРАЙС-ЛИСТ ==========
        logger.info("\n📝 Добавляю прайс-лист...")
        
        pricing_data = []
        # Мастер1 - Портретная татуировка
        pricing_data.append([
            str(uuid.uuid4()),
            master1_id,
            service1_id,
            "300",
            "20",
            "240",
            datetime.now().isoformat(),
            "true",
            ""
        ])
        # Мастер2 - Минималистичная татуировка
        pricing_data.append([
            str(uuid.uuid4()),
            master2_id,
            service2_id,
            "150",
            "20",
            "120",
            datetime.now().isoformat(),
            "true",
            ""
        ])
        # Мастер3 - Пирсинг ушей
        pricing_data.append([
            str(uuid.uuid4()),
            master3_id,
            service3_id,
            "50",
            "10",
            "45",
            datetime.now().isoformat(),
            "true",
            ""
        ])
        # Мастер3 - Пирсинг носа
        pricing_data.append([
            str(uuid.uuid4()),
            master3_id,
            service4_id,
            "60",
            "10",
            "54",
            datetime.now().isoformat(),
            "true",
            ""
        ])
        
        sheets_client.append_rows("Прайс-лист", pricing_data)
        logger.info(f"✅ Добавлено {len(pricing_data)} прайс-записей")
        
        # ========== РЕЗЮМЕ ==========
        logger.info("\n" + "=" * 70)
        logger.info("✅ УСПЕШНО! БД заполнена многоязычными данными")
        logger.info("=" * 70)
        logger.info("\n📊 Статистика:")
        logger.info(f"   🎨 Мастеров: {len(masters_data)}")
        logger.info(f"   💼 Услуг: {len(services_data)}")
        logger.info(f"   📅 Записей расписания: {len(schedule_data)}")
        logger.info(f"   👥 Клиентов: {len(clients_data)}")
        logger.info(f"   💰 Прайс-записей: {len(pricing_data)}")
        logger.info("\n🌍 Поддерживаемые языки:")
        logger.info("   🇷🇺 Русский (ru)")
        logger.info("   🇬🇧 Английский (en)")
        logger.info("   🇮🇱 Иврит (he)")
        logger.info("\n💾 Все данные содержат локализованные версии названий и описаний")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при заполнении БД: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = populate_multilingual_data()
    sys.exit(0 if success else 1)
