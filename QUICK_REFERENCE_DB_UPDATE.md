# ⚡ БЫСТРАЯ СПРАВКА: ЧТО ИЗМЕНИЛОСЬ В БД

**TL;DR** - Проблема, решение и что делать дальше

---

## 🔴 ПРОБЛЕМА

ИНКА (AI-ассистент) **не работает** из-за отсутствия критичных полей в БД:

```python
# Ошибка 1: calendar_id не существует
calendar_id = master.get("calendar_id")  # ← None!
events = calendar_service.events().list(calendarId=calendar_id)  # ← CRASH

# Ошибка 2: schedule использует неправильную структуру
schedule_rows = [s for s in data if s.get("master_id") == master_id]  # ← Empty!
# Потому что вместо master_id там "Telegram ID Мастера"

# Ошибка 3: bookings не использует правильные связи
bookings = [b for b in data if b.get("client_id") == client_id]  # ← Empty!
# Потому что вместо client_id там "Telegram ID Клиента"
```

---

## ✅ РЕШЕНИЕ

### ДОБАВЛЕНО В ТАБЛИЦЫ:

| Таблица | Добавлено | Тип | Обязательно? |
|---------|-----------|-----|-------------|
| Мастера | `calendar_id` | string (Google Calendar ID) | 🔴 ДА! |
| Мастера | `bio` | text (описание специализации) | 🟡 Рекомендуется |
| Расписание | **`master_id`** | UUID мастера | 🔴 ДА! |
| Расписание | **`day_of_week`** | monday/tuesday/etc | 🔴 ДА! |
| Расписание | **`is_working`** | true/false | 🔴 ДА! |
| Записи | `client_id` | UUID клиента | 🔴 ДА! |
| Записи | `master_id` | UUID мастера | 🔴 ДА! |
| Отзывы | `client_id` | UUID клиента | 🟡 Рекомендуется |
| Отзывы | `master_id` | UUID мастера | 🟡 Рекомендуется |

### ПЕРЕДЕЛАНО:

| Таблица | Было | Стало | Причина |
|---------|-----|-------|---------|
| Расписание | `Дата` + `Время` | `day_of_week` + `start_time/end_time` | ИНКА использует расписание по дням недели |
| Клиенты | Куча полей | `id, telegram_id, name, phone, email, notes, created_at` | Упрощение и стандартизация |

---

## 🚀 ЧТО ДЕЛАТЬ

### Вариант 1️⃣: У вас новая БД (РЕКОМЕНДУЕТСЯ)

```bash
# 1. Инициализировать БД с новой структурой
python3 setup/init_database.py

# 2. Заполнить тестовыми данными
python3 setup/populate_for_inka.py

# 3. Проверить что все работает
python3 validate_db_inka.py

# ✅ Готово!
```

### Вариант 2️⃣: У вас есть существующие данные

```bash
# 1. Экспортировать старые данные (File → Download)
# 2. Создать новую таблицу Google Sheets
# 3. Инициализировать с новой структурой
python3 setup/init_database.py

# 4. Вручную перенести данные или написать миграцию
# 5. Проверить что все работает
python3 validate_db_inka.py
```

---

## 🔑 КРИТИЧНЫЕ ШАГИ

### Шаг 1: Получить calendar_id для каждого мастера

```
Google Calendar → Settings → Integrate calendar → Calendar ID
Пример: abc123def456ghi789@group.calendar.google.com

Вставить в таблицу "Мастера", колонка "calendar_id"
```

### Шаг 2: Заполнить расписание по дням недели

**Старая структура (неправильная):**
| Дата | Время начала | Время окончания |
|------|---|---|
| 2025-12-06 | 10:00 | 19:00 |
| 2025-12-07 | 10:00 | 19:00 |

**Новая структура (правильная):**
| day_of_week | start_time | end_time | is_working |
|---|---|---|---|
| monday | 10:00 | 19:00 | true |
| tuesday | 10:00 | 19:00 | true |
| saturday | 12:00 | 17:00 | true |
| sunday | - | - | false |

### Шаг 3: Убедиться что UUID используются везде

Старое: `Telegram ID Мастера` = `123456`  
Новое: `master_id` = `3b5f4c8e-91a2-4d6e-8c1a-9e2f5c8d1a3b`

