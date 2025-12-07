# 🔍 АНАЛИЗ ТРЕБОВАНИЙ ИНКА К БАЗЕ ДАННЫХ

## Дата анализа: 6 декабря 2025

---

## 1. ОБЗОР АРХИТЕКТУРЫ

### Взаимодействие компонентов:
```
CLIENT (Telegram)
    ↓
HANDLER (bot/handlers/client_handler.py)
    ↓
ADVANCED INKA (src/ai/advanced_inka.py)
    ↓
┌─────────────────────────────────────┐
│   СИСТЕМА ПОЛУЧЕНИЯ ДАННЫХ:         │
├─────────────────────────────────────┤
│ • GoogleSheetsClient (БД Sheets)    │
│ • Google Calendar API (расписание)  │
│ • DataSyncService (кэш и синхр)    │
│ • Cache (расписание, мастера, услуги)
└─────────────────────────────────────┘
```

---

## 2. ТАБЛИЦЫ БД И ПОЛЯ, КОТОРЫЕ ИЩЕТ ИНКА

### 📋 ТАБЛИЦА: clients (Клиенты)

**Текущие поля:**
- ✅ ID
- ✅ Telegram ID
- ✅ Имя
- ✅ Телефон
- ✅ Email
- ✅ Дата регистрации
- ✅ Статус
- ✅ Всего визитов
- ✅ Общая потрачено (руб)
- ✅ Примечания

**ИСПОЛЬЗУЕТСЯ В ИНКА:**
- `telegram_id` - для поиска клиента по ID: `get_database_info("clients", "telegram_id", telegram_id_str)`
- `id` - для создания записей: сохраняется как `client_id` в bookings
- `name` - для отображения профиля

**ПРОБЛЕМЫ:** ✅ ВСЕ ПОЛЯ ПРИСУТСТВУЮТ

---

### 👥 ТАБЛИЦА: masters (Мастера)

**Текущие поля:**
- ✅ ID
- ✅ Имя
- ✅ Специальность
- ✅ Опыт (лет)
- ✅ Рейтинг
- ✅ Телефон
- ✅ Instagram
- ✅ Цена за сеанс (руб)
- ✅ Статус
- ✅ Описание

**ИСПОЛЬЗУЕТСЯ В ИНКА:**
- `id` - для фильтрации: `schedule.get("master_id") == master_id`
- `specialization` - для поиска по стилю: `get_database_info("masters", "specialization", keyword)`
- `bio` или `description` - для поиска по ключевому слову (реализм, минимализм)
- `name` - для отображения: `masters_data["data"][0].get("name")`

**ОТСУТСТВУЮЩИЕ ПОЛЯ:**
- ❌ **calendar_id** - КРИТИЧНО! Нужен для получения событий из Google Calendar: 
  ```python
  calendar_id = master.get("calendar_id")
  events_result = self.calendar_service.events().list(calendarId=calendar_id)
  ```
- ❌ **bio** - поле для подробного описания специализации (в db_initializer есть "Описание", но нужна проверка согласованности)
- ⚠️ **day_off** - дни отдыха (опционально, но может быть использовано для фильтрации)

---

### 📅 ТАБЛИЦА: schedule (Расписание)

**Текущие поля:**
- ✅ ID
- ✅ Telegram ID Мастера
- ✅ Имя мастера
- ✅ Дата
- ✅ Время начала
- ✅ Время окончания
- ✅ Занято/Свободно
- ✅ Тип события
- ✅ Примечания

**ТРЕБУЕМЫЕ ДЛЯ ИНКА:**
- ❌ **master_id** - КРИТИЧНО! advanced_inka.py ищет именно это поле:
  ```python
  schedule_rows = [s for s in schedule_rows if s.get("master_id") == master_id]
  day_schedule = [s for s in schedule_rows if s.get("day_of_week") == day_of_week]
  ```
