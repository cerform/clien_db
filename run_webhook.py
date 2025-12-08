"""
Запуск FastAPI webhook-сервера для Cloud Run без интерактивного меню.
"""
import os
import asyncio
from src.main import BotSetup

if __name__ == "__main__":
    # Headless запуск: сразу стартуем webhook-сервер
    setup = BotSetup()
    # Читаем конфиг и запускаем бота с webhook
    env = setup.read_env_file()
    if setup.validate_config(env):
        asyncio.run(setup.run_bot())
    else:
        print("\n⚠️  Пожалуйста, сначала выполните конфигурацию")
