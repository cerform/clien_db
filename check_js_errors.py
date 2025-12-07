#!/usr/bin/env python3
"""
Анализатор JavaScript ошибок в админ-панели
"""

import subprocess
import re
from urllib.parse import urljoin

BASE_URL = "https://tattoo-bot-408800151466.us-central1.run.app"
ENDPOINTS = [
    "/",
    "/admin/masters",
    "/admin/services",
    "/admin/clients",
    "/admin/bookings",
]

def check_endpoint(endpoint):
    """Проверить эндпоинт на JavaScript ошибки"""
    url = urljoin(BASE_URL, endpoint)
    
    print(f"\n{'='*60}")
    print(f"🔍 Анализ: {endpoint}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            ['curl', '-s', url],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        html = result.stdout
        
        # Ищем JavaScript блоки
        script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        
        print(f"✅ Статус: OK (размер {len(html)} байт)")
        print(f"📝 JavaScript блоков найдено: {len(script_blocks)}")
        
        # Ищем потенциальные ошибки
        errors_found = []
        
        # Ошибка 1: Undefined functions
        undefined_patterns = [
            r'function\s+(\w+)\s*\(',  # Определения функций
            r'(\w+)\s*\(',  # Вызовы функций
        ]
        
        # Ищем вызовы fetch
        fetch_calls = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", html)
        if fetch_calls:
            print(f"\n📡 Fetch вызовы найдены:")
            for call in fetch_calls:
                print(f"   • {call}")
        
        # Ищем onclick вызовы
        onclick_calls = re.findall(r'onclick=["\']([^"\']+)["\']', html)
        if onclick_calls:
            print(f"\n🖱️ Onclick вызовы найдено: {len(onclick_calls)}")
            for call in set(onclick_calls[:5]):
                print(f"   • {call}")
        
        # Ищем ошибки в консоли
        console_errors = re.findall(r'console\.error\(["\']([^"\']+)["\']', html)
        if console_errors:
            print(f"\n❌ Console.error вызовы найдено: {len(console_errors)}")
            for error in set(console_errors[:5]):
                print(f"   • {error}")
        
        # Ищем потенциальные проблемы
        issues = []
        
        # Проверка: есть ли document.getElementById
        if 'document.getElementById' in html:
            print(f"✅ Используется getElementById")
            # Ищем ID'ы которых нет
            id_gets = re.findall(r"getElementById\(['\"]([^'\"]+)['\"]", html)
            id_defs = re.findall(r'id=["\']([^"\']+)["\']', html)
            
            missing = set(id_gets) - set(id_defs)
            if missing:
                print(f"⚠️  Отсутствующие ID'ы в HTML:")
                for missing_id in missing:
                    print(f"   • #{missing_id}")
                    issues.append(f"Missing ID: {missing_id}")
        
        # Проверка: table элементы
        if 'table' in html.lower():
            print(f"✅ Таблица присутствует")
            tbody_match = re.search(r'<tbody[^>]*>(.*?)</tbody>', html, re.DOTALL)
            if tbody_match:
                tbody = tbody_match.group(1)
                if '<tr' in tbody:
                    tr_count = tbody.count('<tr')
                    print(f"   • Строк в tbody: {tr_count}")
        
        # Проверка: API endpoints
        api_calls = re.findall(r"fetch\(['\"](/api/[^'\"]+)['\"]", html)
        if api_calls:
            print(f"\n🔌 API вызовы:")
            for api in set(api_calls):
                print(f"   • {api}")
        
        if issues:
            print(f"\n⚠️  Проблемы найдены: {len(issues)}")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ Никаких проблем не обнаружено")
            
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")

def main():
    print("\n" + "="*60)
    print("🔍 АНАЛИЗАТОР JAVASCRIPT ОШИБОК")
    print("="*60)
    
    for endpoint in ENDPOINTS:
        check_endpoint(endpoint)
    
    print(f"\n" + "="*60)
    print("📊 ИТОГОВАЯ ПРОВЕРКА ВСЕХ ЭНДПОИНТОВ")
    print("="*60 + "\n")
    
    # Проверка доступности всех URL'ов
    for endpoint in ENDPOINTS:
        url = urljoin(BASE_URL, endpoint)
        try:
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', url],
                capture_output=True,
                text=True,
                timeout=5
            )
            status = result.stdout
            status_emoji = "✅" if status == "200" else "⚠️"
            print(f"{status_emoji} {endpoint:30} → {status}")
        except Exception as e:
            print(f"❌ {endpoint:30} → Error: {e}")

if __name__ == "__main__":
    main()