Скрипт `populate_for_inka.py` автоматически генерирует UUID!

---

## 🧪 ПРОВЕРКА

```bash
# Запустить валидацию
python3 validate_db_inka.py

# Результат должен быть:
# ✅ БД ПОЛНОСТЬЮ СОВМЕСТИМА С ИНКА! 🎉
```

---

## 📝 НОВЫЕ ФАЙЛЫ

| Файл | Назначение | Размер |
|------|-----------|--------|
| `setup/populate_for_inka.py` | Заполнить БД тестовыми данными | 200+ строк |
| `validate_db_inka.py` | Проверить совместимость БД | 350+ строк |
| `INKA_DATABASE_REQUIREMENTS.md` | Полный анализ требований | 500+ строк |
| `DATABASE_UPDATE_INKA.md` | Инструкции по обновлению | 450+ строк |
| `ANALYSIS_REPORT_INKA.md` | Итоговый отчет | 400+ строк |

---

## 🎯 РЕЗУЛЬТАТ

### До обновления:
```
ИНКА: ❌ Не работает
- Нет calendar_id → Не может получить события
- Неправильное расписание → Не может генерировать слоты
- Нет UUID → Не может создавать записи
```

### После обновления:
```
ИНКА: ✅ Полностью работает
- calendar_id есть → События получаются ✅
- Расписание по дням недели → Слоты генерируются ✅
- UUID везде → Записи создаются ✅
```

---

## 🤔 ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ

### Q: Что делать со старыми данными?
**A:** Экспортируйте, создайте новую таблицу, перенесите вручную или напишите миграцию.

### Q: Обязателен calendar_id?
**A:** 🔴 **ДА!** Без него ИНКА не может работать с Google Calendar.

### Q: Почему day_of_week в английском?
**A:** Python's `datetime.strftime("%A").lower()` возвращает англ. названия (monday, tuesday и т.д.)

### Q: Что такое UUID?
**A:** Уникальный идентификатор вроде `3b5f4c8e-91a2-4d6e-8c1a-9e2f5c8d1a3b`. Используется вместо telegram_id для правильной нормализации БД.

### Q: Скрипт populate_for_inka.py не работает?
**A:** Проверьте что:
1. Google Sheets инициализирована (`init_database.py`)
2. credentials.json правильно сконфигурирован
3. GOOGLE_SPREADSHEET_ID установлен

### Q: Валидация не проходит?
**A:** Запустите `validate_db_inka.py` и прочитайте ошибки в выводе.

---

## 📊 ПРИМЕРЫ

### Правильная таблица "Мастера":

```
id                    | name      | calendar_id
uuid_1234567890abc    | Анна      | calendar_anna@group.calendar.google.com
uuid_0987654321def    | Платон    | calendar_platon@group.calendar.google.com
```

### Правильная таблица "Расписание":

```
id        | master_id  | day_of_week | start_time | end_time | is_working
uuid_aaa  | uuid_1234  | monday      | 10:00      | 19:00    | true
uuid_bbb  | uuid_1234  | tuesday     | 10:00      | 19:00    | true
uuid_ccc  | uuid_1234  | sunday      |            |          | false
```

### Правильная таблица "Записи":

```
id        | client_id    | master_id   | service_id  | date       | time
uuid_xyz  | uuid_client1 | uuid_master1 | uuid_svc1  | 2025-12-10 | 14:00
```

---

## 💬 ОБЗОР ИЗМЕНЕНИЙ

**Строк кода изменено:** 100+ строк в db_initializer.py  
**Новых скриптов:** 2 (populate, validate)  
**Документации:** 2000+ строк  
**Таблиц переделано:** 7 из 7  
**Критичных полей добавлено:** 6  

---

## ✨ ФИНАЛ

**Все готово! ИНКА теперь может:**
- ✅ Получать события из Google Calendar
- ✅ Генерировать доступные слоты для записи
- ✅ Создавать записи с правильными UUID
- ✅ Искать мастеров по специализации
- ✅ Управлять расписанием по дням недели
- ✅ Работать с клиентами и отзывами

**Начните с:**
```bash
python3 setup/init_database.py && \
python3 setup/populate_for_inka.py && \
python3 validate_db_inka.py
```

**Готово! 🎉**
