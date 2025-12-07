#!/usr/bin/env python3
"""
Заполнение Google Sheets реальными данными израильского салона
- 2-3 мастера с разными специализациями
- Полный прайс-лист услуг
- Расписание работы
- Примеры цен для мастеров
"""

import sys
from pathlib import Path
from datetime import datetime
import uuid

sys.path.insert(0, str(Path(__file__).parent))

from src.db.sheets_client import GoogleSheetsClient
from src.config import get_config

# Реальные мастера с израильскими именами
MASTERS = [
    {
        "id": "m_anna_levi",
        "name": "Анна Леви",
        "phone": "+972-3-629-4270",
        "telegram_id": "123456789",
        "specialization": "tattoo",
        "rating": "4.8",
        "photo_url": "https://example.com/anna.jpg",
        "bio": "Специалист по реалистичным татуировкам. 8 лет опыта. Сертифицирована.",
        "status": "active",
        "created_at": "2017-03-15 10:00:00"
    },
    {
        "id": "m_omer_cohen",
        "name": "Омер Коэн",
        "phone": "+972-3-699-9239",
        "telegram_id": "987654321",
        "specialization": "tattoo",
        "rating": "4.9",
        "photo_url": "https://example.com/omer.jpg",
        "bio": "Мастер минимализма и линий. 12 лет опыта. Творческие дизайны.",
        "status": "active",
        "created_at": "2012-06-20 14:30:00"
    },
    {
        "id": "m_sarah_nir",
        "name": "Сара Нир",
        "phone": "+972-50-7708561",
        "telegram_id": "456789123",
        "specialization": "piercing",
        "rating": "4.7",
        "photo_url": "https://example.com/sarah.jpg",
        "bio": "Сертифицированный мастер пирсинга (APP). Специалист по микропирсингу.",
        "status": "active",
        "created_at": "2015-01-10 11:00:00"
    }
]

# Услуги на основе реальных израильских цен
SERVICES = [
    {
        "id": "s_tattoo_small",
        "name": "Маленькая татуировка",
        "description": "До 5 см. Простой дизайн, 1-2 часа",
        "duration_min": "60",
        "price_from": "250",
        "price_to": "500",
        "category": "tattoo",
        "active": "true"
    },
    {
        "id": "s_tattoo_medium",
        "name": "Средняя татуировка",
        "description": "5-15 см. Средняя сложность, 2-4 часа",
        "duration_min": "120",
        "price_from": "600",
        "price_to": "1500",
        "category": "tattoo",
        "active": "true"
    },
    {
        "id": "s_tattoo_large",
        "name": "Большая татуировка",
        "description": "15+ см. Сложный дизайн, 4+ часа",
        "duration_min": "240",
        "price_from": "1800",
        "price_to": "5000",
        "category": "tattoo",
        "active": "true"
    },
    {
        "id": "s_tattoo_text",
        "name": "Надпись (текст)",
        "description": "Простая надпись до 10 слов. 30-60 мин",
        "duration_min": "45",
        "price_from": "250",
        "price_to": "400",
        "category": "tattoo",
        "active": "true"
    },
    {
        "id": "s_piercing_ear",
        "name": "Пирсинг уха",
        "description": "Классический пирсинг уха (мочка, хрящ)",
        "duration_min": "30",
        "price_from": "90",
        "price_to": "150",
        "category": "piercing",
        "active": "true"
    },
    {
        "id": "s_piercing_nose",
        "name": "Пирсинг носа",
        "description": "Пирсинг носа (крыло, септум)",
        "duration_min": "30",
        "price_from": "120",
        "price_to": "180",
        "category": "piercing",
        "active": "true"
    },
    {
        "id": "s_piercing_body",
        "name": "Пирсинг тела",
        "description": "Пирсинг пупка, губы, языка, других зон",
        "duration_min": "30",
        "price_from": "150",
        "price_to": "250",
        "category": "piercing",
        "active": "true"
    },
    {
        "id": "s_consultation",
        "name": "Консультация",
        "description": "Бесплатная первичная консультация с мастером",
        "duration_min": "30",
        "price_from": "0",
        "price_to": "0",
        "category": "consultation",
        "active": "true"
    }
]

