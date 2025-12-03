#!/usr/bin/env python3
"""
Telegram Bot для Тату-Салона
Главный файл с интерактивным меню конфигурации
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Добавляем parent directory в path
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Dispatcher, Router
from aiogram.types import BotCommand
from src.config.logging_config import setup_logging
from src.config import get_config, Config, set_config
from src.bot.loader import init_bot, get_dispatcher
from src.bot.handlers import start_handler, client_handler, master_handler, admin_handler
from src.bot.handlers import admin_panel

logger = logging.getLogger(__name__)

class BotSetup:
    """Interactive bot setup utility"""
    
    def __init__(self):
        self.env_file = Path(__file__).parent / ".env"
        self.credentials_file = Path(__file__).parent / "credentials.json"
    
    def print_header(self):
        """Print header"""
        print("\n" + "="*60)
        print("🤖 Telegram Bot для Тату-Салона")
        print("="*60 + "\n")
    
    def print_menu(self):
        """Print main menu"""
        print("\n📋 Главное меню:")
        print("1. ⚙️  Конфигурация")
        print("2. ✅ Запустить бота")
        print("3. ❌ Выход")
        print()
    
    def print_config_menu(self):
        """Print configuration menu"""
        print("\n⚙️  Конфигурация:")
        print("1. 🔐 Telegram Bot Token")
        print("2. 📊 Google Spreadsheet ID")
        print("3. 🔑 Google Credentials JSON")
        print("4. 🌍 Timezone")
        print("5. 👤 Admin IDs")
        print("6. 🔙 Назад")
        print()
    
    def read_env_file(self) -> dict:
        """Read environment variables from .env file"""
        env_vars = {}
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    
    def write_env_file(self, env_vars: dict):
        """Write environment variables to .env file"""
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write("# Telegram Bot\n")
            f.write(f"TELEGRAM_BOT_TOKEN={env_vars.get('TELEGRAM_BOT_TOKEN', '')}\n\n")
            
            f.write("# Google API\n")
            f.write(f"GOOGLE_SPREADSHEET_ID={env_vars.get('GOOGLE_SPREADSHEET_ID', '')}\n")
            f.write(f"GOOGLE_CREDENTIALS_JSON={env_vars.get('GOOGLE_CREDENTIALS_JSON', 'credentials.json')}\n\n")
            
            f.write("# Settings\n")
            f.write(f"TIMEZONE={env_vars.get('TIMEZONE', 'Europe/Moscow')}\n")
            f.write(f"LOG_LEVEL={env_vars.get('LOG_LEVEL', 'INFO')}\n\n")
            
            f.write("# Admin settings\n")
            f.write(f"ADMIN_IDS={env_vars.get('ADMIN_IDS', '')}\n")
        
        print(f"✅ Файл {self.env_file} сохранен")
    
    def configure_token(self, env_vars: dict):
        """Configure Telegram bot token"""
        print("\n🔐 Введите Telegram Bot Token")
        print("Получить токен можно у BotFather в Telegram (@BotFather)")
        token = input("Token: ").strip()
        
        if token and (token.startswith(('123', '456', '789')) or ':' in token):
            env_vars['TELEGRAM_BOT_TOKEN'] = token
            print("✅ Token сохранен")
        else:
            print("❌ Некорректный формат токена")
    
    def configure_spreadsheet_id(self, env_vars: dict):
        """Configure Google Spreadsheet ID"""
        print("\n📊 Введите Google Spreadsheet ID")
        print("ID находится в URL таблицы: https://docs.google.com/spreadsheets/d/{ID}/edit")
        spreadsheet_id = input("Spreadsheet ID: ").strip()
        
        if spreadsheet_id and len(spreadsheet_id) > 20:
            env_vars['GOOGLE_SPREADSHEET_ID'] = spreadsheet_id
            print("✅ Spreadsheet ID сохранен")
        else:
            print("❌ ID кажется некорректным (слишком короткий)")
    
    def configure_credentials(self, env_vars: dict):
        """Configure Google Credentials"""
        print("\n🔑 Конфигурация Google Credentials")
        print("1. Используется существующий credentials.json")
        print("2. Указать другой путь к файлу")
        
        choice = input("Выбор (1-2): ").strip()
        
        if choice == "1":
            if self.credentials_file.exists():
                env_vars['GOOGLE_CREDENTIALS_JSON'] = 'credentials.json'
                print("✅ Используется файл credentials.json")
            else:
                print("❌ Файл credentials.json не найден")
                print("📖 Инструкция:")
                print("1. Перейдите на https://console.cloud.google.com")
                print("2. Создайте новый проект")
                print("3. Включите Google Sheets API и Google Calendar API")
                print("4. Создайте Service Account и скачайте JSON файл")
                print("5. Сохраните файл как credentials.json в директории проекта")
        elif choice == "2":
            path = input("Путь к credentials.json: ").strip()
            if Path(path).exists():
                env_vars['GOOGLE_CREDENTIALS_JSON'] = path
                print("✅ Путь сохранен")
            else:
                print("❌ Файл не найден")
    
    def configure_timezone(self, env_vars: dict):
        """Configure timezone"""
        print("\n🌍 Выберите временную зону:")
        timezones = [
            "Europe/Moscow",
            "Europe/London",
            "America/New_York",
            "Asia/Tokyo",
            "Australia/Sydney"
        ]
        
        for i, tz in enumerate(timezones, 1):
            print(f"{i}. {tz}")
        print(f"{len(timezones) + 1}. Другое (указать вручную)")
        
        choice = input("Выбор: ").strip()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(timezones):
                env_vars['TIMEZONE'] = timezones[idx]
            else:
                tz = input("Введите временную зону: ").strip()
                env_vars['TIMEZONE'] = tz
            print(f"✅ Временная зона: {env_vars['TIMEZONE']}")
        except ValueError:
            print("❌ Некорректный выбор")
    
    def configure_admin_ids(self, env_vars: dict):
        """Configure admin IDs"""
        print("\n👤 Введите Telegram IDs администраторов")
        print("Получить свой ID можно у бота @userinfobot в Telegram")
        print("Разделяйте несколько ID запятыми")
        
        admin_ids = input("Admin IDs (например: 123456789,987654321): ").strip()
        
        if admin_ids:
            env_vars['ADMIN_IDS'] = admin_ids
            print("✅ Admin IDs сохранены")
        else:
            print("⚠️  Admin IDs не установлены")
    
    def show_config(self, env_vars: dict):
        """Show current configuration"""
        print("\n📋 Текущая конфигурация:")
        print(f"🔐 Bot Token: {'✅ Установлен' if env_vars.get('TELEGRAM_BOT_TOKEN') else '❌ Не установлен'}")
        print(f"📊 Spreadsheet ID: {'✅ Установлен' if env_vars.get('GOOGLE_SPREADSHEET_ID') else '❌ Не установлен'}")
        print(f"🔑 Credentials: {'✅ Установлены' if Path(env_vars.get('GOOGLE_CREDENTIALS_JSON', 'credentials.json')).exists() else '❌ Не найдены'}")
        print(f"🌍 Timezone: {env_vars.get('TIMEZONE', 'Europe/Moscow')}")
        print(f"👤 Admin IDs: {env_vars.get('ADMIN_IDS', 'Не установлены')}")
    
    def validate_config(self, env_vars: dict) -> bool:
        """Validate configuration"""
        if not env_vars.get('TELEGRAM_BOT_TOKEN'):
            print("❌ Telegram Bot Token не установлен")
            return False
        
        if not env_vars.get('GOOGLE_SPREADSHEET_ID'):
            print("❌ Google Spreadsheet ID не установлен")
            return False
        
        creds_path = env_vars.get('GOOGLE_CREDENTIALS_JSON', 'credentials.json')
        if not Path(creds_path).exists():
            print(f"❌ Файл credentials не найден: {creds_path}")
            return False
        
        return True
    
    def run_configuration_menu(self):
        """Run configuration menu"""
        env_vars = self.read_env_file()
        
        while True:
            self.print_config_menu()
            choice = input("Выбор: ").strip()
            
            if choice == "1":
                self.configure_token(env_vars)
            elif choice == "2":
                self.configure_spreadsheet_id(env_vars)
            elif choice == "3":
                self.configure_credentials(env_vars)
            elif choice == "4":
                self.configure_timezone(env_vars)
            elif choice == "5":
                self.configure_admin_ids(env_vars)
            elif choice == "6":
                self.write_env_file(env_vars)
                break
            else:
                print("❌ Некорректный выбор")
            
            self.show_config(env_vars)
    
    async def run_bot(self) -> bool:
        """Run bot"""
        try:
            # Load configuration
            config = get_config()
            
            # Setup logging
            setup_logging(config.log_level)
            logger.info("Конфигурация загружена успешно")
            
            # Initialize bot
            bot, dp = await init_bot(config.telegram_bot_token)
            logger.info("Бот инициализирован")
            
            # Setup routers
            main_router = Router()
            
            # Include all handlers
            main_router.include_router(start_handler.router)
            main_router.include_router(client_handler.router)
            main_router.include_router(master_handler.router)
            main_router.include_router(admin_handler.router)
            main_router.include_router(admin_panel.router)
            
            dp.include_router(main_router)
            logger.info("Handlers зарегистрированы")
            
            # Set bot commands
            commands = [
                BotCommand(command="start", description="Начать работу с ботом"),
                BotCommand(command="help", description="Справка"),
                BotCommand(command="cancel", description="Отмена"),
            ]
            await bot.set_my_commands(commands)
            
            # Start polling
            print("\n✅ Бот запущен! Нажмите Ctrl+C для остановки\n")
            logger.info("Бот запущен и слушает сообщения...")
            
            try:
                await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            except KeyboardInterrupt:
                print("\n🛑 Остановка бота...")
                logger.info("Бот остановлен пользователем")
            finally:
                await bot.session.close()
            
            return True
        
        except FileNotFoundError as e:
            print(f"\n❌ Ошибка: {e}")
            print("Пожалуйста, установите конфигурацию")
            return False
        except Exception as e:
            print(f"\n❌ Ошибка при запуске бота: {e}")
            logger.error(f"Bot error: {e}", exc_info=True)
            return False
    
    def run(self):
        """Main entry point"""
        self.print_header()
        
        while True:
            self.print_menu()
            choice = input("Выбор: ").strip()
            
            if choice == "1":
                self.run_configuration_menu()
            elif choice == "2":
                if self.validate_config(self.read_env_file()):
                    asyncio.run(self.run_bot())
                else:
                    print("\n⚠️  Пожалуйста, сначала выполните конфигурацию")
            elif choice == "3":
                print("\n👋 До свидания!")
                sys.exit(0)
            else:
                print("❌ Некорректный выбор")

def main():
    """Main function"""
    setup = BotSetup()
    setup.run()

if __name__ == "__main__":
    main()
