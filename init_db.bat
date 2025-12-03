@echo off
REM Скрипт для инициализации полноценной БД в Google Sheets
REM Запустить init_database.py для создания структуры БД

echo.
echo ========================================
echo  DATABASE INITIALIZATION
echo ========================================
echo.

REM Проверить наличие .env файла
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please configure .env first
    pause
    exit /b 1
)

REM Проверить наличие credentials.json
if not exist "credentials.json" (
    echo ERROR: credentials.json not found!
    echo Please add Google credentials file
    pause
    exit /b 1
)

echo Initializing database structure...
echo.

REM Выполнить инициализацию
.\venv\Scripts\python.exe init_database.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: Database initialized!
    echo ========================================
    echo.
    echo Do you want to populate with sample data? (Y/N)
    set /p choice="Enter choice: "
    if /i "%choice%"=="Y" (
        .\venv\Scripts\python.exe populate_database.py
    )
) else (
    echo.
    echo ERROR: Database initialization failed!
    pause
    exit /b 1
)

pause