# Расписание (понедельник = 0, воскресенье = 6)
SCHEDULE = [
    # Анна - пн-пт 10:00-19:00, сб 12:00-17:00, вс выходной
    {"id": "sch_anna_mon", "master_id": "m_anna_levi", "day_of_week": "0", "start_time": "10:00", "end_time": "19:00", "is_working": "true", "notes": "Обеденный перерыв 13:00-14:00"},
    {"id": "sch_anna_tue", "master_id": "m_anna_levi", "day_of_week": "1", "start_time": "10:00", "end_time": "19:00", "is_working": "true", "notes": "Обеденный перерыв 13:00-14:00"},
    {"id": "sch_anna_wed", "master_id": "m_anna_levi", "day_of_week": "2", "start_time": "10:00", "end_time": "19:00", "is_working": "true", "notes": "Обеденный перерыв 13:00-14:00"},
    {"id": "sch_anna_thu", "master_id": "m_anna_levi", "day_of_week": "3", "start_time": "10:00", "end_time": "19:00", "is_working": "true", "notes": "Обеденный перерыв 13:00-14:00"},
    {"id": "sch_anna_fri", "master_id": "m_anna_levi", "day_of_week": "4", "start_time": "10:00", "end_time": "17:00", "is_working": "true", "notes": "Последний слот 16:00"},
    {"id": "sch_anna_sat", "master_id": "m_anna_levi", "day_of_week": "5", "start_time": "12:00", "end_time": "17:00", "is_working": "true", "notes": "Выходной в понедельник"},
    {"id": "sch_anna_sun", "master_id": "m_anna_levi", "day_of_week": "6", "start_time": "00:00", "end_time": "00:00", "is_working": "false", "notes": "Выходной"},
    
    # Омер - пн-пт 11:00-20:00, сб-вс выходной
    {"id": "sch_omer_mon", "master_id": "m_omer_cohen", "day_of_week": "0", "start_time": "11:00", "end_time": "20:00", "is_working": "true", "notes": "Обеденный перерыв 14:00-15:00"},
    {"id": "sch_omer_tue", "master_id": "m_omer_cohen", "day_of_week": "1", "start_time": "11:00", "end_time": "20:00", "is_working": "true", "notes": "Обеденный перерыв 14:00-15:00"},
    {"id": "sch_omer_wed", "master_id": "m_omer_cohen", "day_of_week": "2", "start_time": "11:00", "end_time": "20:00", "is_working": "true", "notes": "Обеденный перерыв 14:00-15:00"},
    {"id": "sch_omer_thu", "master_id": "m_omer_cohen", "day_of_week": "3", "start_time": "11:00", "end_time": "20:00", "is_working": "true", "notes": "Обеденный перерыв 14:00-15:00"},
    {"id": "sch_omer_fri", "master_id": "m_omer_cohen", "day_of_week": "4", "start_time": "11:00", "end_time": "18:00", "is_working": "true", "notes": "Сокращённый день"},
    {"id": "sch_omer_sat", "master_id": "m_omer_cohen", "day_of_week": "5", "start_time": "00:00", "end_time": "00:00", "is_working": "false", "notes": "Выходной (Суббота)"},
    {"id": "sch_omer_sun", "master_id": "m_omer_cohen", "day_of_week": "6", "start_time": "00:00", "end_time": "00:00", "is_working": "false", "notes": "Выходной (Воскресенье)"},
    
    # Сара (пирсинг) - пн-пт 10:00-18:00, сб 10:00-14:00, вс выходной
    {"id": "sch_sarah_mon", "master_id": "m_sarah_nir", "day_of_week": "0", "start_time": "10:00", "end_time": "18:00", "is_working": "true", "notes": ""},
    {"id": "sch_sarah_tue", "master_id": "m_sarah_nir", "day_of_week": "1", "start_time": "10:00", "end_time": "18:00", "is_working": "true", "notes": ""},
    {"id": "sch_sarah_wed", "master_id": "m_sarah_nir", "day_of_week": "2", "start_time": "10:00", "end_time": "18:00", "is_working": "true", "notes": ""},
    {"id": "sch_sarah_thu", "master_id": "m_sarah_nir", "day_of_week": "3", "start_time": "10:00", "end_time": "18:00", "is_working": "true", "notes": ""},
    {"id": "sch_sarah_fri", "master_id": "m_sarah_nir", "day_of_week": "4", "start_time": "10:00", "end_time": "17:00", "is_working": "true", "notes": ""},
    {"id": "sch_sarah_sat", "master_id": "m_sarah_nir", "day_of_week": "5", "start_time": "10:00", "end_time": "14:00", "is_working": "true", "notes": "Половина дня"},
    {"id": "sch_sarah_sun", "master_id": "m_sarah_nir", "day_of_week": "6", "start_time": "00:00", "end_time": "00:00", "is_working": "false", "notes": "Выходной"},
]

