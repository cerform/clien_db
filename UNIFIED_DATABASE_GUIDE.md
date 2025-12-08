# 🗄️ Руководство по унифицированной базе данных

## 🎯 Что это?

**Unified Database Creator** - это система для создания и управления базой данных, которая работает с **Админ-панелью** и **INKA Assistant** одновременно.

## ⚡ Быстрый старт

### Вариант 1: Интерактивный скрипт (рекомендуется)

```bash
./scripts/quick_setup_db.sh
```

Выберите нужное действие из меню.

### Вариант 2: Прямые команды

```bash
# Показать схему БД
python3 scripts/unified_database_creator.py --schema

# Создать пустую БД
python3 scripts/unified_database_creator.py --create

# Создать БД с тестовыми данными
python3 scripts/unified_database_creator.py --create
python3 scripts/unified_database_creator.py --test-data

# Проверить данные
python3 scripts/unified_database_creator.py --validate
```

## 📊 Структура БД

### 8 основных таблиц:

1. **Masters** - Мастера салона
2. **Clients** - Клиенты
3. **Services** - Каталог услуг
4. **Bookings** - Записи на услуги
5. **Schedule** - Расписание мастеров (важно для INKA!)
6. **Reviews** - Отзывы клиентов
7. **Pricing** - Индивидуальные цены
8. **InkaTraining** - Данные для обучения INKA

## 🔑 Ключевые особенности

### Для Админ-панели:
- ✅ Простые CRUD операции
- ✅ Валидация данных
- ✅ Поддержка поиска
- ✅ Статистика и отчеты

### Для INKA Assistant:
- ✅ Calendar ID для каждого мастера
- ✅ Расписание в формате day_of_week
- ✅ Многоязычная поддержка (ru/en/he)
- ✅ Связь с Google Calendar

## 🔧 Основные сценарии использования

### 1️⃣ Создание новой БД с нуля

```bash
# Шаг 1: Создать структуру
python3 scripts/unified_database_creator.py --create

# Шаг 2: Заполнить тестовыми данными (опционально)
python3 scripts/unified_database_creator.py --test-data

# Шаг 3: Проверить
python3 scripts/unified_database_creator.py --validate
```

**Результат:** Чистая БД с правильной структурой.

### 2️⃣ Миграция существующей БД

```bash
# Шаг 1: Backup
python3 scripts/unified_database_creator.py --backup

# Шаг 2: Посмотреть что будет изменено (dry run)
python3 scripts/unified_database_creator.py --migrate

# Шаг 3: Применить изменения
python3 scripts/unified_database_creator.py --migrate --apply

# Шаг 4: Проверить результат
python3 scripts/unified_database_creator.py --validate
```

**Результат:** Существующие данные приведены к единому стандарту.

### 3️⃣ Регулярная проверка БД

```bash
# Валидация (можно запускать часто)
python3 scripts/unified_database_creator.py --validate
```

**Результат:** Отчет об ошибках и предупреждениях в данных.

### 4️⃣ Полный цикл обслуживания

```bash
# Всё в одной команде
python3 scripts/unified_database_creator.py --full
```

**Результат:** Backup → Migrate → Validate автоматически.

## 📋 Требования к данным

### Обязательные поля для INKA

**Masters:**
- ✅ `id` - уникальный идентификатор
- ✅ `name` - имя мастера
- ✅ `specialization` - специализация
- ✅ `calendar_id` - **КРИТИЧНО для INKA!**

**Schedule:**
- ✅ `master_id` - связь с мастером
- ✅ `day_of_week` - monday/tuesday/.../sunday
- ✅ `start_time` - время начала (HH:MM)
- ✅ `end_time` - время окончания (HH:MM)

### Форматы данных

| Тип | Формат | Пример |
|-----|--------|--------|
| UUID | стандарт или custom | `m_001`, `uuid` |
| Телефон | +код | `+972501234567` |
| Дата | YYYY-MM-DD | `2025-12-08` |
| Время | HH:MM | `14:30` |
| Boolean | TRUE/FALSE | `TRUE` |
| День недели | english | `monday` |

## 🛠️ Интеграция с кодом

### Python