- ❌ **day_of_week** - день недели (monday, tuesday и т.д.) для генерации слотов:
  ```python
  day_of_week = current.strftime("%A").lower()
  day_schedule = [s for s in schedule_rows if s.get("day_of_week") == day_of_week]
  ```
- ❌ **start_time** - время в формате HH:MM
- ❌ **end_time** - время в формате HH:MM
- ❌ **is_working** - флаг рабочего дня ("true"/"false"):
  ```python
  if schedule.get("is_working") != "true":
      continue
  ```

**ПРОБЛЕМЫ:** ⚠️ СТРУКТУРА НЕ СООТВЕТСТВУЕТ! 
- Вместо `master_id` там `Telegram ID Мастера`
- Вместо `day_of_week` там `Дата`
- Отсутствуют правильные временные поля

---

### 📝 ТАБЛИЦА: bookings (Записи)

**Текущие поля:**
- ✅ ID
- ✅ Telegram ID Клиента
- ✅ Имя клиента
- ✅ Telegram ID Мастера
- ✅ Имя мастера
- ✅ Услуга
- ✅ Дата/Время
- ✅ Длительность (мин)
- ✅ Цена (руб)
- ✅ Статус
- ✅ Дата создания
- ✅ Примечания

**ИСПОЛЬЗУЕТСЯ В ИНКА:**
```python
booking_row = [
    booking_id,          # id
    client_id,           # client_id (NOT telegram_id!)
    master_id,           # master_id (NOT telegram_id!)
    service,             # service_id
    date,                # date
    time,                # time
    "60",                # duration_min
    "",                  # price
    "confirmed",         # status
    notes,               # notes
    created_at           # created_at
]
```

**ПРОБЛЕМЫ:** ⚠️ НЕСООТВЕТСТВИЕ СТРУКТУРЫ!
- ИНКА использует `client_id` (UUID/string), а Sheets имеет `Telegram ID Клиента`
- ИНКА использует `master_id` (UUID/string), а Sheets имеет `Telegram ID Мастера`
- Текущая структура не позволяет связывать записи с UUID мастеров/клиентов

---

### 💼 ТАБЛИЦА: services (Услуги)

**Текущие поля:**
- ✅ ID
- ✅ Название
- ✅ Описание
- ✅ Длительность (мин)
- ✅ Базовая цена (руб)
- ✅ Категория
- ✅ Статус
- ✅ Изображение URL

**ИСПОЛЬЗУЕТСЯ В ИНКА:**
- `id` - для фильтрации и связи в bookings
- `name` - для отображения
- `duration_min` - для расчета времени

**ПРОБЛЕМЫ:** ✅ СТРУКТУРА ПРАВИЛЬНАЯ

---

### 📊 ТАБЛИЦА: reviews (Отзывы)

**Текущие поля:**
- ✅ ID
- ✅ Telegram ID Клиента
- ✅ Имя клиента
- ✅ Telegram ID Мастера
- ✅ Имя мастера
- ✅ Оценка (1-5)
- ✅ Текст отзыва
- ✅ Дата отзыва
- ✅ ID записи
- ✅ Полезно

**ПРОБЛЕМЫ:** ⚠️ НЕСООТВЕТСТВИЕ СТРУКТУРЫ!
- Использует `Telegram ID` вместо `client_id`/`master_id`

---

### 💰 ТАБЛИЦА: price_list (Прайс-лист)

**Текущие поля:**
- ✅ ID
- ✅ Мастер
- ✅ Услуга
- ✅ Цена (руб)
- ✅ Комиссия (%)
- ✅ Чистый доход
- ✅ Дата добавления
- ✅ Активна
- ✅ Примечания

**ПРОБЛЕМЫ:** ⚠️ СЛАБАЯ СВЯЗЬ
- `Мастер` - должно быть `master_id` (UUID)
- `Услуга` - должно быть `service_id` (UUID)

---

## 3. КРИТИЧЕСКИЕ НЕДОСТАТКИ ДЛЯ РАБОТЫ ИНКА

