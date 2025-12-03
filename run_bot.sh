#!/bin/bash
# Скрипт для запуска бота на Linux/Mac

echo "==================================="
echo "Tattoo Bot Launcher"
echo "==================================="
echo ""

# Проверяем, активировано ли виртуальное окружение
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Активирую виртуальное окружение..."
    if [ -f venv/bin/activate ]; then
        source venv/bin/activate
    else
        echo "Ошибка: Виртуальное окружение не найдено!"
        echo "Пожалуйста, создайте его с помощью: python3 -m venv venv"
        exit 1
    fi
fi

echo ""
echo "Запуск бота..."
echo ""

python src/main.py
