# 🚀 Quick Start - Tattoo Bot (после деплоя)

## ✅ Что уже сделано

- Cloud SQL PostgreSQL instance создан и настроен
- База данных `tattoo_salon` с таблицами masters, clients, bookings
- RBAC система: SuperAdmin, Admin, Master, INKA
- User Manager для создания пользователей
- Cloud Run деплой с webhook
- Все секреты настроены в Secret Manager

## 📋 Следующие 3 шага

### 1️⃣ Настроить Telegram Webhook

```bash
cd /home/etcsys/projects/clien_db
./scripts/setup_webhook.sh
```

Это автоматически:
- Получит URL сервиса из Cloud Run
- Настроит webhook в Telegram
- Покажет статус webhook

### 2️⃣ Обновить Telegram ID суперадмина

**Сейчас:** Username: `владимир_петров`, Password: `KJALT3tinwn-S_aU`, Telegram ID: `123456789` (тестовый)

**Получите свой реальный ID:**
1. Откройте бота [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте любое сообщение
3. Скопируйте ваш ID (например, 987654321)

**Обновите в БД:**
```bash
# Запустите Cloud SQL Proxy (если еще не запущен)
./cloud_sql_proxy -instances=tattoo-480007:us-central1:tattoo-db=tcp:5432 &

# Обновите Telegram ID
source .venv/bin/activate
export DATABASE_URL="postgresql://tattoo_user:AdNICZWTcyqwT6Jn9EEg4VEXXQUP4l17HdUnz+E/2xM=@localhost:5432/tattoo_salon"

python3 -c "
from src.services.user_manager import UserManager
manager = UserManager()
manager.sql_client.execute_query(
    'UPDATE masters SET telegram_id = %s WHERE username = %s',
    ('ВАШ_РЕАЛЬНЫЙ_ID', 'владимир_петров')
)
print('✅ Telegram ID обновлен!')
"
```

### 3️⃣ Протестировать бота

Отправьте `/start` вашему боту в Telegram.

**Ожидаемый результат:**
```
👑 Привет, СуперАдмин Владимир Петров!

У вас полный доступ ко всем функциям:

🔹 Админ-панель: /admin
🔹 Управление мастерами (приём/увольнение)
🔹 Управление клиентами и записями
🔹 Все календари мастеров
🔹 Мониторинг и тесты
🔹 Управление БД
🔹 Setup Wizard

Чем могу помочь?
```

---

## 🔧 Создание других пользователей

### Создать админа
```bash
python3 scripts/create_user.py admin \
  --name "Анна Иванова" \
  --phone "+972502222222" \
  --telegram-id "987654321"
```

### Создать мастера
```bash
python3 scripts/create_user.py master \
  --name "Мария Сидорова" \
  --phone "+972503333333" \
  --telegram-id "111222333"
```

### Список пользователей
```bash
python3 scripts/create_user.py list
```

### Изменить роль
```bash
python3 scripts/create_user.py update-role \
  --master-id "abc-123" --role admin
```

### Уволить (деактивировать)
```bash
python3 scripts/create_user.py deactivate --master-id "abc-123"
```

---

## 📊 Проверка системы

### Статус Cloud Run
```bash
gcloud run services describe telegram-bot --region=us-central1
```

### Логи
```bash
gcloud run services logs read telegram-bot --region=us-central1 --limit=50
```

### Webhook статус
```bash
# Получите bot token
BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token)

# Проверьте webhook
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool
```

### Проверка БД
```bash
source .venv/bin/activate
export DATABASE_URL="postgresql://tattoo_user:AdNICZWTcyqwT6Jn9EEg4VEXXQUP4l17HdUnz+E/2xM=@localhost:5432/tattoo_salon"

python3 -c "
from src.services.user_manager import UserManager
manager = UserManager()
users = manager.list_all_users()
print(f'Всего пользователей: {len(users)}')
for user in users:
    print(f\"  - {user['name']}: {user['role']} (telegram_id: {user.get('telegram_id', 'не указан')})\")
"
```

---

## 🐛 Troubleshooting

### Бот не отвечает
```bash
# 1. Проверить webhook
./scripts/setup_webhook.sh

# 2. Проверить логи
gcloud run services logs read telegram-bot --region=us-central1 --limit=50

# 3. Проверить что сервис запущен
gcloud run services describe telegram-bot --region=us-central1 --format="value(status.url)"
```

### Ошибка "Permission denied"
```bash
# Проверить IAM права service account
gcloud projects get-iam-policy tattoo-480007 | grep telegram-bot-sa
```

### "User not found" при /start
```bash
# Проверить что ваш Telegram ID в БД
python3 scripts/create_user.py list
```

---

## 📁 Важные файлы

- `DEPLOYMENT_COMPLETE.md` - полная документация деплоя
- `README.md` - общее описание проекта
- `scripts/create_user.py` - CLI для управления пользователями
- `scripts/predeploy_checks.sh` - проверки перед деплоем
- `scripts/setup_webhook.sh` - настройка webhook
- `src/auth/roles.py` - RBAC система
- `src/services/user_manager.py` - User Manager

---

## 📞 Информация о проекте

- **Project ID:** tattoo-480007
- **Region:** us-central1
- **Cloud SQL Instance:** tattoo-db
- **Database:** tattoo_salon
- **User:** tattoo_user
- **Cloud Run Service:** telegram-bot
- **Service Account:** telegram-bot-sa@tattoo-480007.iam.gserviceaccount.com

---

**✅ Готово! Следуйте трём шагам выше для запуска.**