### 🔴 КРИТИЧНЫЕ (ИНКА НЕ РАБОТАЕТ БЕЗ ЭТОГО):

1. **masters.calendar_id** - ОБЯЗАТЕЛЕН для Google Calendar API
   - Сейчас: ❌ ОТСУТСТВУЕТ
   - Влияние: Календарь не работает, слоты не генерируются
   - Решение: Добавить поле `calendar_id` (string)

2. **schedule.master_id** - для связи с мастером
   - Сейчас: ❌ ИСПОЛЬЗУЕТСЯ `Telegram ID Мастера`
   - Влияние: Фильтрация расписания не работает
   - Решение: Добавить `master_id` (UUID)

3. **schedule.day_of_week** - для дневного расписания
   - Сейчас: ❌ ИСПОЛЬЗУЕТСЯ `Дата` (не подходит)
   - Влияние: Генерация слотов не работает
   - Решение: Добавить `day_of_week` (monday, tuesday и т.д.)

4. **schedule.start_time, end_time** - временные границы работы
   - Сейчас: ❌ ИСПОЛЬЗУЕТСЯ `Время начала` / `Время окончания` (может подойти)
   - Влияние: Слоты генерируются неправильно
   - Решение: Убедиться, что формат HH:MM

5. **schedule.is_working** - флаг рабочего дня
   - Сейчас: ❌ ОТСУТСТВУЕТ
   - Влияние: Нельзя отключить рабочий день
   - Решение: Добавить `is_working` (true/false)

### 🟠 ВАЖНЫЕ (ФИЧИ НЕ РАБОТАЮТ):

6. **bookings.client_id** - вместо telegram_id
   - Сейчас: Используется `Telegram ID Клиента`
   - Влияние: Связь с таблицей clients нарушена
   - Решение: Добавить `client_id` (UUID)

7. **bookings.master_id** - вместо telegram_id
   - Сейчас: Используется `Telegram ID Мастера`
   - Влияние: Связь с таблицей masters нарушена
   - Решение: Добавить `master_id` (UUID)

8. **masters.bio** - для поиска по специализации
   - Сейчас: Есть `Описание`
   - Влияние: Поиск по ключевому слову не работает правильно
   - Решение: Убедиться, что поле используется

---

## 4. ФУНКЦИИ ИНКА И ИХ ТРЕБОВАНИЯ К БД

### `get_database_info(table, filter_field, filter_value)`
```python
# Требует существования всех полей в таблице
clients: telegram_id, id, name
masters: id, specialization, bio/description
bookings: client_id, master_id, date, time, service, status
services: id, name, description
schedule: master_id, day_of_week, start_time, end_time, is_working
```

### `get_calendar_slots(start_date, end_date, master_id, duration_minutes)`
```python
# Требует:
1. masters.calendar_id (для Google Calendar API)
2. schedule.master_id, day_of_week, start_time, end_time, is_working
3. Google Calendar события
```

### `create_booking(user_id, master_id, date, time, service, notes)`
```python
# Требует:
1. clients: telegram_id (для поиска), id (для создания)
2. masters: id, name
3. bookings: client_id, master_id, service_id, date, time, status
```

### `create_client(telegram_id, name, phone, email, notes)`
```python
# Требует:
1. clients: id, telegram_id, name, phone, email, notes, created_at
```

---

## 5. ИСПОЛЬЗУЕМЫЕ ПОЛЯ ПО ТИПАМ

### Поля в цикле для всех мастеров (data_sync):
```python
for master in self._masters_data:
    calendar_id = master.get("calendar_id")  # ОТСУТСТВУЕТ!
    master_id = master.get("id")             # OK
    name = master.get("name")                # OK
```

