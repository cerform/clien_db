#!/usr/bin/env pwsh
# Telegram Bot для Тату-Салона
# Быстрый старт (PowerShell версия)

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "         TELEGRAM BOT ДЛЯ ТАТУ-САЛОНА" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# Проверяем Python
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "✅ Python найден: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден! Установите Python 3.14 или выше." -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем виртуальное окружение
if (Test-Path "venv") {
    Write-Host "✅ Виртуальное окружение найдено" -ForegroundColor Green
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  Виртуальное окружение не найдено!" -ForegroundColor Yellow
    Write-Host "Создаем новое окружение..." -ForegroundColor Yellow
    python -m venv venv
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "✅ Окружение создано" -ForegroundColor Green
}

Write-Host ""
Write-Host "Выбор действия:" -ForegroundColor Cyan
Write-Host "1. 🔧 Конфигурация (ввод токена и ID)" -ForegroundColor White
Write-Host "2. 🚀 Запустить бота" -ForegroundColor White
Write-Host "3. 📋 Показать инструкцию" -ForegroundColor White
Write-Host "4. ❌ Выход" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Введите номер (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Запускаем конфигуратор..." -ForegroundColor Cyan
        python configure.py
        Read-Host "Нажмите Enter для выхода"
    }
    "2" {
        Write-Host ""
        Write-Host "Запускаем бота..." -ForegroundColor Cyan
        python run_bot.py
    }
    "3" {
        Write-Host ""
        Get-Content QUICKSTART.txt
        Read-Host "Нажмите Enter для выхода"
    }
    "4" {
        Write-Host "Выход..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "❌ Некорректный выбор" -ForegroundColor Red
        Read-Host "Нажмите Enter для выхода"
    }
}