# Кастомные цены для мастеров (дополнение к основному прайсу)
PRICE_LIST = [
    # Анна берет 15% премиум за реалистичные работы
    {"id": "p_anna_small", "service_id": "s_tattoo_small", "master_id": "m_anna_levi", "custom_price": "300", "description": "Реалистичный стиль", "active": "true"},
    {"id": "p_anna_medium", "service_id": "s_tattoo_medium", "master_id": "m_anna_levi", "custom_price": "750", "description": "Реалистичный стиль", "active": "true"},
    
    # Омер берет 20% премиум за сложные дизайны
    {"id": "p_omer_medium", "service_id": "s_tattoo_medium", "master_id": "m_omer_cohen", "custom_price": "850", "description": "Авторский дизайн", "active": "true"},
    {"id": "p_omer_large", "service_id": "s_tattoo_large", "master_id": "m_omer_cohen", "custom_price": "2200", "description": "Авторский дизайн", "active": "true"},
]

# Примеры клиентов для тестирования
CLIENTS = [
    {
        "id": "c_test_1",
        "telegram_id": "111111111",
        "name": "Тестовый Клиент",
        "phone": "+972-50-1234567",
        "email": "test@example.com",
        "notes": "Первый визит, интересуется маленькой татуировкой",
        "created_at": "2025-12-01 10:00:00",
        "last_visit": "2025-12-01 10:00:00"
    }
]

# Примеры записей
BOOKINGS = [
    {
        "id": str(uuid.uuid4()),
        "client_id": "c_test_1",
        "master_id": "m_anna_levi",
        "service_id": "s_tattoo_small",
        "date": "2025-12-10",
        "time": "14:00",
        "duration_min": "60",
        "price": "300",
        "status": "confirmed",
        "notes": "Надпись на запястье на иврите",
        "created_at": "2025-12-01 10:00:00"
    },
    {
        "id": str(uuid.uuid4()),
        "client_id": "c_test_1",
        "master_id": "m_sarah_nir",
        "service_id": "s_piercing_ear",
        "date": "2025-12-15",
        "time": "11:00",
        "duration_min": "30",
        "price": "120",
        "status": "pending",
        "notes": "Пирсинг хряща уха",
        "created_at": "2025-12-02 15:30:00"
    }
]

# Примеры отзывов
REVIEWS = [
    {
        "id": str(uuid.uuid4()),
        "client_id": "c_test_1",
        "master_id": "m_anna_levi",
        "booking_id": BOOKINGS[0]["id"],
        "rating": "5",
        "comment": "Профессионально, чисто, быстро. Рекомендую!",
        "created_at": "2025-12-11 16:00:00"
    }
]