### Поля в цикле для расписания:
```python
for schedule in schedule_rows:
    if schedule.get("is_working") != "true":  # ОТСУТСТВУЕТ!
        continue
    
    start_time = schedule.get("start_time", "10:00")
    end_time = schedule.get("end_time", "18:00")
    master_id = schedule.get("master_id")     # ОТСУТСТВУЕТ!
    day_of_week = schedule.get("day_of_week") # ОТСУТСТВУЕТ!
```

---

## 6. РЕШЕНИЕ

### НЕОБХОДИМЫЕ ИЗМЕНЕНИЯ В db_initializer.py:

1. **Таблица Мастера** - добавить колонку:
   - `calendar_id` (string) - ID Google Calendar

2. **Таблица Расписание** - ПЕРЕДЕЛАТЬ СТРУКТУРУ:
   - Удалить: `Дата` (не нужна для недельного расписания)
   - Изменить: `Telegram ID Мастера` → `master_id`
   - Добавить: `day_of_week` (monday, tuesday, etc.)
   - Переименовать: `Время начала` → `start_time` (формат HH:MM)
   - Переименовать: `Время окончания` → `end_time` (формат HH:MM)
   - Добавить: `is_working` (true/false)

3. **Таблица Записи** - добавить колонки:
   - `client_id` (UUID) - связь с clients
   - `master_id` (UUID) - связь с masters
   - Сохранить: telegram_id для отладки

4. **Таблица Отзывы** - добавить колонки:
   - `client_id` (UUID) - вместо telegram_id
   - `master_id` (UUID) - вместо telegram_id
   - Сохранить: telegram_id для отладки

---

## 7. ПРИМЕРЫ ПРАВИЛЬНЫХ СТРУКТУР

### Правильная таблица Schedule:
| ID | master_id | day_of_week | start_time | end_time | is_working | notes |
|----|-----------|-------------|-----------|----------|-----------|-------|
| 1 | master_uuid_123 | monday | 10:00 | 18:00 | true | Normal work day |
| 2 | master_uuid_123 | tuesday | 10:00 | 18:00 | true | Normal work day |
| 3 | master_uuid_123 | saturday | 12:00 | 17:00 | true | Reduced hours |
| 4 | master_uuid_123 | sunday | - | - | false | Day off |

### Правильная таблица Bookings:
| ID | client_id | master_id | service_id | date | time | duration_min | status | created_at |
|----|-----------|-----------|-----------|------|------|--------------|--------|-----------|
| 1 | client_uuid_456 | master_uuid_123 | service_uuid_789 | 2025-12-10 | 14:00 | 60 | confirmed | 2025-12-06 10:00 |

### Правильная таблица Masters:
| ID | name | specialization | calendar_id | bio | phone | instagram |
|----|------|-----------------|-------------|-----|-------|-----------|
| 1 | Анна Леви | Реалистичные татуировки | calendar_id_from_google | Специалист по реалистичным татуировкам... | +972... | @m_anna_levi |

---

## 8. ТЕСТИРОВАНИЕ ПОСЛЕ ИЗМЕНЕНИЙ

После обновления БД нужно:

1. ✅ Инициализировать БД с новой структурой
2. ✅ Добавить примеры расписания мастеров
3. ✅ Добавить calendar_id для каждого мастера
4. ✅ Протестировать:
   - `get_calendar_slots()` - должны генерироваться слоты
   - `get_database_info()` - должны работать фильтры
   - `create_booking()` - должны создаваться записи с правильными UUID
   - Поиск по специализации - должен находить мастеров

---

## ЗАКЛЮЧЕНИЕ

**ИНКА полностью неработоспособна без следующих полей:**

1. ❌ `masters.calendar_id` - КРИТИЧНО
2. ❌ `schedule.master_id` - КРИТИЧНО
3. ❌ `schedule.day_of_week` - КРИТИЧНО
4. ❌ `schedule.start_time, end_time` - нужна проверка формата
5. ❌ `schedule.is_working` - нужно добавить

**После добавления этих полей ИНКА будет полностью функциональна!**
