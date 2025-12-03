@echo off
REM Скрипт для инициализации проекта

echo ===================================
echo Инициализация проекта
echo ===================================
echo.

REM Создаем виртуальное окружение
if not exist venv (
    echo Создаю виртуальное окружение...
    python -m venv venv
    if errorlevel 1 (
        echo Ошибка: Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
    echo ✓ Виртуальное окружение создано
)

REM Активируем виртуальное окружение
echo Активирую виртуальное окружение...
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo.
echo Устанавливаю зависимости...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo Ошибка: Не удалось установить зависимости
    pause
    exit /b 1
)

echo.
echo ✓ Проект инициализирован успешно!
echo.
echo Следующие шаги:
echo 1. Запустите: python src/main.py
echo 2. Выполните конфигурацию через интерактивное меню
echo 3. Инициализируйте БД: python init_db.py
echo 4. Снова запустите бота: python src/main.py
echo.
pause
