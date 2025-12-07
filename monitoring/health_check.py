#!/usr/bin/env python3
"""
Health Check и Диагностика для Telegram Bot
Запускает веб-сервер для мониторинга состояния бота
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import aiohttp
from aiohttp import web
import traceback

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthChecker:
    """Проверка состояния всех компонентов бота"""
    
    def __init__(self):
        self.checks_history: List[Dict] = []
        self.max_history = 100
        
    async def check_telegram_api(self) -> Dict[str, Any]:
        """Проверка доступности Telegram API"""
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not bot_token:
            return {
                'status': 'error',
                'message': 'TELEGRAM_BOT_TOKEN не найден в переменных окружения',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            'status': 'ok',
                            'message': 'Telegram API доступен',
                            'bot_info': data.get('result', {}),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'Telegram API вернул статус {resp.status}',
                            'timestamp': datetime.now().isoformat()
                        }
        except asyncio.TimeoutError:
            return {
                'status': 'error',
                'message': 'Таймаут при подключении к Telegram API',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка при проверке Telegram API: {str(e)}',
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_google_credentials(self) -> Dict[str, Any]:
        """Проверка Google Credentials"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
            
            if not os.path.exists(credentials_path):
                return {
                    'status': 'error',
                    'message': f'Файл credentials не найден: {credentials_path}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Проверка валидности credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            return {
                'status': 'ok',
                'message': 'Google Credentials валидны',
                'service_account': credentials.service_account_email,
                'scopes': credentials.scopes,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка при проверке Google Credentials: {str(e)}',
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_google_sheets(self) -> Dict[str, Any]:
        """Проверка доступа к Google Sheets"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
            
            if not spreadsheet_id:
                return {
                    'status': 'error',
                    'message': 'GOOGLE_SHEETS_SPREADSHEET_ID не найден',
                    'timestamp': datetime.now().isoformat()
                }
            
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            service = build('sheets', 'v4', credentials=credentials)
            
            # Попытка прочитать метаданные таблицы
            result = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            return {
                'status': 'ok',
                'message': 'Доступ к Google Sheets работает',
                'spreadsheet_title': result.get('properties', {}).get('title'),
                'spreadsheet_id': spreadsheet_id,
                'sheets': [sheet['properties']['title'] for sheet in result.get('sheets', [])],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка при проверке Google Sheets: {str(e)}',
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_environment_variables(self) -> Dict[str, Any]:
        """Проверка всех необходимых переменных окружения"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'GOOGLE_SHEETS_SPREADSHEET_ID',
            'GOOGLE_APPLICATION_CREDENTIALS'
        ]
        
        missing_vars = []
        present_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                present_vars.append({
                    'name': var,
                    'value_length': len(value),
                    'masked_value': value[:10] + '...' if len(value) > 10 else value
                })
            else:
                missing_vars.append(var)
        
        status = 'ok' if not missing_vars else 'warning'
        
        return {
            'status': status,
            'message': 'Проверка переменных окружения завершена',
            'present': present_vars,
            'missing': missing_vars,
            'timestamp': datetime.now().isoformat()
        }
    
    async def check_bot_imports(self) -> Dict[str, Any]:
        """Проверка импортов модулей бота"""
        try:
            import_tests = []
            
            # Основные импорты
            modules_to_test = [
                ('aiogram', 'Telegram Bot Framework'),
                ('aiohttp', 'Async HTTP Client'),
                ('google.oauth2', 'Google Auth'),
                ('googleapiclient', 'Google API Client'),
                ('pydantic', 'Data Validation'),
                ('pytz', 'Timezone Support'),
            ]
            
            for module_name, description in modules_to_test:
                try:
                    __import__(module_name)
                    import_tests.append({
                        'module': module_name,
                        'description': description,
                        'status': 'ok'
                    })
                except ImportError as e:
                    import_tests.append({
                        'module': module_name,
                        'description': description,
                        'status': 'error',
                        'error': str(e)
                    })
            
            failed = [t for t in import_tests if t['status'] == 'error']
            status = 'ok' if not failed else 'error'
            
            return {
                'status': status,
                'message': 'Проверка импортов завершена',
                'imports': import_tests,
                'failed_count': len(failed),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка при проверке импортов: {str(e)}',
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Запуск всех проверок"""
        logger.info("Запуск полной диагностики...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Запускаем все проверки параллельно
        checks = {
            'environment': self.check_environment_variables(),
            'imports': self.check_bot_imports(),
            'telegram_api': self.check_telegram_api(),
            'google_credentials': self.check_google_credentials(),
            'google_sheets': self.check_google_sheets(),
        }
        
        for name, check_coro in checks.items():
            try:
                results['checks'][name] = await check_coro
            except Exception as e:
                results['checks'][name] = {
                    'status': 'error',
                    'message': f'Критическая ошибка при проверке: {str(e)}',
                    'traceback': traceback.format_exc(),
                    'timestamp': datetime.now().isoformat()
                }
        
        # Общий статус
        all_statuses = [check['status'] for check in results['checks'].values()]
        if 'error' in all_statuses:
            results['overall_status'] = 'error'
        elif 'warning' in all_statuses:
            results['overall_status'] = 'warning'
        else:
            results['overall_status'] = 'ok'
        
        # Сохраняем в историю
        self.checks_history.append(results)
        if len(self.checks_history) > self.max_history:
            self.checks_history.pop(0)
        
        return results


# Глобальный checker
checker = HealthChecker()


# Web интерфейс
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram Bot Health Check</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            text-transform: uppercase;
        }
        
        .status-ok {
            background: #10b981;
            color: white;
        }
        
        .status-warning {
            background: #f59e0b;
            color: white;
        }
        
        .status-error {
            background: #ef4444;
            color: white;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        button:hover {
            background: #764ba2;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .checks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .check-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s;
        }
        
        .check-card:hover {
            transform: translateY(-5px);
        }
        
        .check-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .check-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        
        .check-content {
            color: #666;
            line-height: 1.6;
        }
        
        .check-detail {
            background: #f3f4f6;
            padding: 10px;
            border-radius: 6px;
            margin-top: 10px;
            font-size: 14px;
        }
        
        .error-trace {
            background: #fee;
            border-left: 4px solid #ef4444;
            padding: 10px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .timestamp {
            color: #999;
            font-size: 12px;
            margin-top: 10px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: white;
            font-size: 18px;
        }
        
        .history {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .history-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .history-item:hover {
            background: #f9fafb;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                🤖 Telegram Bot Health Check
                <span id="overall-status" class="status-badge">Loading...</span>
            </h1>
            <p>Последняя проверка: <span id="last-check-time">никогда</span></p>
            <div class="controls">
                <button onclick="runCheck()" id="check-btn">
                    ▶️ Запустить проверку
                </button>
                <button onclick="toggleAutoRefresh()" id="auto-refresh-btn">
                    🔄 Авто-обновление: ВЫКЛ
                </button>
            </div>
        </div>
        
        <div id="checks-container" class="checks-grid">
            <div class="loading">
                <div class="spinner"></div>
                <p>Загрузка данных...</p>
            </div>
        </div>
        
        <div class="history">
            <h2 style="margin-bottom: 15px;">📊 История проверок</h2>
            <div id="history-container">
                История пока пуста
            </div>
        </div>
    </div>
    
    <script>
        let autoRefresh = false;
        let refreshInterval;
        
        async function runCheck() {
            const btn = document.getElementById('check-btn');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Проверка...';
            
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                updateUI(data);
            } catch (error) {
                console.error('Error:', error);
                alert('Ошибка при выполнении проверки: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '▶️ Запустить проверку';
            }
        }
        
        function updateUI(data) {
            // Обновляем общий статус
            const statusBadge = document.getElementById('overall-status');
            statusBadge.textContent = data.overall_status.toUpperCase();
            statusBadge.className = 'status-badge status-' + data.overall_status;
            
            // Обновляем время
            document.getElementById('last-check-time').textContent = 
                new Date(data.timestamp).toLocaleString('ru-RU');
            
            // Обновляем проверки
            const container = document.getElementById('checks-container');
            container.innerHTML = '';
            
            for (const [name, check] of Object.entries(data.checks)) {
                const card = createCheckCard(name, check);
                container.appendChild(card);
            }
            
            updateHistory();
        }
        
        function createCheckCard(name, check) {
            const card = document.createElement('div');
            card.className = 'check-card';
            
            const header = document.createElement('div');
            header.className = 'check-header';
            
            const title = document.createElement('div');
            title.className = 'check-title';
            title.textContent = formatCheckName(name);
            
            const badge = document.createElement('span');
            badge.className = 'status-badge status-' + check.status;
            badge.textContent = check.status.toUpperCase();
            
            header.appendChild(title);
            header.appendChild(badge);
            
            const content = document.createElement('div');
            content.className = 'check-content';
            content.innerHTML = '<p>' + check.message + '</p>';
            
            // Дополнительная информация
            if (check.bot_info) {
                const detail = document.createElement('div');
                detail.className = 'check-detail';
                detail.innerHTML = '<strong>Bot:</strong> @' + check.bot_info.username + 
                                 ' (' + check.bot_info.first_name + ')';
                content.appendChild(detail);
            }
            
            if (check.service_account) {
                const detail = document.createElement('div');
                detail.className = 'check-detail';
                detail.innerHTML = '<strong>Service Account:</strong> ' + check.service_account;
                content.appendChild(detail);
            }
            
            if (check.spreadsheet_title) {
                const detail = document.createElement('div');
                detail.className = 'check-detail';
                detail.innerHTML = '<strong>Spreadsheet:</strong> ' + check.spreadsheet_title;
                if (check.sheets) {
                    detail.innerHTML += '<br><strong>Листы:</strong> ' + check.sheets.join(', ');
                }
                content.appendChild(detail);
            }
            
            if (check.traceback) {
                const trace = document.createElement('pre');
                trace.className = 'error-trace';
                trace.textContent = check.traceback;
                content.appendChild(trace);
            }
            
            const timestamp = document.createElement('div');
            timestamp.className = 'timestamp';
            timestamp.textContent = '⏰ ' + new Date(check.timestamp).toLocaleString('ru-RU');
            
            card.appendChild(header);
            card.appendChild(content);
            card.appendChild(timestamp);
            
            return card;
        }
        
        function formatCheckName(name) {
            const names = {
                'environment': '🔧 Переменные окружения',
                'imports': '📦 Модули Python',
                'telegram_api': '📱 Telegram API',
                'google_credentials': '🔑 Google Credentials',
                'google_sheets': '📊 Google Sheets'
            };
            return names[name] || name;
        }
        
        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            const btn = document.getElementById('auto-refresh-btn');
            
            if (autoRefresh) {
                btn.textContent = '🔄 Авто-обновление: ВКЛ';
                runCheck();
                refreshInterval = setInterval(runCheck, 30000); // каждые 30 сек
            } else {
                btn.textContent = '🔄 Авто-обновление: ВЫКЛ';
                clearInterval(refreshInterval);
            }
        }
        
        async function updateHistory() {
            try {
                const response = await fetch('/api/history');
                const history = await response.json();
                
                const container = document.getElementById('history-container');
                if (history.length === 0) {
                    container.innerHTML = 'История пока пуста';
                    return;
                }
                
                container.innerHTML = '';
                history.slice().reverse().forEach((item, index) => {
                    const historyItem = document.createElement('div');
                    historyItem.className = 'history-item';
                    
                    const badge = document.createElement('span');
                    badge.className = 'status-badge status-' + item.overall_status;
                    badge.textContent = item.overall_status.toUpperCase();
                    
                    historyItem.innerHTML = 
                        '<strong>' + new Date(item.timestamp).toLocaleString('ru-RU') + '</strong> ' +
                        badge.outerHTML;
                    
                    container.appendChild(historyItem);
                });
            } catch (error) {
                console.error('Error loading history:', error);
            }
        }
        
        // Загружаем при старте
        runCheck();
    </script>
</body>
</html>
"""


async def handle_index(request):
    """Главная страница"""
    return web.Response(text=HTML_TEMPLATE, content_type='text/html')


async def handle_health_check(request):
    """API endpoint для проверки здоровья"""
    results = await checker.run_all_checks()
    return web.json_response(results)


async def handle_history(request):
    """API endpoint для истории проверок"""
    return web.json_response(checker.checks_history)


async def handle_quick_check(request):
    """Быстрая проверка статуса (для Cloud Run health check)"""
    try:
        # Быстрая проверка только критичных компонентов
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return web.json_response({'status': 'unhealthy', 'reason': 'No bot token'}, status=503)
        
        return web.json_response({'status': 'healthy'})
    except Exception as e:
        return web.json_response({'status': 'unhealthy', 'error': str(e)}, status=503)


def create_app():
    """Создание web приложения"""
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/health', handle_health_check)
    app.router.add_get('/api/history', handle_history)
    app.router.add_get('/health', handle_quick_check)  # Для Cloud Run
    return app


if __name__ == '__main__':
    print("=" * 60)
    print("🏥 Telegram Bot Health Check Server")
    print("=" * 60)
    print("")
    print("Запуск веб-сервера для мониторинга бота...")
    print("")
    
    port = int(os.getenv('PORT', 8080))
    
    print(f"🌐 Откройте в браузере: http://localhost:{port}")
    print(f"🔍 API проверки здоровья: http://localhost:{port}/api/health")
    print(f"💚 Cloud Run health check: http://localhost:{port}/health")
    print("")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 60)
    
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=port)
