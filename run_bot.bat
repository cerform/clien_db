@echo off
REM Скрипт для запуска бота на Windows

echo ===================================
echo Tattoo Bot Launcher
echo ===================================
echo.

REM Проверяем, активировано ли виртуальное окружение
if not defined VIRTUAL_ENV (
    echo Активирую виртуальное окружение...
    if exist venv\Scripts\activate.bat (
        call venv\Scripts\activate.bat
    ) else (
        echo Ошибка: Виртуальное окружение не найдено!
        echo Пожалуйста, создайте его с помощью: python -m venv venv
        pause
        exit /b 1
    )
)

echo.
echo Запуск бота...
echo.

python src/main.py

pause
