# 🗄️ Unified Database Creator

## Описание

Универсальный скрипт для создания и унификации базы данных в Google Sheets.
Поддерживает как **Админ-панель**, так и **INKA Assistant**.

## 🚀 Быстрый старт

```bash
# 1. Посмотреть схему БД
python scripts/unified_database_creator.py --schema

# 2. Создать структуру БД
python scripts/unified_database_creator.py --create

# 3. Заполнить тестовыми данными
python scripts/unified_database_creator.py --test-data

# 4. Проверить данные
python scripts/unified_database_creator.py --validate
```

## 📋 Команды

| Команда | Описание |
|---------|----------|
| `--schema` | Показать схему всех таблиц |
| `--create` | Создать структуру БД (пустые таблицы) |
| `--create --force` | Пересоздать БД с нуля (удалит существующие листы!) |
| `--validate` | Проверить данные на соответствие схеме |
| `--migrate` | Миграция данных в унифицированный формат (dry run) |
| `--migrate --apply` | Применить миграцию |
| `--backup` | Создать backup всех данных |
| `--restore <file>` | Восстановить из backup |
| `--full` | Полный цикл: backup → migrate → validate |
| `--test-data` | Заполнить тестовыми данными |

## 🗂️ Структура БД

### Masters (Мастера)
Информация о мастерах салона.

| Поле | Обязательное | Тип | Описание |
|------|-------------|-----|----------|
| `id` | ✅ | UUID | Уникальный ID (формат: m_xxx) |
| `name` | ✅ | string | Полное имя |
| `phone` | ❌ | phone | Телефон (+972...) |
| `telegram_id` | ❌ | string | Telegram ID |
| `specialization` | ✅ | string | tattoo/piercing/etc |
| `rating` | ❌ | number | Рейтинг 0-5 |
| `experience` | ❌ | number | Опыт в годах |
| `instagram` | ❌ | string | @username |
| `status` | ❌ | string | active/inactive |
| `bio` | ❌ | string | Описание |
| `calendar_id` | ✅ | string | Google Calendar ID (для INKA!) |
| `name_ru/en/he` | ❌ | string | Многоязычность |
| `bio_ru/en/he` | ❌ | string | Многоязычность |

### Clients (Клиенты)
Информация о клиентах.

| Поле | Обязательное | Тип | Описание |
|------|-------------|-----|----------|
| `id` | ✅ | UUID | Уникальный ID |
| `telegram_id` | ❌ | string | Telegram ID |
| `name` | ✅ | string | Имя клиента |
| `phone` | ❌ | phone | Телефон |
| `email` | ❌ | email | Email |
| `notes` | ❌ | string | Заметки |
| `created_at` | ❌ | datetime | Дата регистрации |
| `last_visit` | ❌ | datetime | Последний визит |
| `language` | ❌ | string | ru/en/he |
| `total_visits` | ❌ | number | Количество визитов |
| `total_spent` | ❌ | number | Общая сумма |

### Services (Услуги)
Каталог услуг.

| Поле | Обязательное | Тип | Описание |
|------|-------------|-----|----------|
| `id` | ✅ | UUID | Уникальный ID (формат: s_xxx) |
| `name` | ✅ | string | Название |
| `description` | ❌ | string | Описание |
| `duration_min` | ✅ | number | Длительность (минуты) |
| `price_from` | ✅ | number | Цена от |
| `price_to` | ❌ | number | Цена до |
| `category` | ❌ | string | Категория |
| `active` | ❌ | boolean | TRUE/FALSE |
| `name_ru/en/he` | ❌ | string | Многоязычность |
| `description_ru/en/he` | ❌ | string | Многоязычность |

### Bookings (Записи)
Записи на услуги.

| Поле | Обязательное | Тип | Описание |
|------|-------------|-----|----------|
| `id` | ✅ | UUID | Уникальный ID (формат: b_xxx) |
| `client_id` | ✅ | string | ID клиента |
| `master_id` | ✅ | string | ID мастера |
| `service_id` | ✅ | string | ID услуги |
| `date` | ✅ | date | YYYY-MM-DD |
| `time` | ✅ | time | HH:MM |
| `duration_min` | ❌ | number | Длительность |
| `price` | ❌ | number | Цена |
| `status` | ❌ | string | pending/confirmed/completed/cancelled |
| `notes` | ❌ | string | Заметки |
| `created_at` | ❌ | datetime | Дата создания |
| `google_event_id` | ❌ | string | ID в Google Calendar |

