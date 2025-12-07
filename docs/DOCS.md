# 📑 Индекс Документации

Быстрая справка по всей документации проекта.

---

## 🚀 ДЛЯ НАЧИНАЮЩИХ

**Вы новичок?** Начните здесь:

1. **[QUICKSTART.md](QUICKSTART.md)** - 5 минут до рабочего бота
   - Локальная установка
   - Cloud Run deployment
   - Первое сообщение

2. **[README.md](README.md)** - обзор проекта
   - Возможности
   - Стек технологий
   - Ключевые компоненты

3. **[STRUCTURE.md](STRUCTURE.md)** - карта проекта
   - Где что находится
   - Как устроен код
   - Ссылки на компоненты

---

## 📚 ОСНОВНАЯ ДОКУМЕНТАЦИЯ

### [INKA.md](INKA.md) - 🤖 AI-Ассистент
Всё о INKA AI и как её использовать.
- ❓ Что такое INKA?
- 🏗️ Архитектура
- 📖 Методы и примеры
- 💬 Примеры диалогов
- 🔌 Интеграция с другими сервисами
- 🐛 Проблемы и решения

### [DATABASE.md](DATABASE.md) - 📊 База Данных
Вся информация о БД, Sheets и Calendar.
- 🏛️ Архитектура БД
- 📋 Таблицы (masters, services, schedule, bookings, clients)
- 🔄 Синхронизация (Sheets ↔ Calendar)
- 💾 Инициализация и заполнение
- ✅ Валидация данных
- 🔍 Поиск через keyword matching

### [DEPLOYMENT.md](DEPLOYMENT.md) - 🚀 Cloud Run & CI/CD
Развёртывание, мониторинг, масштабирование.
- ⚡ Быстрый старт (3 команды)
- 🔐 Переменные окружения
- 🏗️ Архитектура развёртывания
- 🔄 CI/CD Pipeline
- 📊 Мониторинг и логирование
- 🔙 Откат версий
- 📈 Масштабирование

---

## 🔍 СПРАВОЧНЫЕ МАТЕРИАЛЫ

### [CLEANUP_REPORT.md](CLEANUP_REPORT.md) - 🧹 История Очистки
Что было удалено и почему.
- 📊 Статистика удалений
- 📁 До/После структура
- 🔄 Миграция со старых скриптов

### [STRUCTURE.md](STRUCTURE.md) - 🗺️ Карта Проекта
Полная карта всего кода и структуры.
- 📂 Структура файлов
- 🎯 Ключевые компоненты
- 📊 Данные в Sheets
- ⚡ Быстрые команды

---

## 👩‍💻 ДЛЯ РАЗРАБОТЧИКОВ

### Быстрые ссылки на код

| Компонент | Файл | Описание |
|-----------|------|---------|
| **INKA AI** | `src/ai/advanced_inka.py` | Главный LLM класс |
| **DataSync** | `src/services/data_sync.py` | Унифицированный доступ к данным |
| **Bot Handler** | `src/bot/handlers/client_handler.py` | Маршрутизация сообщений |
| **Sheets Client** | `src/db/sheets_client.py` | Google Sheets API |
| **Calendar Init** | `src/calendars/calendar_init.py` | Google Calendar API |
| **Config** | `src/config/config.py` | Конфигурация |
| **Entry Point** | `run_production.py` | Главный файл приложения |

### Команды разработки

```bash
# Локальный запуск
python -u run_production.py

# Тестирование
python test_send_message.py         # Webhook тест
python test_unified_sync.py         # Тест синхронизации
python pre_deploy_check.py          # Предпроверка

# Операции с БД
python init_database.py             # Создание схемы
python populate_real_data.py        # Заполнение данными
python add_data.py                  # Добавить записи
python fix_schedule.py              # Исправить расписание

# Cloud Run
gcloud run deploy telegram-bot --source . --region us-central1 --quiet

# Логи
gcloud logging read "resource.service.name=telegram-bot" --limit 100
```

---

## ❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ

### "Как быстро начать?"
→ [QUICKSTART.md](QUICKSTART.md) (5 минут)

### "Как работает INKA?"
→ [INKA.md](INKA.md) - раздел "Архитектура" + "Примеры диалогов"

### "Где данные хранятся?"
→ [DATABASE.md](DATABASE.md) - раздел "Архитектура"

