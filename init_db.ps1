#!/usr/bin/env pwsh
# Скрипт для инициализации полноценной БД в Google Sheets

Write-Host ""
Write-Host "========================================"
Write-Host " DATABASE INITIALIZATION" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host ""

# Проверить наличие .env файла
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please configure .env first"
    Read-Host "Press Enter to exit"
    exit 1
}

# Проверить наличие credentials.json
if (-not (Test-Path "credentials.json")) {
    Write-Host "ERROR: credentials.json not found!" -ForegroundColor Red
    Write-Host "Please add Google credentials file"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Initializing database structure..."
Write-Host ""

# Выполнить инициализацию
& ".\venv\Scripts\python.exe" init_database.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "SUCCESS: Database initialized!" -ForegroundColor Green
    Write-Host "========================================"
    Write-Host ""
    
    $choice = Read-Host "Do you want to populate with sample data? (Y/N)"
    if ($choice -eq "Y" -or $choice -eq "y") {
        Write-Host ""
        & ".\venv\Scripts\python.exe" populate_database.py
    }
} else {
    Write-Host ""
    Write-Host "ERROR: Database initialization failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"
