# 📊 Быстрая миграция БД в Google Sheets - Пошаговое руководство

## Текущее состояние
- ✅ БД уже находится в Google Sheets
- ✅ Все данные доступны INKA через Google Sheets API
- ✅ Cloud Run Service Account имеет права доступа
- ✅ Все required таблицы созданы: `clients`, `masters`, `bookings`, `services`

## Что такое "миграция БД в Google"?

Если вы имеете в виду перенос данных ИЗ другого источника (например, CSV, JSON, другой БД) ВГоogle Sheets - вот как это сделать:

---

## 📋 Вариант 1: Миграция из CSV файла в Google Sheets

### Быстрый способ (1-2 минуты):
```bash
# 1. Откройте Google Sheets
# 2. Создайте новый лист
# 3. Меню → Файл → Импорт
# 4. Загрузите CSV файл
# 5. Выберите лист для вставки
```

### Программный способ:
```python
# Подробный пример в scripts/migrate_from_csv.py
import csv
from src.db.sheets_client import GoogleSheetsClient

client = GoogleSheetsClient("", SPREADSHEET_ID)

# Читаем CSV
with open('clients.csv', 'r') as f:
    rows = list(csv.reader(f))

# Пишем в Google Sheets
for row in rows[1:]:  # Skip header
    client.append_row("clients", row)
```

---

## 📋 Вариант 2: Миграция из SQL БД в Google Sheets

### Из PostgreSQL:
```python
import psycopg2
from src.db.sheets_client import GoogleSheetsClient

# Подключаемся к PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="tattoo_db",
    user="user",
    password="password"
)
cursor = conn.cursor()

# Читаем данные
cursor.execute("SELECT * FROM clients")
rows = cursor.fetchall()

# Пишем в Google Sheets
sheets_client = GoogleSheetsClient("", SPREADSHEET_ID)
for row in rows:
    sheets_client.append_row("clients", list(row))

conn.close()
```

### Из SQLite:
```python
import sqlite3
from src.db.sheets_client import GoogleSheetsClient

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM clients")
rows = cursor.fetchall()

sheets_client = GoogleSheetsClient("", SPREADSHEET_ID)
for row in rows:
    sheets_client.append_row("clients", list(row))

conn.close()
```

### Из MySQL:
```python
import mysql.connector
from src.db.sheets_client import GoogleSheetsClient

conn = mysql.connector.connect(
    host="localhost",
    user="user",
    password="password",
    database="tattoo_db"
)
cursor = conn.cursor()

cursor.execute("SELECT * FROM clients")
rows = cursor.fetchall()

sheets_client = GoogleSheetsClient("", SPREADSHEET_ID)
for row in rows:
    sheets_client.append_row("clients", list(row))

conn.close()
```

---

## 📋 Вариант 3: Миграция из JSON файла

```python
import json
from src.db.sheets_client import GoogleSheetsClient

# Читаем JSON
with open('clients.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sheets_client = GoogleSheetsClient("", SPREADSHEET_ID)

# Предполагаем что это список объектов
for obj in data:
    # Преобразуем в список в нужном порядке
    row = [
        obj.get('id'),
        obj.get('telegram_id'),
        obj.get('name'),
        obj.get('phone'),
        obj.get('email'),
        obj.get('notes'),
        obj.get('created_at'),
        obj.get('last_visit')
    ]
    sheets_client.append_row("clients", row)
```

---

## 🔧 Создам скрипт миграции для вас

```python
# scripts/migrate_database.py - используйте этот скрипт

#!/usr/bin/env python3
"""
Миграция данных в Google Sheets
Поддерживает: CSV, JSON, SQL БД
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import os

load_dotenv()

from src.db.sheets_client import GoogleSheetsClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")

def migrate_from_csv(csv_file: str, sheet_name: str):
    """Миграция из CSV"""
    import csv
    
    logger.info(f"📥 Reading CSV: {csv_file}")
    rows_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Пропускаем заголовок
        
        logger.info(f"   Columns: {header}")
        
        sheets = GoogleSheetsClient("", SPREADSHEET_ID)
        
        for row in reader:
            sheets.append_row(sheet_name, row)
            rows_count += 1
            
            if rows_count % 10 == 0:
                logger.info(f"   Imported {rows_count} rows...")
    
    logger.info(f"✅ Migration complete! {rows_count} rows imported")

def migrate_from_json(json_file: str, sheet_name: str):
    """Миграция из JSON"""
    import json
    
    logger.info(f"📥 Reading JSON: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("JSON должен быть массивом объектов")
    
    sheets = GoogleSheetsClient("", SPREADSHEET_ID)
    rows_count = 0
    
    for obj in data:
        # Преобразуем объект в список
        row = [obj.get(col) for col in obj.keys()]
        sheets.append_row(sheet_name, row)
        rows_count += 1
        
        if rows_count % 10 == 0:
            logger.info(f"   Imported {rows_count} rows...")
    
    logger.info(f"✅ Migration complete! {rows_count} rows imported")

def main():
    parser = argparse.ArgumentParser(description="Миграция данных в Google Sheets")
    parser.add_argument("--type", choices=["csv", "json"], required=True, help="Тип файла")
    parser.add_argument("--file", required=True, help="Путь к файлу")
    parser.add_argument("--sheet", default="clients", help="Имя листа (по умолчанию: clients)")
    
    args = parser.parse_args()
    
    try:
        if args.type == "csv":
            migrate_from_csv(args.file, args.sheet)
        elif args.type == "json":
            migrate_from_json(args.file, args.sheet)
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 📊 Примеры использования

### Импорт из CSV:
```bash
python3 scripts/migrate_database.py --type csv --file clients.csv --sheet clients
python3 scripts/migrate_database.py --type csv --file masters.csv --sheet masters
```

### Импорт из JSON:
```bash
python3 scripts/migrate_database.py --type json --file clients.json --sheet clients
```

---

## ⚠️ ВАЖНО: Проверка перед миграцией

Всегда сначала запустите проверку доступа:
```bash
python3 check_inka_access.py
```

Убедитесь что:
- ✅ `Google Sheets Read` - PASSED
- ✅ `Google Sheets Write` - PASSED
- ✅ `Database Structure` - PASSED

Если какой-то чек не прошел - сначала исправьте проблему!

---

## 🚀 Быстрая миграция БД (все 4 таблицы)

```bash
#!/bin/bash

echo "🚀 Migrating all database tables..."

python3 scripts/migrate_database.py --type csv --file ./data/clients.csv --sheet clients
python3 scripts/migrate_database.py --type csv --file ./data/masters.csv --sheet masters
python3 scripts/migrate_database.py --type csv --file ./data/bookings.csv --sheet bookings
python3 scripts/migrate_database.py --type csv --file ./data/services.csv --sheet services

echo "✅ Migration complete!"
```

---

## 📌 Рекомендация

**ТЕКУЩАЯ СИТУАЦИЯ:**
- ✅ БД уже в Google Sheets
- ✅ INKA уже работает с Google Sheets
- ✅ Все права доступа есть

**ДЕЙСТВИЯ:**
1. Сначала запустите `python3 check_inka_access.py` чтобы убедиться что все работает
2. Если нужно импортировать данные - используйте `migrate_database.py`
3. Основная проблема сейчас - INKA не может записывать клиентов (функция `append_row` возвращает False)
4. Это скорее всего проблема с правами, не с БД

Давайте сначала запустим проверку доступа!