### "Как развернуть в Cloud Run?"
→ [DEPLOYMENT.md](DEPLOYMENT.md) - раздел "Быстрый старт"

### "Как найти мастера по стилю?"
→ [DATABASE.md](DATABASE.md) - раздел "Поиск в INKA"

### "Как мониторить логи?"
→ [DEPLOYMENT.md](DEPLOYMENT.md) - раздел "Логи"

### "Что удалили при очистке?"
→ [CLEANUP_REPORT.md](CLEANUP_REPORT.md)

### "Где что находится в коде?"
→ [STRUCTURE.md](STRUCTURE.md)

---

## 🎯 ТОЧКИ ВХОДА ПО СЦЕНАРИЮ

### Сценарий: "Я новичок, хочу понять проект"
```
1. README.md (обзор)
2. QUICKSTART.md (локальный запуск)
3. STRUCTURE.md (навигация по коду)
4. INKA.md (понимание AI)
5. DATABASE.md (данные)
```

### Сценарий: "Я хочу развернуть в production"
```
1. QUICKSTART.md (локально сначала)
2. DATABASE.md (если нужны данные)
3. DEPLOYMENT.md (Cloud Run)
4. Запустить pre_deploy_check.py
5. gcloud run deploy...
```

### Сценарий: "Бот не работает"
```
1. python pre_deploy_check.py
2. python test_send_message.py
3. Смотреть логи:
   gcloud logging read "resource.service.name=telegram-bot" --limit 50
4. Если дело в INKA: читать INKA.md раздел "Проблемы и решения"
5. Если дело в БД: читать DATABASE.md раздел "Проблемы и решения"
```

### Сценарий: "Я добавляю новго мастера"
```
1. DATABASE.md - раздел "Инициализация БД"
2. python add_data.py (добавить в таблицу masters)
3. python add_schedule.py (добавить расписание)
4. python test_unified_sync.py (проверить синхронизацию)
```

---

## 📊 ДОКУМЕНТАЦИЯ ПО КОМПОНЕНТАМ

### Google APIs
- **Google Sheets**: [DATABASE.md](DATABASE.md) - раздел "Google Sheets"
- **Google Calendar**: [DATABASE.md](DATABASE.md) - раздел "Интеграция Календаря"
- **OpenAI**: [INKA.md](INKA.md) - раздел "Архитектура"

### Развёртывание
- **Cloud Run**: [DEPLOYMENT.md](DEPLOYMENT.md) - раздел "Архитектура"
- **CI/CD**: [DEPLOYMENT.md](DEPLOYMENT.md) - раздел "Pipeline CI/CD"
- **Docker**: [DEPLOYMENT.md](DEPLOYMENT.md) - раздел "Требования"

### Тестирование
- **Pre-deploy check**: `python pre_deploy_check.py`
- **Unit tests**: `python test_unified_sync.py`
- **Integration test**: `python test_send_message.py`
- **Health check**: `python health_check.py`

---

## 🔗 ВНЕШНИЕ ССЫЛКИ

- 📌 [Google Sheets с данными](https://docs.google.com/spreadsheets/d/17mB1AFzy2lr2x3j9uSWEOOG4lzAStMChkHwPQFLzjoQ)
- 🤖 [OpenAI Assistant (asst_LBGeLxauJ3nYbauR3pilbifN)](https://platform.openai.com/assistants)
- 🌐 [GitHub Repository](https://github.com/cerform/clien_db)
- ☁️ [Google Cloud Console](https://console.cloud.google.com)
- 📖 [Aiogram Documentation](https://docs.aiogram.dev)
- 📚 [Google Sheets API Docs](https://developers.google.com/sheets/api)
- 📅 [Google Calendar API Docs](https://developers.google.com/calendar/api)

---

## 📈 ДОРОЖНАЯ КАРТА

### ✅ Текущее состояние (v1.0)
- Production ready
- INKA работает
- Calendar синхронизирован
- Проект очищен от дубликатов

### 🚀 Будущие улучшения
- [ ] Multi-language support (EN, HE)
- [ ] SMS/Email confirmations
- [ ] Payment system integration
- [ ] Telegram inline buttons
- [ ] Client ratings & feedback
- [ ] Advanced analytics

---

**Последнее обновление**: 2025-12-05  
**Версия**: v1.0 Clean  
**Статус**: ✅ Production Ready

*Начните с [QUICKSTART.md](QUICKSTART.md) или [README.md](README.md)*
