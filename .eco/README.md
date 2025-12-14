# .eco - Virtual Environment для Tattoo Bot

## Что это такое?

`.eco` - это изолированная виртуальная среда Python для проекта Tattoo Bot. Она содержит все необходимые библиотеки и зависимости, изолированные от системного Python.

## Зачем нужна виртуальная среда?

- Изоляция зависимостей проекта от других Python проектов
- Воспроизводимость окружения на разных машинах
- Отсутствие конфликтов версий библиотек
- Легкость очистки и пересоздания

## Активация виртуальной среды

### Linux/macOS:
```bash
source .eco/bin/activate
```

### Windows:
```bash
.eco\Scripts\activate
```

После активации в терминале появится префикс `(.eco)`.

## Деактивация

```bash
deactivate
```

## Установленные пакеты

Все зависимости из `requirements.txt`:

### Основные:
- `aiogram==3.15.0` - Telegram Bot framework
- `fastapi` - Web framework для админ-панели
- `uvicorn` - ASGI сервер
- `sqlalchemy` - ORM для работы с PostgreSQL
- `psycopg2-binary` - PostgreSQL адаптер

### Google Cloud:
- `google-cloud-secret-manager` - управление секретами
- `google-cloud-sql` - Cloud SQL интеграция
- `gspread` - работа с Google Sheets (legacy)

### AI/LLM:
- `openai` - OpenAI API для INKA
- `anthropic` - Claude API (опционально)

### Утилиты:
- `python-dotenv` - загрузка .env переменных
- `pydantic` - валидация данных
- `jinja2` - шаблоны для веб-интерфейса

Полный список: `pip list`

## Обновление пакетов

```bash
source .eco/bin/activate
pip install -r requirements.txt --upgrade
```

## Пересоздание с нуля

```bash
# Удалить старую среду
rm -rf .eco

# Создать новую
python3 -m venv .eco

# Активировать
source .eco/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

## Безопасность: Очистка sensitive данных

**ВАЖНО**: `.eco` НЕ должна содержать:
- API ключи
- Пароли
- Токены
- Credentials файлы

Все секреты должны храниться в:
1. `.env` файле (добавлен в `.gitignore`)
2. Google Secret Manager (для production)

### Проверка на утечки:

```bash
# Поиск потенциальных секретов в .eco
grep -r "sk-" .eco/ 2>/dev/null || echo "No OpenAI keys found"
grep -r "xox" .eco/ 2>/dev/null || echo "No Slack tokens found"
grep -r "ghp_" .eco/ 2>/dev/null || echo "No GitHub tokens found"
```

### Что можно безопасно удалить:

```bash
# Кэши pip
rm -rf .eco/lib/python*/site-packages/*.dist-info

# Скомпилированные файлы
find .eco -name "*.pyc" -delete
find .eco -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```

## Интеграция с one-click installer

При запуске `tools/easy_install.sh`:

1. Скрипт НЕ использует `.eco` (Cloud Run создаёт свою среду)
2. `.eco` нужна только для локальной разработки
3. Production использует Docker/buildpacks на Cloud Run

## Workflow разработчика

```bash
# 1. Клонировать репозиторий
git clone <repo>
cd clien_db

# 2. Создать виртуальную среду
python3 -m venv .eco

# 3. Активировать
source .eco/bin/activate

# 4. Установить зависимости
pip install -r requirements.txt

# 5. Настроить .env
cp .env.example .env
# Отредактировать .env с вашими ключами

# 6. Запустить локально
python run_production.py

# 7. Или запустить тесты
pytest tests/
```

## Локальная разработка с PostgreSQL

```bash
# Активировать .eco
source .eco/bin/activate

# Запустить Cloud SQL proxy
./cloud_sql_proxy -instances=tattoo-480007:us-central1:tattoo-db=tcp:5432 &

# Установить DATABASE_URL
export DATABASE_URL="postgresql://root:password@127.0.0.1:5432/admin_messages"

# Запустить миграцию
python scripts/migrate_all_to_postgres.py

# Запустить бота
python run_production.py
```

## Troubleshooting

### Ошибка: "No module named 'aiogram'"
```bash
source .eco/bin/activate
pip install -r requirements.txt
```

### Ошибка: "psycopg2 not found"
```bash
# Для Ubuntu/Debian
sudo apt-get install libpq-dev python3-dev
pip install psycopg2-binary
```

### Ошибка: "Permission denied"
```bash
chmod +x .eco/bin/activate
```

## Не коммитить в Git!

`.eco/` уже добавлена в `.gitignore`. Виртуальная среда не должна попадать в репозиторий.

Каждый разработчик создаёт свою собственную `.eco` локально.

## Размер и очистка

Типичный размер `.eco`: 100-300 MB

Для очистки места:
```bash
# Показать размер
du -sh .eco

# Очистить кэши
pip cache purge

# Пересоздать минимально
pip freeze > temp_requirements.txt
rm -rf .eco
python3 -m venv .eco
source .eco/bin/activate
pip install -r temp_requirements.txt
rm temp_requirements.txt
```

## Автоматизация

Добавьте в `.bashrc` или `.zshrc` для автоактивации:

```bash
# Auto-activate .eco when entering project directory
cd() {
    builtin cd "$@"
    if [[ -d ".eco" ]]; then
        source .eco/bin/activate 2>/dev/null
    fi
}
```

## Связь с Docker/Cloud Run

При деплое на Cloud Run:
- `.eco` игнорируется (`.gcloudignore`)
- Cloud Run использует `requirements.txt` для установки зависимостей
- Buildpack создаёт свою виртуальную среду в контейнере
- `.eco` остаётся только для локальной разработки

---

**Создано**: Автоматически при первичной настройке проекта
**Обновлено**: При установке новых зависимостей через `pip install`
**Не коммитить**: Добавлено в `.gitignore`
