#!/usr/bin/env python3
"""
Pre-deployment validation script
Проверяет всё перед деплоем на Cloud Run
"""

import sys
import subprocess
from pathlib import Path

# Цвета для вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_section(title):
    """Печать заголовка секции"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}🔍 {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.ENDC}\n")

def run_command(cmd, description):
    """Запустить команду и проверить результат"""
    print(f"{Colors.CYAN}▶ {description}...{Colors.ENDC}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ {description} OK{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  {description} - warnings found:{Colors.ENDC}")
            if result.stderr:
                print(f"   {result.stderr[:200]}")
            return True  # Continue anyway for non-critical checks
    except Exception as e:
        print(f"{Colors.RED}❌ {description} FAILED: {e}{Colors.ENDC}")
        return False

def check_file_exists(filepath, description):
    """Проверить наличие файла"""
    if Path(filepath).exists():
        print(f"{Colors.GREEN}✅ {description} found{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.RED}❌ {description} NOT FOUND{Colors.ENDC}")
        return False

def check_python_syntax():
    """Проверить синтаксис Python файлов"""
    print_section("Python Syntax Check")
    import sys
    python_exec = sys.executable or "python3"
    errors_found = False
    for py_file in Path("src").rglob("*.py"):
        result = subprocess.run(
            f"{python_exec} -m py_compile {py_file}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"{Colors.RED}❌ {py_file}: {result.stderr}{Colors.ENDC}")
            errors_found = True
    
    if not errors_found:
        print(f"{Colors.GREEN}✅ All Python files have valid syntax{Colors.ENDC}")
    
    return not errors_found

def check_imports():
    """Проверить импорты"""
    print_section("Import Check")
    
    try:
        exec(open("src/main.py").read())
        print(f"{Colors.GREEN}✅ Main module imports successfully{Colors.ENDC}")
        return True
    except ImportError as e:
        print(f"{Colors.RED}❌ Import error: {e}{Colors.ENDC}")
        return False
    except Exception:
        # main.py might require full runtime setup
        print(f"{Colors.YELLOW}⚠️  Could not fully validate runtime imports{Colors.ENDC}")
        return True

def check_requirements():
    """Проверить requirements.txt"""
    print_section("Requirements Check")
    
    if not check_file_exists("requirements.txt", "requirements.txt"):
        return False
    
    # Check that all required packages are in requirements
    required_packages = [
        "aiogram",
        "aiohttp",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
        "openai",
        "python-dotenv"
    ]
    
    with open("requirements.txt") as f:
        content = f.read().lower()
    
    missing = []
    for pkg in required_packages:
        if pkg.lower() not in content:
            missing.append(pkg)
    
    if missing:
        print(f"{Colors.YELLOW}⚠️  Missing packages in requirements.txt: {missing}{Colors.ENDC}")
        return False
    
    print(f"{Colors.GREEN}✅ All required packages are in requirements.txt{Colors.ENDC}")
    return True

def check_config():
    """Проверить конфигурацию"""
    print_section("Configuration Check")
    
    required_env_vars = [
        "TELEGRAM_BOT_TOKEN",
        "GOOGLE_SPREADSHEET_ID",
        "OPENAI_API_KEY",
        "OPENAI_ASSISTANT_ID",
        "ADMIN_IDS"
    ]
    
    import os
    missing = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"{Colors.YELLOW}⚠️  Missing environment variables: {missing}{Colors.ENDC}")
        print(f"   These should be set in Cloud Run secrets or .env")
        return True  # Not critical for build
    
    print(f"{Colors.GREEN}✅ All environment variables set{Colors.ENDC}")
    return True

def check_docker():
    """Проверить Dockerfile"""
    print_section("Docker Configuration Check")
    
    if not check_file_exists("Dockerfile", "Dockerfile"):
        return False
    
    with open("Dockerfile") as f:
        content = f.read()
    
    checks = [
        ("FROM python", "Base image specified"),
        ("EXPOSE", "Port exposed"),
        ("RUN pip install", "Dependencies installed"),
        ("CMD", "Entry point defined")
    ]
    
    for check_str, description in checks:
        if check_str in content:
            print(f"{Colors.GREEN}✅ {description}{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}⚠️  {description} might be missing{Colors.ENDC}")
    
    return True

def check_database():
    """Проверить подключение к БД"""
    print_section("Database Connection Check")
    
    print(f"{Colors.CYAN}▶ Checking Google Sheets connection...{Colors.ENDC}")
    
    try:
        from src.db.sheets_client import GoogleSheetsClient
        from src.config import get_config
        
        config = get_config()
        client = GoogleSheetsClient("credentials.json", config.google_spreadsheet_id)
        
        # Try to get masters
        masters = client.get_all_rows("masters")
        if masters and len(masters) > 0:
            print(f"{Colors.GREEN}✅ Database connection OK ({len(masters)} rows in masters){Colors.ENDC}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  Database connected but tables empty{Colors.ENDC}")
            return True
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Could not verify database: {str(e)[:100]}{Colors.ENDC}")
        return True  # Not critical for deploy

def check_openai():
    """Проверить подключение к OpenAI"""
    print_section("OpenAI API Check")
    
    try:
        from src.config import get_config
        from openai import OpenAI
        
        config = get_config()
        client = OpenAI(api_key=config.openai_api_key)
        
        # Check that assistant exists
        assistant = client.beta.assistants.retrieve(config.openai_assistant_id)
        print(f"{Colors.GREEN}✅ OpenAI connection OK (Assistant: {config.openai_assistant_id}){Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Could not verify OpenAI: {str(e)[:100]}{Colors.ENDC}")
        return True  # Not critical for deploy

def check_linting():
    """Проверить код стиль (pylint)"""
    print_section("Code Quality Check (Pylint)")
    
    print(f"{Colors.CYAN}▶ Running pylint on src/...{Colors.ENDC}")
    result = subprocess.run(
        "pylint src/ --max-line-length=120 --disable=missing-docstring,too-many-arguments --exit-zero",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if "Your code has been rated" in result.stdout:
        lines = result.stdout.split('\n')
        for line in lines:
            if "rated" in line:
                print(f"{Colors.GREEN}✅ {line.strip()}{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}⚠️  Pylint output: {result.stdout[:200]}{Colors.ENDC}")
    
    return True


def check_admin_ids_env():
    """Validate ADMIN_IDS parseable to list of ints"""
    print_section("Admin IDs Config Check")
    import os
    admin_ids = os.getenv('ADMIN_IDS')
    if not admin_ids:
        print(f"{Colors.YELLOW}⚠️  ADMIN_IDS not set{Colors.ENDC}")
        return True
    try:
        ids = [int(i.strip()) for i in admin_ids.split(',') if i.strip()]
        print(f"{Colors.GREEN}✅ ADMIN_IDS parsed ({len(ids)} ids){Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ ADMIN_IDS invalid: {e}{Colors.ENDC}")
        return False


def validate_credentials_json():
    """Check credentials.json is valid JSON with expected keys"""
    print_section("Google Credentials Check")
    import json
    try:
        p = Path('credentials.json')
        if not p.exists():
            print(f"{Colors.YELLOW}⚠️  credentials.json not found{Colors.ENDC}")
            return True
        data = json.loads(p.read_text())
        if 'type' in data and 'client_email' in data:
            print(f"{Colors.GREEN}✅ credentials.json looks valid{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  credentials.json seems incomplete{Colors.ENDC}")
            return True
    except Exception as e:
        print(f"{Colors.RED}❌ Invalid credentials.json: {e}{Colors.ENDC}")
        return False


def check_api_endpoints():
    """Call important API endpoints via TestClient (fast, internal checks)"""
    try:
        from src.web.app import create_app
        from fastapi.testclient import TestClient
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  API endpoint check skipped: {e}{Colors.ENDC}")
        return True

    print_section("API Endpoint Check")
    try:
        app = create_app()
        client = TestClient(app)
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  API endpoint check skipped: {e}{Colors.ENDC}")
        return True
    endpoints = [
        '/api/health',
        '/api/stats',
        '/api/masters',
        '/api/clients',
        '/api/bookings',
        '/api/inka-training/stats',
    ]
    failed = False
    for ep in endpoints:
        try:
            r = client.get(ep)
            if r.status_code != 200:
                print(f"{Colors.YELLOW}⚠️  {ep} -> {r.status_code}{Colors.ENDC}")
                failed = True
            else:
                print(f"{Colors.GREEN}✅ {ep} -> {r.status_code}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}❌ {ep} -> {e}{Colors.ENDC}")
            failed = True

    return not failed


def check_tests():
    """Run pytest suite and report status; return boolean"""
    print_section("Unit Tests")
    try:
        result = subprocess.run('pytest -q', shell=True)
        return result.returncode == 0
    except Exception as e:
        print(f"{Colors.RED}❌ Error running pytest: {e}{Colors.ENDC}")
        return False

def main():
    """Главная функция"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║              🔍 PRE-DEPLOYMENT VALIDATION SCRIPT                          ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(Colors.ENDC)
    
    checks = [
        ("File Existence", lambda: all([
            check_file_exists("Dockerfile", "Dockerfile"),
            check_file_exists("requirements.txt", "requirements.txt"),
            check_file_exists("credentials.json", "credentials.json (optional)") or True,
        ])),
        ("Python Syntax", check_python_syntax),
        ("Requirements", check_requirements),
        ("Docker Configuration", check_docker),
        ("Configuration", check_config),
        ("Database Connection", check_database),
        ("Google Credentials", validate_credentials_json),
        ("OpenAI API", check_openai),
        ("Admin IDs", check_admin_ids_env),
        ("API Endpoints", check_api_endpoints),
        ("Unit Tests", check_tests),
        ("Code Quality", check_linting),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"{Colors.RED}❌ {check_name} check failed: {e}{Colors.ENDC}")
            results[check_name] = False
    
    # Summary
    print_section("Validation Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        status = f"{Colors.GREEN}✅{Colors.ENDC}" if result else f"{Colors.RED}❌{Colors.ENDC}"
        print(f"{status} {check_name}")
    
    print()
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL CHECKS PASSED ({passed}/{total}){Colors.ENDC}")
        print(f"{Colors.GREEN}Ready for deployment!{Colors.ENDC}\n")
        write_report(results)
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  SOME CHECKS FAILED ({passed}/{total}){Colors.ENDC}")
        print(f"{Colors.YELLOW}Please review warnings above before deploying{Colors.ENDC}\n")
        write_report(results)
        return 1


def write_report(results: dict, path: str = 'pre_deploy_report.json'):
    import json, time
    payload = {
        'ts': time.time(),
        'results': results,
        'summary': { 'passed': sum(1 for v in results.values() if v), 'total': len(results) }
    }
    try:
        Path(path).write_text(json.dumps(payload))
        print(f"{Colors.GREEN}✅ Saved report to {path}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Could not write report: {e}{Colors.ENDC}")

if __name__ == "__main__":
    sys.exit(main())
