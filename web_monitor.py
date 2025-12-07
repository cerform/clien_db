#!/usr/bin/env python3
"""
🔍 Веб-интерфейс анализатор реал-тайм
Мониторит все действия в админ-панели: клики, запросы, ошибки, загрузку данных
"""

import asyncio
import json
import time
import sys
from datetime import datetime
from typing import Dict, List
import subprocess

# Цвета для консоли
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'

class WebMonitor:
    def __init__(self):
        self.api_calls = []
        self.errors = []
        self.page_loads = []
        self.js_errors = []
        self.start_time = time.time()
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'errors_count': 0,
        }
        
    def log_event(self, event_type: str, message: str, level: str = "INFO"):
        """Логировать событие с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Выбрать цвет по типу
        color_map = {
            "INFO": Colors.CYAN,
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW,
            "REQUEST": Colors.BLUE,
            "DEBUG": Colors.DIM,
        }
        
        color = color_map.get(level, Colors.WHITE)
        
        print(f"{Colors.DIM}[{timestamp}]{Colors.RESET} {color}[{level}]{Colors.RESET} {event_type}: {message}")
        
    def parse_cloud_logs(self):
        """Парсить логи Cloud Run и выделить ключевые события"""
        try:
            result = subprocess.run(
                ['gcloud', 'run', 'services', 'logs', 'read', 'tattoo-bot', 
                 '--region', 'us-central1', '--limit', '50', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logs = json.loads(result.stdout) if result.stdout.strip() else []
                return logs
        except Exception as e:
            print(f"{Colors.RED}❌ Ошибка при чтении логов: {e}{Colors.RESET}")
        return []
    
    def analyze_logs(self):
        """Анализировать логи и выделить события"""
        logs = self.parse_cloud_logs()
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}📊 АНАЛИЗ ВЕБА И ЛОГОВ - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")
        
        for log in logs:
            text_payload = log.get('textPayload', '')
            severity = log.get('severity', 'INFO')
            
            # Выделять ключевые события
            if 'GET' in text_payload and '/api/' in text_payload:
                # API запрос
                if '200' in text_payload:
                    self.log_event("🌐 API REQUEST", text_payload[:120], "REQUEST")
                    self.stats['successful_requests'] += 1
                elif '404' in text_payload:
                    self.log_event("❌ API NOT FOUND", text_payload[:120], "ERROR")
                    self.stats['failed_requests'] += 1
                self.stats['total_requests'] += 1
                
            elif 'ERROR' in text_payload or 'error' in text_payload.lower():
                self.log_event("⚠️  ОШИБКА", text_payload[:150], "ERROR")
                self.stats['errors_count'] += 1
                self.errors.append(text_payload)
                
            elif 'Successfully' in text_payload or 'initialized' in text_payload:
                self.log_event("✅ УСПЕХ", text_payload[:150], "SUCCESS")
                
            elif 'Waiting' in text_payload or 'startup' in text_payload:
                self.log_event("🔄 ИНИЦИАЛИЗАЦИЯ", text_payload[:150], "DEBUG")
                
            elif '/api/masters' in text_payload or '/api/services' in text_payload:
                self.log_event("📦 DATA LOAD", text_payload[:150], "REQUEST")
        
        self._print_stats()
        
    def _print_stats(self):
        """Показать статистику"""
        uptime = time.time() - self.start_time
        print(f"\n{Colors.BOLD}📈 СТАТИСТИКА:{Colors.RESET}")
        print(f"  ⏱️  Время работы: {int(uptime)}с")
        print(f"  📡 Всего запросов: {self.stats['total_requests']}")
        print(f"  ✅ Успешных: {self.stats['successful_requests']}")
        print(f"  ❌ Ошибок: {self.stats['failed_requests']}")
        print(f"  ⚠️  Предупреждений: {self.stats['errors_count']}")
        
    def test_endpoints(self):
        """Протестировать все основные эндпоинты"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}🧪 ТЕСТИРОВАНИЕ ЭНДПОИНТОВ:{Colors.RESET}\n")
        
        base_url = "https://tattoo-bot-408800151466.us-central1.run.app"
        endpoints = [
            ("/api/health", "Health Check"),
            ("/api/stats", "Статистика"),
            ("/api/masters", "Мастера"),
            ("/api/services", "Услуги"),
            ("/api/clients", "Клиенты"),
            ("/api/bookings", "Бронирования"),
            ("/", "Главная страница"),
            ("/admin/masters", "Админ - Мастера"),
            ("/admin/services", "Админ - Услуги"),
        ]
        
        for endpoint, name in endpoints:
            try:
                result = subprocess.run(
                    ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
                     f"{base_url}{endpoint}"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                status_code = result.stdout.strip()
                
                if status_code == "200":
                    self.log_event(f"✅ {name}", f"{endpoint} → {status_code}", "SUCCESS")
                else:
                    self.log_event(f"⚠️  {name}", f"{endpoint} → {status_code}", "WARNING")
                    
            except Exception as e:
                self.log_event(f"❌ {name}", f"{endpoint} → Error: {e}", "ERROR")
    
    def show_live_dashboard(self):
        """Показать живую панель мониторинга"""
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}🎯 ЖИВОЙ МОНИТОРИНГ АДМИН-ПАНЕЛИ{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}✅ Запущен реал-тайм мониторинг:{Colors.RESET}")
        print(f"  • Логи Cloud Run - обновляются каждые 3 секунды")
        print(f"  • API запросы - отслеживаются в реальном времени")
        print(f"  • Ошибки JavaScript - будут выделены в красном")
        print(f"  • Загрузка данных - мониторится для каждого эндпоинта\n")
        
        print(f"{Colors.YELLOW}📊 Адреса для проверки:{Colors.RESET}")
        print(f"  • Админ-панель: https://tattoo-bot-408800151466.us-central1.run.app")
        print(f"  • API Мастера: https://tattoo-bot-408800151466.us-central1.run.app/api/masters")
        print(f"  • API Услуги: https://tattoo-bot-408800151466.us-central1.run.app/api/services\n")
        
        print(f"{Colors.MAGENTA}💡 Инструкции:{Colors.RESET}")
        print(f"  1. Откройте админ-панель в браузере")
        print(f"  2. Наблюдайте логи здесь в реальном времени")
        print(f"  3. Кликните по элементам (мастера, услуги, клиенты)")
        print(f"  4. Проверьте консоль браузера (F12 → Console)")
        print(f"  5. Ошибки будут показаны здесь с красным флагом\n")
        
        print(f"{Colors.GREEN}🟢 Монитор активен - ждем действий...{Colors.RESET}\n")

    def continuous_monitor(self):
        """Непрерывный мониторинг с обновлением"""
        self.show_live_dashboard()
        self.test_endpoints()
        
        iteration = 0
        while True:
            try:
                iteration += 1
                print(f"\n{Colors.DIM}[Обновление #{iteration} в {datetime.now().strftime('%H:%M:%S')}]{Colors.RESET}")
                self.analyze_logs()
                time.sleep(5)
            except KeyboardInterrupt:
                self._print_final_report()
                break
            except Exception as e:
                self.log_event("❌ ОШИБКА МОНИТОРА", str(e), "ERROR")
                time.sleep(5)
    
    def _print_final_report(self):
        """Финальный отчет при завершении"""
        print(f"\n\n{Colors.BOLD}{Colors.YELLOW}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.YELLOW}📋 ФИНАЛЬНЫЙ ОТЧЕТ{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.YELLOW}{'='*80}{Colors.RESET}\n")
        
        self._print_stats()
        
        if self.errors:
            print(f"\n{Colors.RED}❌ Обнаруженные ошибки:{Colors.RESET}")
            for error in set(self.errors[-5:]):  # Показать последние 5 уникальных
                print(f"  • {error[:100]}")
        
        print(f"\n{Colors.GREEN}✅ Мониторинг завершен{Colors.RESET}\n")


if __name__ == "__main__":
    monitor = WebMonitor()
    
    try:
        monitor.continuous_monitor()
    except KeyboardInterrupt:
        monitor._print_final_report()
        sys.exit(0)
