# ✅ Tests - Тестирование

Unit & Integration тесты для всего приложения.

## 📋 Тесты

### `pre_deploy_check.py`
**Цель**: Проверка готовности к деплою

**Проверяет** (8 проверок):
1. ✅ Файлы существуют
2. ✅ Python синтаксис
3. ✅ requirements.txt
4. ✅ Docker конфигурация
5. ✅ Config загружается
6. ✅ Database подключается
7. ✅ OpenAI API работает
8. ✅ Code quality (pylint)

**Использование**:
```bash
python tests/pre_deploy_check.py
```

**Результат**:
```
✅ ALL CHECKS PASSED (8/8)
Ready for deployment!
```

**Когда запускать**: ВСЕГДА перед деплоем!

---

### `test_send_message.py`
**Цель**: Тест webhook - отправить сообщение боту

**Что тестирует**:
- HTTP POST /webhook работает
- Бот получает сообщение
- Ответ приходит обратно

**Использование**:
```bash
# 1. В одном терминале запустить бота
python -u run_production.py

# 2. В другом терминале
python tests/test_send_message.py
```

**Результат**:
```
Status: 200
✅ Message sent successfully!
```

**Когда запускать**: При тестировании webhook локально

---

### `test_unified_sync.py`
**Цель**: Тест синхронизации данных

**Что тестирует**:
- DataSyncService работает
- Masters загружаются (3 мастера)
- Services загружаются (8 услуг)
- Поиск по ключевому слову работает
- Доступные слоты вычисляются правильно

**Использование**:
```bash
pytest tests/test_unified_sync.py -v
```

**Результат**:
```
test_masters ✓
test_services ✓
test_search_masters ✓
test_available_slots ✓
====== 4 passed in 2.45s ======
```

**Когда запускать**: При изменении DataSync или структуры данных

---

## 🚀 Запуск тестов

### Все тесты (pytest)
```bash
# Все тесты в папке
pytest tests/ -v

# С coverage
pytest tests/ --cov=src --cov-report=html
```

### Конкретный тест
```bash
# Только синхронизацию
pytest tests/test_unified_sync.py -v

# Только один метод
pytest tests/test_unified_sync.py::test_masters -v
```

### Предпроверка (перед деплоем)
```bash
# ВСЕГДА перед деплоем!
python tests/pre_deploy_check.py
```

---

## 🛠️ Структура теста

```python
# tests/test_example.py

import pytest
from src.services.data_sync import get_data_sync_service

def test_example():
    """Описание теста"""
    # Arrange - подготовка
    sync = get_data_sync_service()
    
    # Act - выполнение
    masters = sync.get_masters()
    
    # Assert - проверка
    assert len(masters) == 3
    assert masters[0]['name'] == 'Анна Леви'
```

---

## 📊 Coverage

```bash
# Посмотреть coverage
pytest tests/ --cov=src --cov-report=term-missing

# HTML report
pytest tests/ --cov=src --cov-report=html
# Откроется: htmlcov/index.html
```

---

## 🔄 CI/CD Integration

Тесты автоматически запускаются:

1. **Локально** (перед коммитом): `pre-commit hook`
2. **На сервере** (при push): `GitHub Actions` / `Cloud Build`
3. **Перед деплоем**: `pre_deploy_check.py`

---

## 🐛 Решение проблем

**Проблема**: `ModuleNotFoundError: No module named 'src'`
**Решение**: Убедитесь что запускаете из корня проекта

**Проблема**: `Database connection failed`
**Решение**: Проверить:
1. GOOGLE_SPREADSHEET_ID в .env
2. GOOGLE_CREDENTIALS_JSON установлен
3. Service Account имеет доступ

**Проблема**: `test_send_message.py: Connection refused`
**Решение**: Убедитесь что `run_production.py` запущен

---

## ✅ Чек-лист перед деплоем

- [ ] `python tests/pre_deploy_check.py` - все pass
- [ ] `pytest tests/ -v` - все pass
- [ ] `python tests/test_send_message.py` - работает
- [ ] Логи выглядят нормально
- [ ] `git status` - все commited
- [ ] `git log --oneline -5` - commits make sense

---

**Статус**: ✅ Production Ready
