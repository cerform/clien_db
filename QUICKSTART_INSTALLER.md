# 🚀 One-Click Installer для Tattoo Bot

## Для администратора салона (без знания программирования)

### Шаг 1: Запустить установщик

```bash
./tools/easy_install.sh
```

Скрипт попросит у вас:
1. ✅ Google API Key (для календаря и таблиц)
2. ✅ OpenAI API Key (для INKA AI ассистента)
3. ✅ Telegram Bot Token (от @BotFather)
4. ✅ Имя проекта в Google Cloud

### Шаг 2: Автоматическая установка

Скрипт автоматически:
- ☁️ Создаст Cloud Run инстанс
- 🗄️ Настроит PostgreSQL базу данных
- 🔐 Сохранит все ключи в Secret Manager
- 🌐 Даст вам ссылку на веб-установщик

### Шаг 3: Веб-конфигурация

По ссылке откроется веб-интерфейс где вы:
1. Укажете название салона
2. Выберете часовой пояс
3. Добавите мастеров
4. Настроите расписание
5. Протестируете бота

### Шаг 4: Готово!

В конце получите:
- 🤖 Работающий Telegram бот
- 📊 Админ-панель
- 🎨 AI ассистент (INKA)
- 📅 Интеграция с Google Calendar

## Техническая информация

Установщик создаёт:
- Cloud Run service (https://your-bot.run.app)
- Cloud SQL PostgreSQL database
- Secret Manager secrets
- Service Account с правами

## Что нужно перед установкой

1. **Google Cloud Account** - [создать бесплатно](https://cloud.google.com/free)
2. **Telegram Bot** - создать через [@BotFather](https://t.me/botfather)
3. **OpenAI API Key** - [получить здесь](https://platform.openai.com/api-keys)

## Поддержка

Если что-то пошло не так:
- Проверьте логи: `./tools/check_logs.sh`
- Перезапустите: `./tools/restart.sh`
- Полная переустановка: `./tools/reinstall.sh`