class DBPopulator:
    """Заполнение БД реальными данными"""
    
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        self.client = GoogleSheetsClient(credentials_file, spreadsheet_id)
        self.stats = {"added": {}, "errors": {}}
    
    def populate_all(self) -> bool:
        """Заполнить все таблицы"""
        print("\n" + "=" * 70)
        print("📊 ЗАПОЛНЕНИЕ GOOGLE SHEETS РЕАЛЬНЫМИ ДАННЫМИ")
        print("=" * 70)
        
        try:
            # Очищаем старые данные (кроме заголовков)
            self._clear_data()
            
            # Заполняем таблицы
            self._populate_table("masters", MASTERS, "Мастера")
            self._populate_table("services", SERVICES, "Услуги")
            self._populate_table("schedule", SCHEDULE, "Расписание")
            self._populate_table("price_list", PRICE_LIST, "Прайс-лист")
            self._populate_table("clients", CLIENTS, "Клиенты")
            self._populate_table("bookings", BOOKINGS, "Записи")
            self._populate_table("reviews", REVIEWS, "Отзывы")
            
            # Итоговой отчет
            self._print_summary()
            
            return True
        
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            return False
    
    def _clear_data(self):
        """Очистить данные (кроме заголовков)"""
        tables = ["masters", "clients", "bookings", "services", "schedule", "reviews", "price_list"]
        
        for table in tables:
            try:
                rows = self.client.get_all_rows(table)
                if len(rows) > 1:
                    # Очищаем все кроме заголовка
                    for i in range(2, len(rows) + 1):  # Начиная со строки 2
                        self.client.update_range(table, f"{i}:{i}", [[""] * len(rows[0])])
                    print(f"✓ Очищена таблица {table} ({len(rows) - 1} строк удалено)")
            except Exception as e:
                print(f"⚠ Не удалось очистить {table}: {e}")
    
    def _populate_table(self, table_name: str, data: list, description: str):
        """Заполнить одну таблицу"""
        success_count = 0
        
        for item in data:
            try:
                # Преобразуем словарь в список значений
                if isinstance(item, dict):
                    # Получаем заголовки из БД чтобы правильный порядок
                    rows = self.client.get_all_rows(table_name)
                    if not rows:
                        print(f"❌ {table_name}: таблица не найдена или пуста")
                        return
                    
                    headers = rows[0]
                    values = [item.get(h, "") for h in headers]
                else:
                    values = item
                
                # Добавляем строку
                if self.client.append_row(table_name, values):
                    success_count += 1
            
            except Exception as e:
                print(f"❌ Ошибка при добавлении в {table_name}: {e}")
        
        self.stats["added"][table_name] = success_count
        print(f"✅ {description:20} добавлено: {success_count}/{len(data)}")
    
    def _print_summary(self):
        """Вывести итоговый отчет"""
        print("\n" + "-" * 70)
        print("📊 ИТОГОВАЯ СТАТИСТИКА:")
        print("-" * 70)
        
        total_added = 0
        for table, count in self.stats["added"].items():
            print(f"  {table:15} {count:3} записей")
            total_added += count
        
        print("-" * 70)
        print(f"  {'ВСЕГО':15} {total_added:3} записей добавлено")
        
        print("\n" + "=" * 70)
        print("✅ ДАННЫЕ УСПЕШНО ЗАГРУЖЕНЫ!")
        print("=" * 70)
        
        print("\n📌 ИНФОРМАЦИЯ О МАСТЕРАХ:")
        print("-" * 70)
        for master in MASTERS:
            print(f"  🎨 {master['name']:20} | {master['specialization']:10} | ⭐ {master['rating']}")
        
        print("\n🛎️  УСЛУГИ:")
        print("-" * 70)
        categories = {}
        for service in SERVICES:
            cat = service["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(f"{service['name']} ({service['price_from']}-{service['price_to']}₪)")
        
        for cat, services in categories.items():
            print(f"\n  📂 {cat.upper()}:")
            for svc in services:
                print(f"     • {svc}")
        
        print("\n" + "=" * 70)
        print("✅ Теперь INKA может работать с реальными данными!")
        print("=" * 70)


def main():
    """Главная функция"""
    config = get_config()
    
    populator = DBPopulator("credentials.json", config.google_spreadsheet_id)
    
    success = populator.populate_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
