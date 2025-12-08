# 📊 Унификация базы данных - Руководство

## 🎯 Цель

Привести базу данных к единому стандарту для совместного использования ИНКОЙ и Административной панелью.

## 📋 Структура таблиц

### 🎨 Мастера (Masters)
```
ID | name | phone | telegram_id | specialization | rating | experience | instagram | status | bio | calendar_id
```

**Используется:**
- INKA: Поиск мастеров, информация о специализации, calendar_id для записей
- Admin Panel: Управление мастерами, редактирование данных

### 👥 Клиенты (Clients)
```
id | telegram_id | name | phone | email | notes | created_at | last_visit
```

**Используется:**
- INKA: Идентификация клиентов, создание записей
- Admin Panel: Просмотр и управление клиентской базой

**Расширенные данные в notes:**
- Город клиента
- Пол (М/Ж)
- Первая татуировка (Да/Нет)

### 💼 Услуги (Services)
```
id | name | description | duration_min | price_from | price_to | category | active
```

**Используется:**
- INKA: Информация о прайсах, длительности процедур
- Admin Panel: Управление прайс-листом

### 📅 Записи (Bookings)
```
id | client_id | master_id | service_id | date | time | duration_min | price | status | notes | created_at
```

**Используется:**
- INKA: Создание и проверка записей
- Admin Panel: Управление расписанием, просмотр записей

### 🗓️ Расписание (Schedule)
```
id | master_id | day_of_week | start_time | end_time | is_working | break_start | break_end | notes
```

**Используется:**
- INKA: Поиск свободных слотов для записи
- Admin Panel: Настройка расписания мастеров

## 🔧 Использование

### Запуск унификации (проверка без изменений)
```bash
python src/utils/database_unifier.py
```

### Применение изменений
```bash
python src/utils/database_unifier.py --apply
```

### Унификация конкретной таблицы
```bash
python src/utils/database_unifier.py --table masters
python src/utils/database_unifier.py --table clients
python src/utils/database_unifier.py --table services
```

## 📚 Функции парсинга

### 1. Парсинг имени клиента
```python
from src.utils.database_unifier import DatabaseUnifier

unifier = DatabaseUnifier(sheets_client)
name_parts = unifier.parse_client_name("Иван Петров")
# Результат: {'full_name': 'Иван Петров', 'first_name': 'Иван', 'last_name': 'Петров', 'display_name': 'Иван'}
```

### 2. Нормализация телефона
```python
phone = unifier.parse_phone_number("+972-50-123-45-67")
# Результат: "+972501234567"
```

### 3. Поиск ID мастера по имени
```python
from src.utils.db_helpers import parse_master_id

masters = [{'id': 'm_anna', 'name': 'Анна Федорова'}]
master_id = parse_master_id("Запись к Анне", masters)
# Результат: "m_anna"
```

### 4. Извлечение информации из заметок
```python
notes = "Город: Тель-Авив | Пол: М | Первая тату: Да"
info = unifier.extract_client_info_from_notes(notes)
# Результат: {'city': 'Тель-Авив', 'gender': 'male', 'is_first_tattoo': True}
```

### 5. Поиск свободных слотов
```python
from src.utils.db_helpers import get_available_time_slots

schedule = [{'day_of_week': 'monday', 'start_time': '09:00', 'end_time': '18:00', 'is_working': 'true'}]
bookings = []
slots = get_available_time_slots(schedule, bookings, '2025-12-09', duration_min=60)
# Результат: ['09:00', '10:00', '11:00', ...]
```

### 6. Форматирование информации
```python
from src.utils.db_helpers import format_master_info, format_service_info

# Форматирование данных мастера
master = {'name': 'Анна', 'specialization': 'Реализм', 'rating': '4.8', 'experience': '8'}
info = format_master_info(master, language='ru')

# Форматирование данных услуги
service = {'name': 'Маленькая тату', 'duration_min': '60', 'price_from': '250'}
info = format_service_info(service, language='ru')
```

## 🔍 Валидация данных

При унификации автоматически проверяются:

✅ **Мастера:**
- Наличие имени и ID
- Корректность формата телефона

✅ **Клиенты:**
- Наличие имени и ID
- Валидность данных

✅ **Услуги:**
- Наличие названия и цены
- Положительные значения длительности

## 📊 Отчёт о валидации

После запуска унификации выводится:

```
================================================================================
📊 СТАТИСТИКА УНИФИКАЦИИ
================================================================================
✅ Мастеров обработано: 15
✅ Клиентов обработано: 234
✅ Услуг обработано: 42
⚠️  Ошибок валидации: 3

⚠️  ОБНАРУЖЕНЫ ОШИБКИ ВАЛИДАЦИИ:
  - Мастера: m_123 -> ['Некорректный номер телефона: 123']
  - Клиенты: c_456 -> ['Отсутствует имя клиента']
================================================================================
```

## 🛡️ Безопасность

- ✅ Автоматическое создание резервных копий перед изменениями
- ✅ Режим `dry_run` по умолчанию (только проверка)
- ✅ Логирование всех операций
- ✅ Валидация данных перед сохранением

## 🔗 Интеграция с ИНКОЙ

ИНКА использует эти функции для:

1. **Парсинг имён клиентов** при создании записи
2. **Нормализация телефонов** для связи с клиентами
3. **Поиск мастеров** по имени или специализации
4. **Извлечение информации** о клиенте из заметок (город, пол, опыт)
5. **Валидация дат и времени** при бронировании

## 🔗 Интеграция с Админ-панелью

Админ-панель использует:

1. **Нормализацию данных** при добавлении/редактировании
2. **Валидацию полей** перед сохранением
3. **Форматирование информации** для отображения
4. **Статистику по записям** для дашборда
5. **Группировку данных** по датам/мастерам

## 📝 Примеры использования в коде

### В ИНКА (advanced_inka.py)
```python
from src.utils.db_helpers import parse_master_id, normalize_phone, format_booking_info

# Поиск мастера по имени
master_id = parse_master_id(user_message, masters_list)

# Нормализация телефона клиента
client_phone = normalize_phone(raw_phone)

# Форматирование информации о записи
booking_text = format_booking_info(booking, master_name, client_name, language='ru')
```

### В Админ-панели (admin_db_manager.py)
```python
from src.utils.database_unifier import DatabaseUnifier
from src.utils.db_helpers import validate_date, validate_time

# Валидация при создании записи
if not validate_date(booking_date):
    return False, "Некорректная дата"

if not validate_time(booking_time):
    return False, "Некорректное время"

# Нормализация данных мастера
normalized = unifier.normalize_master_data(master_data)
```

## 🚀 Рекомендации

1. **Запускайте проверку регулярно** для поддержания качества данных
2. **Используйте `--apply`** только после проверки результатов
3. **Создавайте резервные копии** перед массовыми изменениями
4. **Исправляйте ошибки валидации** как можно скорее

## 📞 Поддержка

При возникновении проблем проверьте:
1. Логи в консоли
2. Список ошибок валидации
3. Формат данных в Google Sheets

## 🎉 Результат

После унификации вы получите:
- ✅ Единый стандарт данных
- ✅ Автоматический парсинг и нормализацию
- ✅ Валидацию на уровне БД
- ✅ Удобные функции для работы с данными
- ✅ Совместимость между ИНКОЙ и Админ-панелью
