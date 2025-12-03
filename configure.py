#!/usr/bin/env python3
"""
Интерактивный конфигуратор для .env файла
"""

import os
from pathlib import Path

def configure_bot():
    """Interactive configuration"""
    env_file = Path(__file__).parent / ".env"
    
    print("\n" + "="*60)
    print("⚙️  КОНФИГУРАТОР TELEGRAM БОТА")
    print("="*60 + "\n")
    
    print("📝 Введите необходимые значения")
    print("(нажмите Enter чтобы пропустить)\n")
    
    # Получить токен
    print("1️⃣  TELEGRAM BOT TOKEN")
    print("   Как получить: https://t.me/BotFather → /newbot")
    print("   (скопируй токен и вставь сюда)")
    token = input("Token: ").strip()
    
    if not token:
        print("⚠️  Токен не введен. Используем значение из .env")
    
    # Получить Admin ID
    print("\n2️⃣  ADMIN ID")
    print("   Как получить: напиши боту @userinfobot и скопируй свой ID")
    admin_id = input("Admin ID: ").strip()
    
    # Получить Google Spreadsheet ID
    print("\n3️⃣  GOOGLE SPREADSHEET ID")
    print("   Из URL: https://docs.google.com/spreadsheets/d/{ID}/edit")
    sheet_id = input("Sheet ID: ").strip()
    
    # Получить Google Calendar ID
    print("\n4️⃣  GOOGLE CALENDAR ID")
    print("   Из: Google Calendar → Параметры → ID календаря")
    calendar_id = input("Calendar ID: ").strip()
    
    # Название салона
    print("\n5️⃣  НАЗВАНИЕ САЛОНА")
    salon_name = input("Salon Name (по умолчанию 'Tattoo Salon'): ").strip() or "Tattoo Salon"
    
    # Читаем текущий .env
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = ""
    
    # Обновляем значения
    if token:
        content = update_env_value(content, "TELEGRAM_BOT_TOKEN", token)
    if admin_id:
        content = update_env_value(content, "ADMIN_IDS", admin_id)
    if sheet_id:
        content = update_env_value(content, "GOOGLE_SPREADSHEET_ID", sheet_id)
    if calendar_id:
        content = update_env_value(content, "GOOGLE_CALENDAR_ID", calendar_id)
    if salon_name:
        content = update_env_value(content, "SALON_NAME", salon_name)
    
    # Сохраняем обновленный .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "="*60)
    print("✅ Конфигурация сохранена!")
    print("="*60 + "\n")
    
    if token:
        print("✨ Теперь вы можете запустить бота:")
        print("   python run_bot.py\n")
    else:
        print("⚠️  Токен не установлен. Бот не сможет запуститься.")
        print("   Установите TELEGRAM_BOT_TOKEN в .env и попробуйте снова\n")

def update_env_value(content: str, key: str, value: str) -> str:
    """Update or add environment variable in content"""
    lines = content.split('\n')
    found = False
    
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break
    
    if not found:
        # Добавить новую переменную перед комментарием о развитии
        for i, line in enumerate(lines):
            if "DEVELOPMENT" in line or "DEBUG" in line:
                lines.insert(i, f"{key}={value}")
                found = True
                break
        
        if not found:
            # Добавить в конец
            lines.append(f"{key}={value}")
    
    return '\n'.join(lines)

if __name__ == "__main__":
    try:
        configure_bot()
    except KeyboardInterrupt:
        print("\n\n❌ Конфигурация отменена")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
