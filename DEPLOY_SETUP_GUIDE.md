# 🚀 Руководство по настройке деплоя на Google Cloud Run

## 📝 Что нужно подготовить

### 1. Telegram Bot Token
1. Откройте Telegram
2. Найдите бота @BotFather
3. Отправьте команду `/newbot`
4. Следуйте инструкциям для создания бота
5. Скопируйте полученный токен (формат: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Admin ID (ваш Telegram ID)
1. Откройте Telegram
2. Найдите бота @userinfobot
3. Отправьте ему любое сообщение
4. Скопируйте ваш ID (числовое значение)

### 3. Google Sheets Spreadsheet ID
1. Создайте новую таблицу в Google Sheets
2. Из URL скопируйте ID: `https://docs.google.com/spreadsheets/d/{ЭТО_ID}/edit`
3. Пример: если URL `https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit`, то ID = `1ABC...XYZ`

### 4. Google Service Account Credentials
Это будет создано автоматически при деплое, но вам нужно иметь Google Cloud аккаунт.

---

## 🔧 Способ 1: Автоматический деплой (рекомендуется)

### Шаг 1: Авторизация в Google Cloud
```bash
export PATH=$PATH:/home/etcsys/google-cloud-sdk/bin
gcloud auth login
```
Это откроет браузер для входа в Google аккаунт.

### Шаг 2: Создать или выбрать проект
```bash
# Создать новый проект (замените your-project-id на свое)
gcloud projects create your-tattoo-bot-12345

# ИЛИ использовать существующий
gcloud config set project your-existing-project-id
```

**Важно:** Project ID должен быть уникальным и содержать только буквы, цифры и дефисы.

### Шаг 3: Запустить скрипт деплоя
```bash
cd /home/etcsys/projects/clien_db

# Запустить деплой (замените your-project-id)
./deploy.sh your-project-id us-central1
```

Скрипт запросит:
- ✅ Telegram Bot Token
- ✅ Google Sheets Spreadsheet ID
- ✅ Автоматически создаст Service Account
- ✅ Настроит все секреты
- ✅ Соберет и задеплоит приложение

### Шаг 4: Предоставить доступ к Google Sheets
Когда скрипт попросит, вам нужно:
1. Открыть вашу Google Sheets таблицу
2. Нажать кнопку "Настройки доступа" (Share)
3. Добавить email Service Account (формат: `telegram-bot-sheets-sa@your-project-id.iam.gserviceaccount.com`)
4. Дать права "Редактор"
5. Нажать "Готово"

---

## 🛠️ Способ 2: Ручная настройка (для опытных)

### 1. Включить необходимые API
```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com
```

### 2. Создать секреты
```bash
# Telegram Bot Token
echo -n "YOUR_BOT_TOKEN" | gcloud secrets create telegram-bot-token \
    --data-file=- \
    --replication-policy="automatic"

# Google Sheets ID
echo -n "YOUR_SPREADSHEET_ID" | gcloud secrets create google-sheets-id \
    --data-file=- \
    --replication-policy="automatic"
```

### 3. Создать Service Account для Google Sheets
```bash
PROJECT_ID="your-project-id"
SHEETS_SA_NAME="telegram-bot-sheets-sa"

# Создать Service Account
gcloud iam service-accounts create $SHEETS_SA_NAME \
    --display-name="Telegram Bot Google Sheets Service Account"

# Создать ключ
gcloud iam service-accounts keys create credentials.json \
    --iam-account="${SHEETS_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Создать секрет для credentials
gcloud secrets create google-credentials \
    --data-file=credentials.json \
    --replication-policy="automatic"

# Дать права
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SHEETS_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/editor"
```

### 4. Создать Service Account для Cloud Run
```bash
SA_NAME="telegram-bot-sa"

gcloud iam service-accounts create $SA_NAME \
    --display-name="Telegram Bot Service Account"

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Дать права на доступ к секретам
for SECRET in telegram-bot-token google-sheets-id google-credentials; do
    gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/secretmanager.secretAccessor"
done
```

### 5. Собрать и задеплоить
```bash
# Собрать образ
gcloud builds submit --tag gcr.io/$PROJECT_ID/telegram-bot

# Задеплоить в Cloud Run
gcloud run deploy telegram-bot \
    --image gcr.io/$PROJECT_ID/telegram-bot \
    --platform managed \
    --region us-central1 \
    --service-account $SA_EMAIL \
    --set-secrets=TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,GOOGLE_SPREADSHEET_ID=google-sheets-id:latest,GOOGLE_CREDENTIALS=google-credentials:latest \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10
```

---

## 🧪 Способ 3: Локальное тестирование (перед деплоем)

### 1. Настроить локальный .env
```bash
# Активировать venv
source venv/bin/activate

# Запустить конфигуратор
python configure.py
```

Введите:
- Telegram Bot Token
- Admin ID
- Google Sheets Spreadsheet ID

### 2. Получить Google Credentials локально
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com)
2. Создайте проект или выберите существующий
3. Включите Google Sheets API
4. Создайте Service Account
5. Создайте ключ и скачайте как `credentials.json`
6. Поместите в корень проекта

### 3. Инициализировать БД
```bash
python init_db.py
```

### 4. Запустить бота локально
```bash
python src/main.py
```

---

## ✅ Проверка после деплоя

### 1. Проверить статус сервиса
```bash
gcloud run services describe telegram-bot --region us-central1
```

### 2. Посмотреть логи
```bash
gcloud run services logs read telegram-bot --region us-central1
```

### 3. Протестировать бота
1. Откройте Telegram
2. Найдите своего бота по username
3. Отправьте `/start`
4. Проверьте работу команд

---

## 🔧 Обновление бота

После изменений в коде:
```bash
# Пересобрать и задеплоить
./deploy.sh your-project-id us-central1
```

Или вручную:
```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/telegram-bot
gcloud run deploy telegram-bot \
    --image gcr.io/$PROJECT_ID/telegram-bot \
    --region us-central1
```

---

## ❓ Часто встречающиеся проблемы

### "Project ID already exists"
Выберите другой уникальный ID для проекта.

### "Permission denied"
Убедитесь, что вы авторизованы: `gcloud auth login`

### "API not enabled"
Включите необходимые API:
```bash
gcloud services enable run.googleapis.com
```

### Бот не отвечает
1. Проверьте логи: `gcloud run services logs read telegram-bot`
2. Проверьте секреты: убедитесь, что токен правильный
3. Проверьте Google Sheets доступ: Service Account должен иметь права

---

## 📊 Мониторинг и стоимость

### Просмотр метрик
```bash
gcloud run services describe telegram-bot --region us-central1
```

### Примерная стоимость
- **Cloud Run**: бесплатный tier - 2 млн запросов/месяц
- **Secret Manager**: $0.06 за секрет в месяц
- **Container Registry**: от $0.026/GB в месяц

Для небольшого бота расходы обычно < $5/месяц.

---

## 🎯 Быстрый старт (3 команды)

```bash
# 1. Авторизация
gcloud auth login

# 2. Создать проект
gcloud projects create my-tattoo-bot-123

# 3. Деплой
cd /home/etcsys/projects/clien_db
./deploy.sh my-tattoo-bot-123 us-central1
```

После этого следуйте инструкциям скрипта!