```python
from scripts.unified_database_creator import (
    UnifiedDatabaseCreator,
    UnifiedDatabaseSchema,
    DataValidator
)

# Инициализация
creator = UnifiedDatabaseCreator()

# Валидация
results = creator.validate_database()
print(f"Ошибок: {results['total_errors']}")

# Получить схему
schema = UnifiedDatabaseSchema.get_masters_schema()
print(f"Колонок: {len(schema.columns)}")

# Валидация отдельного значения
is_valid, msg = DataValidator.validate_phone("+972501234567")
```

### Прямой доступ к БД

```python
from src.db.sheets_client import GoogleSheetsClient
from src.config.config import get_config

config = get_config()
client = GoogleSheetsClient(
    config.google_credentials_json,
    config.google_spreadsheet_id
)

# Читаем мастеров
masters = client.get_sheet_values("Masters")
print(f"Мастеров: {len(masters) - 1}")  # -1 для заголовка
```

## ⚠️ Важные замечания

### 1. Calendar ID для INKA

INKA **НЕ БУДЕТ РАБОТАТЬ** без `calendar_id` у мастеров!

```python
# Проверить наличие calendar_id
python3 scripts/unified_database_creator.py --validate
```

Найдите строки с ошибками `"calendar_id": "Обязательное поле пустое"`.

### 2. Названия листов

Скрипт поддерживает оба варианта:
- Английские: `Masters`, `Clients`, `Services`, etc.
- Русские: `Мастера`, `Клиенты`, `Услуги`, etc.

### 3. Backup перед изменениями

**ВСЕГДА** создавайте backup перед:
- Миграцией данных
- Пересозданием структуры
- Массовыми изменениями

```bash
python3 scripts/unified_database_creator.py --backup
```

Backups сохраняются в `backups/backup_YYYYMMDD_HHMMSS.json`.

## 🐛 Решение проблем

### Проблема: "Лист не найден"

**Решение:** Скрипт проверяет оба названия (английское и русское). Убедитесь что лист существует в Google Sheets.

### Проблема: "Некорректный формат телефона"

**Решение:** Используйте формат `+код` без пробелов. Например: `+972501234567`.

### Проблема: "API quota exceeded"

**Решение:** Google Sheets API имеет лимиты. Подождите 1-2 минуты и попробуйте снова.

### Проблема: INKA не видит расписание

**Решение:** 
1. Проверьте что таблица `Schedule` заполнена
2. Убедитесь что `day_of_week` на английском
3. Проверьте что у мастера есть `calendar_id`

```bash
python3 scripts/unified_database_creator.py --validate
```

## 📁 Структура файлов

```
clien_db/
├── scripts/
│   ├── unified_database_creator.py      # Главный скрипт
│   ├── quick_setup_db.sh                # Интерактивное меню
│   └── README_DATABASE_UNIFIER.md       # Подробная документация
├── backups/                             # Backup файлы
│   ├── .gitkeep
│   └── backup_*.json
├── src/
│   ├── db/
│   │   ├── sheets_client.py             # Google Sheets клиент
│   │   └── db_initializer.py            # Старый инициализатор
│   ├── services/
│   │   └── admin_db_manager.py          # Менеджер для админки
│   └── utils/
│       └── database_unifier.py          # Старый унификатор
└── UNIFIED_DATABASE_GUIDE.md            # Этот файл
```

## 📞 Дополнительная помощь

### Документация:
- `scripts/README_DATABASE_UNIFIER.md` - Подробное API
- `INKA_DATABASE_REQUIREMENTS.md` - Требования INKA
- `DATABASE_UPDATE_INKA.md` - История изменений

### Команды справки:
```bash
# Справка по скрипту
python3 scripts/unified_database_creator.py --help

# Показать схему БД
python3 scripts/unified_database_creator.py --schema
```

## ✅ Чеклист готовности БД

- [ ] Структура создана (`--create`)
- [ ] Все мастера имеют `calendar_id`
- [ ] Расписание заполнено для всех мастеров
- [ ] `day_of_week` на английском (monday, tuesday, etc.)
- [ ] Валидация проходит без критических ошибок
- [ ] Backup создан
- [ ] INKA может читать расписание
- [ ] Админ-панель работает с данными

## 🚀 Что дальше?

1. ✅ Создайте БД: `./scripts/quick_setup_db.sh`
2. ✅ Проверьте данные: `--validate`
3. ✅ Запустите бота: `python3 src/main.py`
4. ✅ Откройте админ-панель в браузере
5. ✅ Протестируйте INKA в Telegram

**Готово!** 🎉