### Schedule (Расписание)
**ВАЖНО для INKA!** Рабочее время мастеров.

| Поле | Обязательное | Тип | Описание |
|------|-------------|-----|----------|
| `id` | ✅ | UUID | Уникальный ID |
| `master_id` | ✅ | string | ID мастера |
| `day_of_week` | ✅ | string | monday/tuesday/.../sunday |
| `start_time` | ✅ | time | HH:MM |
| `end_time` | ✅ | time | HH:MM |
| `is_working` | ❌ | boolean | TRUE/FALSE |
| `break_start` | ❌ | time | HH:MM |
| `break_end` | ❌ | time | HH:MM |
| `notes` | ❌ | string | Заметки |

### Reviews (Отзывы)
Отзывы клиентов.

### Pricing (Прайс-лист)
Индивидуальные цены мастеров.

### InkaTraining (Обучение INKA)
Данные для обучения ассистента.

## 🔄 Примеры использования

### Создание новой БД с нуля

```bash
# 1. Создать структуру
python scripts/unified_database_creator.py --create

# 2. Заполнить тестовыми данными
python scripts/unified_database_creator.py --test-data

# 3. Проверить
python scripts/unified_database_creator.py --validate
```

### Миграция существующих данных

```bash
# 1. Сделать backup
python scripts/unified_database_creator.py --backup

# 2. Проверить что будет изменено (dry run)
python scripts/unified_database_creator.py --migrate

# 3. Применить изменения
python scripts/unified_database_creator.py --migrate --apply

# 4. Проверить результат
python scripts/unified_database_creator.py --validate
```

### Восстановление из backup

```bash
# Найти backup файл
ls backups/

# Восстановить
python scripts/unified_database_creator.py --restore backups/backup_20231208_120000.json
```

## ⚠️ Важные замечания

1. **calendar_id обязателен для INKA!** Без него бот не сможет работать с расписанием мастера.

2. **Формат ID:**
   - Мастера: `m_xxx` (например: `m_001`, `m_abc123`)
   - Услуги: `s_xxx` (например: `s_001`, `s_tattoo`)
   - Записи: `b_xxx` (например: `b_001`)
   - Или стандартный UUID

3. **День недели в Schedule:** Используйте английские названия: `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`

4. **Время:** Всегда в формате `HH:MM` (например: `09:00`, `14:30`)

5. **Boolean:** `TRUE` или `FALSE` (регистр не важен)

## 🔧 Интеграция с кодом

```python
from scripts.unified_database_creator import UnifiedDatabaseCreator, UnifiedDatabaseSchema

# Создать экземпляр с существующим клиентом
from src.db.sheets_client import GoogleSheetsClient
client = GoogleSheetsClient(credentials_file, spreadsheet_id)
creator = UnifiedDatabaseCreator(sheets_client=client)

# Или позволить автоматическую инициализацию
creator = UnifiedDatabaseCreator()

# Валидация
results = creator.validate_database()
if results["total_errors"] > 0:
    print("Найдены ошибки!")

# Получить схему таблицы
masters_schema = UnifiedDatabaseSchema.get_masters_schema()
for col in masters_schema.columns:
    print(f"{col.name}: {col.description}")
```

## 📁 Структура файлов

```
clien_db/
├── scripts/
│   ├── unified_database_creator.py  # Главный скрипт
│   └── README_DATABASE_UNIFIER.md   # Эта документация
├── backups/                          # Backup файлы
│   └── backup_YYYYMMDD_HHMMSS.json
├── src/
│   ├── db/
│   │   └── sheets_client.py         # Google Sheets клиент
│   └── services/
│       └── admin_db_manager.py      # Менеджер БД
```

## 🐛 Troubleshooting

### Ошибка "Лист не найден"
Скрипт проверяет оба варианта названия (английский и русский): `Masters` и `Мастера`.

### Ошибка credentials
Убедитесь что файл `credentials.json` существует и имеет правильные права.

### Ошибка "API quota exceeded"
Подождите минуту и попробуйте снова. Google Sheets API имеет лимиты.

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи (`--validate`)
2. Создайте backup
3. Обратитесь к администратору
