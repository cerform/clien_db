"""
Примеры использования бота и его компонентов
"""

from src.db.sheets_client import GoogleSheetsClient
from src.services.client_service import ClientService
from src.services.master_service import MasterService
from src.services.booking_service import BookingService
from src.config import get_config

# ============================================
# ПРИМЕР 1: Инициализация сервисов
# ============================================

def example_init_services():
    """Инициализация сервисов"""
    config = get_config()
    
    # Создаем Google Sheets клиент
    sheets = GoogleSheetsClient(
        config.google_credentials_json,
        config.google_spreadsheet_id
    )
    
    # Создаем сервисы
    clients = ClientService(sheets)
    masters = MasterService(sheets)
    bookings = BookingService(sheets)
    
    return sheets, clients, masters, bookings

# ============================================
# ПРИМЕР 2: Работа с клиентами
# ============================================

def example_client_operations():
    """Примеры операций с клиентами"""
    _, clients, _, _ = example_init_services()
    
    # Создание клиента
    clients.create_client(
        user_id=123456789,
        name="Иван Петров",
        phone="+7 (999) 123-45-67",
        email="ivan@example.com"
    )
    
    # Получение клиента
    client = clients.get_client(123456789)
    print(f"Клиент: {client}")
    
    # Получение всех клиентов
    all_clients = clients.get_all_clients()
    print(f"Всего клиентов: {len(all_clients)}")
    
    # Обновление клиента
    clients.update_client(
        123456789,
        name="Иван Петров",
        phone="+7 (999) 123-45-68"
    )
    
    # Проверка существования
    exists = clients.client_exists(123456789)
    print(f"Клиент существует: {exists}")

# ============================================
# ПРИМЕР 3: Работа с мастерами
# ============================================

def example_master_operations():
    """Примеры операций с мастерами"""
    _, _, masters, _ = example_init_services()
    
    # Создание мастера
    masters.create_master(
        name="Алексей",
        specialization="Татуировки",
        phone="+7 (999) 987-65-43",
        calendar_id="alexey@example.com"
    )
    
    # Получение всех мастеров
    all_masters = masters.get_all_masters()
    print(f"Всего мастеров: {len(all_masters)}")
    
    # Получение мастера по имени
    master = masters.get_master_by_name("Алексей")
    print(f"Мастер: {master}")

# ============================================
# ПРИМЕР 4: Работа с записями
# ============================================

def example_booking_operations():
    """Примеры операций с записями"""
    _, _, _, bookings = example_init_services()
    
    # Создание записи
    bookings.create_booking(
        user_id=123456789,
        master_id=1,
        date="15.12.2024",
        time="14:00",
        service="Татуировка рукава"
    )
    
    # Получение записей клиента
    user_bookings = bookings.get_user_bookings(123456789)
    print(f"Записи клиента: {len(user_bookings)}")
    
    # Получение записей мастера
    master_bookings = bookings.get_master_bookings(1)
    print(f"Записи мастера: {len(master_bookings)}")
    
    # Обновление статуса
    from src.config import BOOKING_STATUS_CONFIRMED
    bookings.update_booking_status(1, BOOKING_STATUS_CONFIRMED)

# ============================================
# ПРИМЕР 5: Работа с Google Sheets напрямую
# ============================================

def example_sheets_operations():
    """Примеры прямой работы с Google Sheets"""
    sheets, _, _, _ = example_init_services()
    
    # Получение данных с листа
    data = sheets.get_sheet_values("clients")
    print(f"Данные: {data}")
    
    # Добавление строки
    sheets.append_row("clients", ["999", "Тест", "+79999999999", "test@test.com", "15.12.2024", "active"])
    
    # Обновление ячейки
    sheets.update_cell("clients", "A1", "user_id")
    
    # Поиск строки
    row_idx = sheets.find_row("clients", 1, "Тест")
    print(f"Строка найдена: {row_idx}")

# ============================================
# ПРИМЕР 6: Работа с временем и временными зонами
# ============================================

def example_timezone_operations():
    """Примеры работы с временем"""
    from src.utils.timezone import get_current_time, convert_to_timezone, format_datetime
    from src.config import get_config
    
    config = get_config()
    
    # Получение текущего времени в заданной временной зоне
    now = get_current_time(config.timezone)
    print(f"Текущее время: {format_datetime(now)}")
    
    # Форматирование времени
    formatted = format_datetime(now, "%H:%M:%S")
    print(f"Форматированное время: {formatted}")

# ============================================
# ПРИМЕР 7: Валидация данных
# ============================================

def example_validators():
    """Примеры валидации"""
    from src.utils.validators import (
        validate_phone,
        validate_email,
        validate_name,
        validate_time_slot
    )
    
    # Валидация телефона
    print(validate_phone("+7 (999) 123-45-67"))  # True
    print(validate_phone("invalid"))  # False
    
    # Валидация email
    print(validate_email("test@example.com"))  # True
    print(validate_email("invalid"))  # False
    
    # Валидация имени
    print(validate_name("Иван Петров"))  # True
    print(validate_name("И"))  # False
    
    # Валидация времени
    print(validate_time_slot("14:30"))  # True
    print(validate_time_slot("25:00"))  # False

# ============================================
# ПРИМЕР 8: Получение доступных слотов
# ============================================

def example_slots_finder():
    """Примеры поиска доступных слотов"""
    from src.calendars.slots_finder import SlotsFinder
    
    # Получение доступных слотов
    occupied = ["10:00", "10:30", "11:00"]
    available = SlotsFinder.get_available_slots(occupied)
    print(f"Доступные слоты: {available[:5]}")  # Первые 5
    
    # Получение следующего доступного дня
    next_day = SlotsFinder.get_next_available_day()
    print(f"Следующий доступный день: {next_day}")
    
    # Получение следующих 7 дней
    next_7_days = SlotsFinder.get_next_n_available_days(7)
    print(f"Следующие 7 дней: {next_7_days}")

# ============================================
# ЗАПУСК ПРИМЕРОВ
# ============================================

if __name__ == "__main__":
    print("📚 Примеры использования бота\n")
    
    # Раскомментируйте нужные примеры:
    
    # print("=== Пример 1: Инициализация ===")
    # example_init_services()
    
    # print("\n=== Пример 2: Клиенты ===")
    # example_client_operations()
    
    # print("\n=== Пример 3: Мастера ===")
    # example_master_operations()
    
    # print("\n=== Пример 4: Записи ===")
    # example_booking_operations()
    
    # print("\n=== Пример 5: Google Sheets ===")
    # example_sheets_operations()
    
    # print("\n=== Пример 6: Временные зоны ===")
    # example_timezone_operations()
    
    # print("\n=== Пример 7: Валидация ===")
    # example_validators()
    
    # print("\n=== Пример 8: Поиск слотов ===")
    # example_slots_finder()
    
    print("✅ Примеры готовы к использованию!")
