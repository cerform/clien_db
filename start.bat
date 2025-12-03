@echo off
REM Telegram Bot для Тату-Салона
REM Быстрый старт

echo.
echo ====================================================================
echo         TELEGRAM BOT ДЛЯ ТАТУ-САЛОНА
echo ====================================================================
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.14 или выше.
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Проверяем виртуальное окружение
if exist venv (
    echo ✅ Виртуальное окружение найдено
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Виртуальное окружение не найдено!
    echo Создаем новое окружение...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ Окружение создано
)

echo.
echo Выбор действия:
echo 1. 🔧 Конфигурация (ввод токена и ID)
echo 2. 🚀 Запустить бота
echo 3. 📋 Показать инструкцию
echo 4. ❌ Выход
echo.

set /p choice="Введите номер (1-4): "

if "%choice%"=="1" (
    echo.
    echo Запускаем конфигуратор...
    python configure.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo Запускаем бота...
    python run_bot.py
    pause
) else if "%choice%"=="3" (
    echo.
    type QUICKSTART.txt
    pause
) else if "%choice%"=="4" (
    echo Выход...
    exit /b 0
) else (
    echo ❌ Некорректный выбор
    pause
)
