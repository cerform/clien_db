#!/usr/bin/env python3
"""
Запуск всех тестов и health checks
Объединенный скрипт для проверки состояния
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


async def main():
    """Главная функция"""
    print("=" * 70)
    print("🚀 ПОЛНАЯ ПРОВЕРКА TELEGRAM BOT")
    print("=" * 70)
    print()
    
    # Запускаем тесты
    print("📋 Шаг 1: Интеграционные тесты")
    print("-" * 70)
    
    from test_bot import BotTester
    tester = BotTester()
    tests_passed = await tester.run_all_tests()
    
    print()
    print("📋 Шаг 2: Health Check")
    print("-" * 70)
    
    from health_check import HealthChecker
    checker = HealthChecker()
    health_results = await checker.run_all_checks()
    
    print(f"\n✨ Общий статус: {health_results['overall_status'].upper()}")
    
    for name, check in health_results['checks'].items():
        status_icon = {'ok': '✅', 'warning': '⚠️', 'error': '❌'}.get(check['status'], '❓')
        print(f"{status_icon} {name}: {check['message']}")
    
    print()
    print("=" * 70)
    
    if tests_passed and health_results['overall_status'] == 'ok':
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Бот готов к деплою в Cloud Run")
        return 0
    elif health_results['overall_status'] == 'warning':
        print("⚠️  ПРОВЕРКИ ПРОЙДЕНЫ С ПРЕДУПРЕЖДЕНИЯМИ")
        print("ℹ️  Бот может работать, но есть некритичные проблемы")
        return 0
    else:
        print("❌ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print("⚠️  Исправьте ошибки перед деплоем")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
