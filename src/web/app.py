"""
FastAPI Web Interface для управления БД
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Optional
from fastapi.templating import Jinja2Templates

from src.config.config import Config
from src.services.admin_manager import get_admin_ids as get_runtime_admin_ids
from src.services.admin_db_manager import DatabaseManager, InkaLearningSystem
from src.web.api import routers
from src.web.routes.setup import router as setup_router
from src.bot.telegram_webhook import router as telegram_webhook_router
from src.core.llm_client import LLMClient

logger = logging.getLogger(__name__)

# Initialize managers
db_manager: Optional[DatabaseManager] = None
learning_system: Optional[InkaLearningSystem] = None
sheets_client = None  # Global sheets client for API access

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    global db_manager, learning_system, sheets_client

    config = Config.from_env()
    # Merge configuration from config_manager if present (allows using secret manager + config.json)
    try:
        from src.core.config_manager import get_config as get_aggregate_config, get_secret
        ag_cfg = get_aggregate_config()
        if ag_cfg.get("spreadsheet_id"):
            config.SPREADSHEET_ID = ag_cfg.get("spreadsheet_id")
        if ag_cfg.get("master_calendar_id"):
            config.MASTER_CALENDAR_ID = ag_cfg.get("master_calendar_id")
        # If secret for bot token exists in secret manager, ensure Config uses it
        bot_token_secret = get_secret("TELEGRAM_BOT_TOKEN")
        if bot_token_secret:
            config.BOT_TOKEN = bot_token_secret
    except Exception:
        pass
    
    app = FastAPI(
        title="Tattoo Bot Admin",
        description="Веб-интерфейс для управления БД тату-салона",
        version="1.0.0"
    )
    app.state.config = config

    # Disallow caching on admin web pages so clients always fetch latest JS/HTML
    @app.middleware("http")
    async def add_no_cache_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    # Initialize managers
    try:
        from src.db.sheets_client import SheetsClient

        # Get credentials file path from env or use default
        creds_file = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")
        token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

        sheets_client = SheetsClient(
            creds_path=creds_file,
            token_path=token_path,
        )
        db_manager = DatabaseManager(sheets_client)
        
        # Initialize new AI-powered INKA Learning System
        try:
            from src.ai.inka_learning import INKALearningSystem
            # INKA Learning System does not require OpenAI credentials to initialize.
            # It provides admin-controlled prompt context. Initialize regardless
            # and use OpenAI key at runtime for LLM calls inside INKA where needed.
            learning_system = INKALearningSystem()
            logger.info("✅ INKA Learning System initialized")
        except Exception as inka_error:
            logger.warning(f"⚠️ INKA Learning System initialization failed: {inka_error}")
            learning_system = None
        
        logger.info("✅ Database managers initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize database manager: {e}")
        db_manager = None
        learning_system = None
        sheets_client = None
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Simulation middleware: intercept non-GET requests with 'X-Simulate' header and return simulated response
    @app.middleware('http')
    async def simulate_middleware(request: Request, call_next):
        # header case-insensitive
        if request.headers.get('x-simulate') and request.method != 'GET':
            # Attempt to produce a smarter simulated response based on OpenAPI specification
            try:
                openapi = request.app.openapi()
            except Exception:
                openapi = None
            mock = None
            status = 200
            if openapi:
                # find matching path in openapi
                from re import compile as re_compile
                pmap = openapi.get('paths', {})
                matched_op = None
                matched_path_template = None
                for tmpl, meta in pmap.items():
                    # build regex from template
                    regex = '^' + tmpl.replace('{', '(?P<').replace('}', '>[^/]+)') + '$'
                    try:
                        rx = re_compile(regex)
                        if rx.match(str(request.url.path)):
                            matched_op = meta
                            matched_path_template = tmpl
                            break
                    except Exception:
                        continue
                if matched_op:
                    method_lower = request.method.lower()
                    op = matched_op.get(method_lower)
                    if op:
                        # pick response code
                        resp_map = op.get('responses', {})
                        # prefer 200, 201 else take first key
                        code = '200' if '200' in resp_map else ('201' if '201' in resp_map else (list(resp_map.keys())[0] if resp_map else '200'))
                        resp_def = resp_map.get(code, {})
                        # content -> try find application/json
                        content = resp_def.get('content', {})
                        if 'application/json' in content:
                            schema = content['application/json'].get('schema', {})
                            example = content['application/json'].get('example') or content['application/json'].get('examples')
                            if example:
                                # example may be dict or having 'value'
                                if isinstance(example, dict) and 'value' in example:
                                    mock = example['value']
                                else:
                                    mock = example
                            elif schema:
                                from src.web.utils import schema_to_example
                                components = openapi.get('components', {}) if openapi else {}
                                mock = schema_to_example(schema, components)
                        else:
                            # Try any content type and return simple info
                            mock = {'simulated': True, 'notes': 'no json content, returning basic response'}
                        try:
                            status = int(code)
                        except Exception:
                            status = 200
            # fallback basic response
            if mock is None:
                try:
                    raw = await request.body()
                    body_text = raw.decode('utf-8') if raw else ''
                except Exception:
                    body_text = ''
                mock = {'simulated': True, 'path': str(request.url.path), 'method': request.method, 'query': dict(request.query_params), 'body': body_text}
            return JSONResponse(mock, status_code=status)
        return await call_next(request)

    # Auth token parsing middleware: parse Bearer admin token and expose request.state.admin_id
    @app.middleware('http')
    async def parse_admin_token(request: Request, call_next):
        auth = request.headers.get('Authorization') or request.headers.get('authorization')
        if auth and auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1].strip()
            # Recognize tokens like admin_token_<id>
            if token.startswith('admin_token_'):
                try:
                    admin_id = int(token.split('_')[-1])
                    request.state.admin_id = admin_id
                    request.state.admin_token = token
                except Exception:
                    request.state.admin_id = None
            else:
                # Try JWT decode
                try:
                    from src.web.auth import verify_jwt
                    v = verify_jwt(token)
                    if v:
                        request.state.admin_id = v
                        request.state.admin_token = token
                except Exception:
                    # ignore invalid tokens
                    request.state.admin_id = None
        return await call_next(request)

    # RBAC middleware: set a role on the request for downstream handlers
    from src.security.rbac_middleware import rbac_middleware
    app.middleware('http')(rbac_middleware)

    # RBAC enforcement is handled at endpoint level via _is_admin() helper function
    # Each protected endpoint checks admin status using Bearer token or admin_id
    # See src/web/api.py:_is_admin() for implementation details
    logger.info('✅ RBAC handled at endpoint level via admin token validation')
    
    # Static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Templates
    templates_dir = Path(__file__).parent / "templates"
    if templates_dir.exists():
        app.templates = Jinja2Templates(directory=str(templates_dir))
    else:
        app.templates = Jinja2Templates(directory="src/web/templates")

    # Authorization is enforced at endpoint level using admin token middleware
    # Protected endpoints use _is_admin(request) helper to check permissions

    # Include API routers
    app.include_router(routers.api_router)
    
    # Include admin pages router
    from src.web.pages import admin_router
    app.include_router(admin_router)

    # DB Admin UI
    try:
        from src.web.routes.db_admin import router as db_admin_router
        app.include_router(db_admin_router)
        logger.info('✅ DB Admin router added')
    except Exception as de:
        logger.warning(f'⚠️ Could not add DB Admin router: {de}')

    # Include web installer for admins and first-run setup
    try:
        from src.web.installer import installer_router
        app.include_router(installer_router)
        logger.info('✅ Installer router added')
    except Exception as ie:
        logger.warning(f'⚠️ Could not include installer router: {ie}')

    # Setup page router
    app.include_router(setup_router)
    # System settings router (admin accessible)
    try:
        from src.web.routes.system_settings import router as system_settings_router
        app.include_router(system_settings_router)
        logger.info('✅ System settings router added')
    except Exception as se:
        logger.warning(f'⚠️ Could not add system settings router: {se}')
    # Telegram webhook router
    app.include_router(telegram_webhook_router)

    # Monitoring and health check router
    try:
        from src.web.monitoring import router as monitoring_router
        app.include_router(monitoring_router)
        logger.info('✅ Monitoring router added')
    except Exception as me:
        logger.warning(f'⚠️ Could not add monitoring router: {me}')

    # Initialize Sentry (optional) if env provided
    sentry_dsn = os.getenv('SENTRY_DSN')
    if sentry_dsn:
        try:
            from sentry_sdk import init as sentry_init
            from sentry_sdk.integrations.logging import LoggingIntegration
            sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
            sentry_init(dsn=sentry_dsn, integrations=[sentry_logging], traces_sample_rate=0.05)
            logger.info('✅ Sentry initialized')
        except Exception as se:
            logger.warning(f'⚠️ Failed to initialize Sentry: {se}')

    # Initialize Google Cloud Logging if configured
    if os.getenv('ENABLE_CLOUD_LOGGING', 'false').lower() in ['1', 'true', 'yes']:
        try:
            from google.cloud import logging as cloud_logging
            client = cloud_logging.Client()
            client.setup_logging()
            logger.info('✅ Cloud Logging initialized')
        except Exception as ce:
            logger.warning(f'⚠️ Cloud Logging init error: {ce}')
    
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Главная страница - SPA Dashboard"""
        return app.templates.TemplateResponse("dashboard_spa.html", {"request": request})

    @app.get("/calendar", response_class=HTMLResponse)
    async def calendar_page(request: Request):
        """Calendar page"""
        calendar_id = config.MASTER_CALENDAR_ID if hasattr(config, 'MASTER_CALENDAR_ID') else None
        return app.templates.TemplateResponse("calendar.html", {
            "request": request,
            "calendar_id": calendar_id
        })

    @app.get("/login", response_class=HTMLResponse)
    async def login_page():
        """Страница входа"""
        return get_login_html()
    
    @app.post("/api/login")
    async def login(request: Request):
        """Вход в систему"""
        try:
            from src.web.auth import authenticate_admin, check_admin_password, create_jwt_for_admin
            
            body = await request.json()
            username = body.get("username", "").strip()
            password = body.get("password", "")

            # If username provided, use full authentication
            if username:
                success, admin_info = authenticate_admin(username, password)
                if success:
                    admin_id = admin_info.get('id', 1)
                    jwt_token = create_jwt_for_admin(admin_id)
                    # For backward compatibility also return legacy token
                    legacy = f"admin_token_{admin_id}"
                    return {
                        "success": True,
                        "token": jwt_token,
                        "legacy_token": legacy,
                        "user": admin_info,
                        "message": "Успешный вход"
                    }
                else:
                    return {"success": False, "message": "Неверный логин или пароль"}

            # Fallback: password-only login (backward compatibility)
            if check_admin_password(password):
                try:
                    admin_ids = get_runtime_admin_ids()
                    admin_id = admin_ids[0] if admin_ids else 123
                except Exception:
                    from src.config.config import Config
                    cfg = Config.from_env()
                    admin_id = cfg.ADMIN_USER_IDS[0] if cfg.ADMIN_USER_IDS else 123
                jwt_token = create_jwt_for_admin(admin_id)
                legacy = f"admin_token_{admin_id}"
                return {"success": True, "token": jwt_token, "legacy_token": legacy, "message": "Успешный вход"}
            else:
                return {"success": False, "message": "Неверный пароль"}
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "message": "Ошибка входа"}
    
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Favicon"""
        favicon_path = Path(__file__).parent / "static" / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        # Fallback: return a tiny SVG favicon so browsers don't get 404
        svg = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>
  <rect width='64' height='64' rx='10' ry='10' fill='#1f6feb'/>
  <text x='32' y='38' font-size='28' text-anchor='middle' fill='white' font-family='Arial' font-weight='bold'>T</text>
</svg>
"""
        return HTMLResponse(content=svg, media_type='image/svg+xml')
    
    @app.get("/console", response_class=HTMLResponse)
    async def web_console():
        """Веб-консоль для отладки в реал-тайм"""
        return get_console_html()
    
    return app

def get_dashboard_html() -> str:
    """Get dashboard HTML"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Panel - Tattoo Bot</title>
        <!-- Move to unified base styles; no inline blackwork or theme-switch scripts -->
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #101010 0%, #0b0b0b 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container.dark {
                max-width: 1200px;
                margin: 0 auto;
                background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            
            .header.dark {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .content {
                padding: 30px;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .card {
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                border-color: #667eea;
            }
            
            .card-icon {
                font-size: 3em;
                margin-bottom: 10px;
            }
            
            .card h3 {
                color: #333;
                margin-bottom: 10px;
            }
            
            .card p {
                color: #666;
                font-size: 0.9em;
            }
            
            .card.admin-card {
                border: 2px solid #ff6b6b;
                background: #fff5f5;
            }
            
            .card.admin-card:hover {
                border-color: #ff6b6b;
                background: #ffe0e0;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            
            .stat-box {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
            
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                transition: all 0.3s ease;
            }
            
            .btn:hover {
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .btn-logout {
                background: #e74c3c;
            }
            
            .btn-logout:hover {
                background: #c0392b;
            }
            
            .nav {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }
            
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
        <script>
            // Apply theme on page load if user has it set
            document.addEventListener('DOMContentLoaded', function() {
                if (localStorage.getItem('theme') === 'blackwork') {
                    document.body.classList.add('blackwork-theme');
                }
            });
        </script>
        <script>
            // Define functions BEFORE they are used in onclick handlers
            function goTo(path) {
                window.location.href = path;
            }
            
            function adminFunction(funcName) {
                let message = '';
                switch(funcName) {
                    case 'edit_master':
                        message = 'Напиши ИНКЕ в Telegram: "Обнови мастера [ID]: [параметры]"\nПримеры: "Обнови мастера 1: имя Анна, ставка 5000"';
                        break;
                    case 'edit_service':
                        message = 'Напиши ИНКЕ в Telegram: "Измени услугу [ID]: [параметры]"\nПримеры: "Измени услугу 1: цена 3000"';
                        break;
                    case 'add_schedule':
                        message = 'Напиши ИНКЕ в Telegram: "Добавь слот мастеру [ID] на [дату] [время]"\nПримеры: "Добавь выходной на 2025-12-25 с 10:00 до 18:00"';
                        break;
                    case 'cancel_booking':
                        message = 'Напиши ИНКЕ в Telegram: "Отмени запись [ID] - [причина]"\nПримеры: "Отмени запись 42 - клиент отменил"';
                        break;
                    case 'export_stats':
                        message = 'Напиши ИНКЕ в Telegram: "Дай статистику по [тип]"\nТипы: revenue (доход), bookings (записи), masters (мастера), services (услуги)';
                        break;
                    case 'broadcast':
                        message = 'Напиши ИНКЕ в Telegram: "Отправь всем сообщение: [текст]"\nПримеры: "Отправь всем: новое предложение скидка 20%!"';
                        break;
                }
                alert(`👑 Инструмент администратора\n\n${message}\n\nЭто отправляется в ИНКУ через Telegram (только админы!)`);
            }
            
            function logout() {
                localStorage.removeItem('admin_token');
                window.location.href = '/login';
            }
            function toggleTheme() {
                const body = document.body;
                if (body.classList.contains('blackwork-theme')) {
                    body.classList.remove('blackwork-theme');
                    localStorage.setItem('theme', 'light');
                    document.getElementById('themeToggle').textContent = 'Tattoo Mode';
                } else {
                    body.classList.add('blackwork-theme');
                    localStorage.setItem('theme', 'blackwork');
                    document.getElementById('themeToggle').textContent = 'Light Mode';
                }
            }
        </script>
    </head>
    <body class="blackwork-theme">
        <div class="container dark">
            <div class="header dark">
                <div>
                  <h1>👨‍💼 Админ Панель</h1>
                  <p>Управление БД Тату-Салона</p>
                </div>
                <div style="display:flex;gap:12px;align-items:center;">
                    <button class="btn btn--muted" id="themeToggle" onclick="toggleTheme()">Tattoo Mode</button>
                    <button class="btn btn-logout" onclick="logout()">Выход</button>
                </div>
            </div>
            
            <div class="content">
                <div class="nav">
                    <!-- Space for future nav items / search / breadcrumbs -->
                    <div></div>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Загрузка...</p>
                </div>
                
                <div id="stats" class="stats"></div>
                
                <h2>📊 Управление</h2>
                <div class="grid" id="menu">
                    <div class="card dark" onclick="goTo('/admin/masters')">
                        <div class="card-icon"><img data-icon="master" src="/static/icons/icon-master.svg" alt="masters"/></div>
                        <h3>Мастера</h3>
                        <p>Добавить, редактировать, удалить мастеров</p>
                    </div>
                    
                    <div class="card dark" onclick="goTo('/admin/services')">
                        <div class="card-icon"><img data-icon="services" src="/static/icons/icon-services.svg" alt="services"/></div>
                        <h3>Услуги</h3>
                        <p>Управление доступными услугами</p>
                    </div>
                    
                    <div class="card dark" onclick="goTo('/admin/clients')">
                        <div class="card-icon"><img data-icon="clients" src="/static/icons/icon-clients.svg" alt="clients"/></div>
                        <h3>Клиенты</h3>
                        <p>Просмотр и управление клиентами</p>
                    </div>
                    
                    <div class="card dark" onclick="goTo('/admin/bookings')">
                        <div class="card-icon"><img data-icon="bookings" src="/static/icons/icon-bookings.svg" alt="bookings"/></div>
                        <h3>Записи</h3>
                        <p>Управление расписанием и записями</p>
                    </div>
                    
                    <div class="card" onclick="goTo('/admin/inka-training')">
                        <div class="card-icon"><img data-icon="inka" src="/static/icons/icon-inka.svg" alt="inka"/></div>
                        <h3>Обучение ИНКИ</h3>
                        <p>Автоматическое обучение и ручная корректировка сценариев</p>
                    </div>
                    <div class="card" onclick="goTo('/installer/')">
                        <div class="card-icon"><img data-icon="tools" src="/static/icons/icon-tools.svg" alt="tools"/></div>
                        <h3>Setup Wizard</h3>
                        <p>Пройдите пошаговую настройку для начальной конфигурации и деплоя</p>
                    </div>
                    
                    <div class="card" onclick="goTo('/admin/schedule')">
                        <div class="card-icon"><img data-icon="bookings" src="/static/icons/icon-bookings.svg" alt="schedule"/></div>
                        <h3>Расписание</h3>
                        <p>Календарь салона и мастеров</p>
                    </div>
                    
                    <div class="card" onclick="goTo('/admin/admins')">
                        <div class="card-icon"><img data-icon="admin" src="/static/icons/icon-admin.svg" alt="admins"/></div>
                        <h3>Админы</h3>
                        <p>Управление администраторами и паролями</p>
                    </div>
                    <div class="card dark" onclick="goTo('/admin/db-manager')">
                        <div class="card-icon"><img data-icon="dbmanager" src="/static/icons/icon-dbmanager.svg" alt="dbmanager"/></div>
                        <h3>DB Manager</h3>
                        <p>Экспорт/импорт и полная работа с листами</p>
                    </div>
                    
                    <div class="card" onclick="goTo('/console')">
                        <div class="card-icon"><img data-icon="console" src="/static/icons/icon-console.svg" alt="console"/></div>
                        <h3>Веб-Консоль</h3>
                        <p>Мониторинг в реал-тайм</p>
                    </div>
                    <div class="card" onclick="fetchMonitoringStatus()">
                        <div class="card-icon"><img data-icon="telemetry" src="/static/icons/icon-telemetry.svg" alt="monitoring"/></div>
                        <h3>Мониторинг</h3>
                        <p>Состояние: <span id="dashboard-monitor-status">-</span></p>
                    </div>
                    <div class="card">
                        <div class="card-icon"><img data-icon="history" src="/static/icons/icon-history.svg" alt="history"/></div>
                        <h3>История мониторинга</h3>
                        <p>Последние проверки: <span id="dashboard-monitor-history-count">0</span></p>
                        <button class="btn" onclick="showMonitoringHistory()">Показать историю</button>
                        <div id="monitor-history-table" style="display:none;margin-top:10px;"></div>
                    </div>
                </div>
                
                <h2 style="margin-top: 40px;">👑 Инструменты Администратора</h2>
                <div class="grid" id="admin_menu">
                    <div class="card admin-card" onclick="adminFunction('edit_master')">
                        <div class="card-icon"><img data-icon="edit" src="/static/icons/icon-edit.svg" alt="edit_master"/></div>
                        <h3>Редактировать Мастера</h3>
                        <p>Обновить информацию о мастере через ИНКУ</p>
                    </div>
                    
                    <div class="card admin-card" onclick="adminFunction('edit_service')">
                        <div class="card-icon"><img data-icon="tools" src="/static/icons/icon-tools.svg" alt="edit_service"/></div>
                        <h3>Редактировать Услугу</h3>
                        <p>Изменить цену и описание услуги</p>
                    </div>
                    
                    <div class="card admin-card" onclick="adminFunction('add_schedule')">
                        <div class="card-icon"><img data-icon="bookings" src="/static/icons/icon-bookings.svg" alt="add_schedule"/></div>
                        <h3>Добавить Слот</h3>
                        <p>Добавить выходной или отпуск</p>
                    </div>
                    
                    <div class="card admin-card" onclick="adminFunction('cancel_booking')">
                        <div class="card-icon"><img data-icon="cancel" src="/static/icons/icon-cancel.svg" alt="cancel_booking"/></div>
                        <h3>Отменить Запись</h3>
                        <p>Отменить запись клиента</p>
                    </div>
                    
                    <div class="card admin-card" onclick="adminFunction('export_stats')">
                        <div class="card-icon"><img data-icon="analytics" src="/static/icons/icon-analytics.svg" alt="export_stats"/></div>
                        <h3>Экспорт Статистики</h3>
                        <p>Получить статистику по доходам и записям</p>
                    </div>
                    
                    <div class="card admin-card" onclick="adminFunction('broadcast')">
                        <div class="card-icon"><img data-icon="broadcast" src="/static/icons/icon-broadcast.svg" alt="broadcast"/></div>
                        <h3>Рассылка</h3>
                        <p>Отправить сообщение клиентам</p>
                    </div>
                </div>
            </div>
            <script>
                async function showMonitoringHistory() {
                    try {
                        const res = await fetch('/api/monitoring/history');
                        const data = await res.json();
                        const tableDiv = document.getElementById('monitor-history-table');
                        tableDiv.style.display = 'block';
                        const rows = data.history.slice(-5).reverse();
                        tableDiv.innerHTML = '<table style="width:100%;border-collapse:collapse"><thead><tr><th>Time</th><th>OK</th></tr></thead><tbody>' + rows.map(r => `<tr><td>${new Date(r.ts*1000).toLocaleString()}</td><td>${r.summary.ok}</td></tr>`).join('') + '</tbody></table>';
                    } catch (e) {
                        console.error('Error fetching monitoring history', e);
                    }
                }
                async function fetchMonitoringStatus() {
                    try {
                        const res = await fetch('/api/monitoring/checks');
                        const data = await res.json();
                        const status = data.ok ? 'OK' : 'FAIL';
                        const el = document.getElementById('dashboard-monitor-status');
                        if (el) { el.textContent = status; el.style.color = data.ok ? '#3fb950' : '#f85149'; }
                    } catch (e) {
                        const el = document.getElementById('dashboard-monitor-status');
                        if (el) { el.textContent = 'ERROR'; el.style.color = '#f85149'; }
                    }
                }
                // Run on load
                setTimeout(fetchMonitoringStatus, 1000);
                setInterval(fetchMonitoringStatus, 60000);
            </script>
        </div>
        
        <script>
            // Функция перехода по страницам
            function goTo(path) {
                window.location.href = path;
            }
            
            // Функция выхода
            function logout() {
                localStorage.removeItem('admin_token');
                window.location.href = '/login';
            }
            
            // Функции администратора
            function adminFunction(funcName) {
                let message = '';
                
                switch(funcName) {
                    case 'edit_master':
                        message = 'Напиши ИНКЕ в Telegram: "Обнови мастера [ID]: [параметры]"\\nПримеры: "Обнови мастера 1: имя Анна, ставка 5000"';
                        break;
                    case 'edit_service':
                        message = 'Напиши ИНКЕ в Telegram: "Измени услугу [ID]: [параметры]"\\nПримеры: "Измени услугу 1: цена 3000"';
                        break;
                    case 'add_schedule':
                        message = 'Напиши ИНКЕ в Telegram: "Добавь слот мастеру [ID] на [дату] [время]"\\nПримеры: "Добавь выходной на 2025-12-25 с 10:00 до 18:00"';
                        break;
                    case 'cancel_booking':
                        message = 'Напиши ИНКЕ в Telegram: "Отмени запись [ID] - [причина]"\\nПримеры: "Отмени запись 42 - клиент отменил"';
                        break;
                    case 'export_stats':
                        message = 'Напиши ИНКЕ в Telegram: "Дай статистику по [тип]"\\nТипы: revenue (доход), bookings (записи), masters (мастера), services (услуги)';
                        break;
                    case 'broadcast':
                        message = 'Напиши ИНКЕ в Telegram: "Отправь всем сообщение: [текст]"\\nПримеры: "Отправь всем: новое предложение скидка 20%!"';
                        break;
                }
                
                alert('👑 Инструмент администратора\\n\\n' + message + '\\n\\nЭто отправляется в ИНКУ через Telegram (только админы!)');
            }
            
            // Load stats when page loads
            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    const statsDiv = document.getElementById('stats');
                    const statsHTML = `<div class="stat-box"><div class="stat-value">${data.clients_count}</div><div class="stat-label">Клиентов</div></div><div class="stat-box"><div class="stat-value">${data.masters_count}</div><div class="stat-label">Мастеров</div></div><div class="stat-box"><div class="stat-value">${data.services_count}</div><div class="stat-label">Услуг</div></div><div class="stat-box"><div class="stat-value">${data.bookings_count}</div><div class="stat-label">Записей</div></div>`;
                    statsDiv.innerHTML = statsHTML;
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }
            
            // Load on page load
            document.addEventListener('DOMContentLoaded', () => {
                loadStats();
            });
        </script>
    </body>
    </html>
    """

def get_login_html() -> str:
    """Get login page HTML"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Tattoo Bot</title>
        <link rel="stylesheet" href="/static/blackwork.css">
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                if (localStorage.getItem('theme') === 'blackwork') {
                    document.body.classList.add('blackwork-theme');
                }
            });
        </script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: var(--bg);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .login-box {
                background: var(--card);
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                width: 100%;
                max-width: 400px;
            }
            
            .login-box h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
                font-size: 1.8em;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 500;
            }
            
            .form-group input {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                font-size: 1em;
                transition: all 0.3s ease;
            }
            
            .form-group input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 10px rgba(102, 126, 234, 0.2);
            }
            
            .btn {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 1em;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: bold;
            }
            
            .btn:hover {
                transform: scale(1.02);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .error {
                display: none;
                background: #e74c3c;
                color: white;
                padding: 12px;
                border-radius: 5px;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .loading {
                display: none;
                text-align: center;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
        <script>
            // Define functions before they are used
            function clearLogs() {
                document.getElementById('logs').innerHTML = '';
                document.getElementById('logCount').textContent = '0';
            }
            
            async function testAllEndpoints() {
                const endpoints = ['/api/stats', '/api/masters', '/api/services', '/api/clients', '/api/bookings'];
                const logDiv = document.getElementById('logs');
                const results = [];
                
                for (const endpoint of endpoints) {
                    try {
                        const response = await fetch(endpoint);
                        const status = response.status;
                        results.push({endpoint, status, ok: response.ok});
                        logDiv.innerHTML += `<div class="log-entry" style="color: ${response.ok ? 'green' : 'red'}">[${new Date().toLocaleTimeString()}] ${endpoint}: ${status}</div>`;
                    } catch (error) {
                        results.push({endpoint, status: 'ERROR', ok: false});
                        logDiv.innerHTML += `<div class="log-entry" style="color: red">[${new Date().toLocaleTimeString()}] ${endpoint}: ERROR - ${error.message}</div>`;
                    }
                }
                
                document.getElementById('logCount').textContent = results.length;
            }
        </script>
    </head>
    <body>
        <div class="login-box">
            <h1>🔐 Вход</h1>
            
            <div class="error" id="error"></div>
            
            <form id="loginForm" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label for="username">Логин:</label>
                    <input type="text" id="username" name="username" placeholder="admin" autofocus>
                </div>
                
                <div class="form-group">
                    <label for="password">Пароль:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="btn" id="submitBtn">Войти</button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
            </div>
        </div>
        
        <script>
            async function handleLogin(event) {
                event.preventDefault();
                
                const username = document.getElementById('username').value.trim();
                const password = document.getElementById('password').value;
                const errorDiv = document.getElementById('error');
                const submitBtn = document.getElementById('submitBtn');
                const loading = document.getElementById('loading');
                
                errorDiv.style.display = 'none';
                submitBtn.style.display = 'none';
                loading.style.display = 'block';
                
                try {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ username, password })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        localStorage.setItem('admin_token', data.token);
                        window.location.href = '/';
                    } else {
                        errorDiv.textContent = data.message;
                        errorDiv.style.display = 'block';
                        submitBtn.style.display = 'block';
                        loading.style.display = 'none';
                        document.getElementById('password').value = '';
                    }
                } catch (error) {
                    errorDiv.textContent = 'Ошибка соединения';
                    errorDiv.style.display = 'block';
                    submitBtn.style.display = 'block';
                    loading.style.display = 'none';
                    console.error('Login error:', error);
                }
            }
            
            // Check if already logged in
            if (localStorage.getItem('admin_token')) {
                window.location.href = '/';
            }
        </script>
    </body>
    </html>
    """

def get_console_html() -> str:
    """Get web console HTML for real-time debugging"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔍 Веб-консоль - Admin Panel</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Courier New', monospace;
                background: #0d1117;
                color: #c9d1d9;
                overflow: hidden;
                height: 100vh;
            }

            .container {
                display: flex;
                height: 100vh;
                gap: 1px;
            }

            .panel {
                flex: 1;
                display: flex;
                flex-direction: column;
                border-right: 1px solid #30363d;
                overflow: hidden;
            }

            .header {
                background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%);
                padding: 15px 20px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-bottom: 2px solid #30363d;
            }

            .logs {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background: #0d1117;
            }

            .log-entry {
                margin-bottom: 8px;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
                line-height: 1.4;
                border-left: 3px solid #30363d;
            }

            .log-entry.info {
                border-left-color: #58a6ff;
                background: rgba(88, 166, 255, 0.1);
            }

            .log-entry.success {
                border-left-color: #3fb950;
                background: rgba(63, 185, 80, 0.1);
                color: #3fb950;
            }

            .log-entry.error {
                border-left-color: #f85149;
                background: rgba(248, 81, 73, 0.1);
                color: #f85149;
            }

            .log-entry.warning {
                border-left-color: #d29922;
                background: rgba(210, 153, 34, 0.1);
                color: #d29922;
            }

            .log-entry.request {
                border-left-color: #79c0ff;
                background: rgba(121, 192, 255, 0.1);
            }

            .timestamp {
                color: #8b949e;
                margin-right: 8px;
            }

            .stats {
                background: #161b22;
                padding: 15px;
                border-top: 2px solid #30363d;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }

            .stat-item {
                padding: 10px;
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
            }

            .stat-label {
                color: #8b949e;
                display: block;
                margin-bottom: 5px;
            }

            .stat-value {
                font-size: 18px;
                font-weight: bold;
                color: #58a6ff;
            }

            .controls {
                background: #161b22;
                padding: 10px;
                border-top: 1px solid #30363d;
                display: flex;
                gap: 5px;
            }

            button {
                flex: 1;
                padding: 8px;
                background: #238636;
                color: white;
                border: 1px solid #2ea043;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                font-family: monospace;
            }

            button:hover {
                background: #2ea043;
            }

            button.clear {
                background: #da3633;
                border-color: #f85149;
            }

            button.clear:hover {
                background: #f85149;
            }

            .status-indicator {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 5px;
                animation: pulse 2s infinite;
            }

            .status-indicator.online {
                background: #3fb950;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .endpoints {
                display: grid;
                grid-template-columns: 1fr;
                gap: 5px;
                padding: 10px;
                background: #161b22;
                border-top: 1px solid #30363d;
                max-height: 200px;
                overflow-y: auto;
            }

            .endpoint-btn {
                padding: 8px;
                background: #0d3cc4;
                color: #79c0ff;
                border: 1px solid #1f6feb;
                border-radius: 3px;
                cursor: pointer;
                font-size: 11px;
                text-align: left;
            }

            .endpoint-btn:hover {
                background: #1f6feb;
            }

            .endpoint-btn.status-200 {
                border-left: 4px solid #3fb950;
            }

            .endpoint-btn.status-404 {
                border-left: 4px solid #f85149;
            }

            .endpoint-btn.status-loading {
                border-left: 4px solid #d29922;
            }
        </style>
        <script>
            // ===== Variables & State =====
            var logs = window.logs || [];
            var eventCount = window.eventCount || 0;
            var errorCount = window.errorCount || 0;
            var apiCount = window.apiCount || 0;
            var logsContainer = window.logsContainer || null;
            
            const endpoints = [
                {name: 'Stats', url: '/api/stats'},
                {name: 'Masters', url: '/api/masters'},
                {name: 'Services', url: '/api/services'},
                {name: 'Clients', url: '/api/clients'},
                {name: 'Bookings', url: '/api/bookings'},
                {name: 'INKA Training', url: '/api/inka-training-stats'}
            ];
            
            // ===== Log Functions =====
            function addLog(message, type = 'info') {
                const timestamp = new Date().toLocaleTimeString('ru-RU');
                const entry = {message, type, timestamp};
                logs.unshift(entry);
                eventCount++;
                if (type === 'error') errorCount++;
                if (type === 'request') apiCount++;
                if (logs.length > 100) logs.pop();
                renderLogs();
                updateStats();
                window.logs = logs; window.eventCount = eventCount; window.errorCount = errorCount; window.apiCount = apiCount;
            }
            
            function renderLogs() {
                if (logsContainer) {
                    logsContainer.innerHTML = logs.map(log => `<div class="log-entry ${log.type}"><span class="timestamp">[${log.timestamp}]</span> ${log.message}</div>`).join('');
                    logsContainer.scrollTop = 0;
                }
            }
            
            function updateStats() {
                const totalElem = document.getElementById('total-events');
                const errorElem = document.getElementById('error-count');
                const apiElem = document.getElementById('api-count');
                const lastElem = document.getElementById('last-update');
                if (totalElem) totalElem.textContent = eventCount;
                if (errorElem) errorElem.textContent = errorCount;
                if (apiElem) apiElem.textContent = apiCount;
                if (lastElem) lastElem.textContent = new Date().toLocaleTimeString('ru-RU');
            }
            
            function clearLogs() {
                logs = [];
                eventCount = 0;
                errorCount = 0;
                apiCount = 0;
                renderLogs();
                updateStats();
                window.logs = logs; window.eventCount = eventCount; window.errorCount = errorCount; window.apiCount = apiCount;
                addLog('✅ Логи очищены', 'success');
            }
            
            async function testEndpoint(endpoint) {
                try {
                    const startTime = performance.now();
                    const response = await fetch(endpoint.url, {signal: AbortSignal.timeout(5000)});
                    const duration = Math.round(performance.now() - startTime);
                    const status = response.status;
                    addLog(`🌐 ${endpoint.name}: ${endpoint.url} → ${status} (${duration}ms)`, 'request');
                    return {endpoint, status, duration};
                } catch (error) {
                    addLog(`❌ ${endpoint.name}: ${error.message}`, 'error');
                    return {endpoint, status: 'error', duration: '-'};
                }
            }
            
            async function testAllEndpoints() {
                addLog('🧪 Начало тестирования...', 'warning');
                for (const endpoint of endpoints) {
                    await testEndpoint(endpoint);
                    await new Promise(r => setTimeout(r, 200));
                }
                addLog('✅ Тестирование завершено', 'success');
            }
            
            function renderEndpoints() {
                const endpointsContainer = document.getElementById('endpoints-container');
                if (endpointsContainer) {
                    endpointsContainer.innerHTML = endpoints.map(ep => `<button class="endpoint-btn" onclick="testEndpoint({name: '${ep.name}', url: '${ep.url}'})">${ep.name} → ${ep.url}</button>`).join('');
                }
            }

            async function sendTelemetry(payload) {
                try {
                    await fetch('/api/telemetry/events', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                } catch (e) {
                    console.warn('Telemetry send failed', e);
                }
            }
            
            function initLogging() {
                logsContainer = document.getElementById('logs');
                const originalLog = console.log;
                const originalError = console.error;
                const originalWarn = console.warn;
                
                console.log = function(...args) {
                    originalLog(...args);
                    addLog(`📝 ${args.join(' ')}`, 'info');
                };
                
                console.error = function(...args) {
                    originalError(...args);
                    addLog(`❌ ${args.join(' ')}`, 'error');
                    try { sendTelemetry({event_type: 'ui_error', message: args.join(' '), meta: { source: 'dashboard' }}); } catch(e) {}
                };
                
                console.warn = function(...args) {
                    originalWarn(...args);
                    addLog(`⚠️ ${args.join(' ')}`, 'warning');
                    try { sendTelemetry({event_type: 'ui_warning', message: args.join(' '), meta: { source: 'dashboard' }}); } catch(e) {}
                };
                
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    const url = args[0];
                    addLog(`📤 Fetch: ${url}`, 'request');
                    return originalFetch.apply(this, args).then(response => {
                        addLog(`📥 Response: ${url} → ${response.status}`, response.status >= 400 ? 'error' : 'success');
                        return response;
                    });
                };
                
                renderEndpoints();
                setTimeout(testAllEndpoints, 1000);
                setInterval(testAllEndpoints, 30000);
            }
        </script>
        <script>
            // Initialize dev panel when page loads
            document.addEventListener('DOMContentLoaded', () => {
                initLogging();
            });
        </script>
    </head>
    <body>
        <div class="container">
            <div class="panel" style="flex: 2;">
                <div class="header">🔍 ЛОГИ РЕАЛ-ТАЙМ (Browser Console)</div>
                <div class="logs" id="logs"></div>
                <div class="stats">
                    <div class="stat-item">
                        <span class="stat-label">Всего событий</span>
                        <span class="stat-value" id="total-events">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Ошибок</span>
                        <span class="stat-value" id="error-count" style="color: #f85149;">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">API запросов</span>
                        <span class="stat-value" id="api-count" style="color: #79c0ff;">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Статус</span>
                        <span class="stat-value"><span class="status-indicator online"></span>Online</span>
                    </div>
                </div>
                <div class="controls">
                    <button onclick="clearLogs()">🗑️ Очистить</button>
                    <button onclick="testAllEndpoints()">🧪 Тест</button>
                    <button onclick="location.href='/'">🏠 Назад</button>
                </div>
            </div>

            <div class="panel" style="flex: 1;">
                <div class="header">📊 ЭНДПОИНТЫ</div>
                <div class="endpoints" id="endpoints"></div>
                <div style="flex: 1; overflow-y: auto; padding: 15px; background: #0d1117; font-size: 11px;">
                    <p style="margin-bottom: 10px;"><strong>✅ Статус:</strong></p>
                    <p style="margin-bottom: 5px;">🟢 Веб: <span id="web-status" style="color: #3fb950;">Online</span></p>
                    <p style="margin-bottom: 10px;">🟢 API: <span id="api-status" style="color: #3fb950;">OK</span></p>
                    <p style="margin-bottom: 10px;"><strong>⏱️  Время ответа:</strong></p>
                    <p id="response-time">-ms</p>
                    <p style="margin-top: 10px; color: #8b949e; font-size: 10px;">Обновлено: <span id="last-update">-</span></p>
                </div>
            </div>
        </div>

        <script>
            var logsContainer = window.logsContainer || document.getElementById('logs');
            var endpointsContainer = window.endpointsContainer || document.getElementById('endpoints');
            window.logsContainer = logsContainer;
            window.endpointsContainer = endpointsContainer;
            var logs = window.logs || [];
            var eventCount = window.eventCount || 0;
            var errorCount = window.errorCount || 0;
            var apiCount = window.apiCount || 0;

            const endpoints = [
                { name: '✅ Health', url: '/api/health' },
                { name: '📊 Stats', url: '/api/stats' },
                { name: '👨 Masters', url: '/api/masters' },
                { name: '✂️ Services', url: '/api/services' },
                { name: '👤 Clients', url: '/api/clients' },
                { name: '📅 Bookings', url: '/api/bookings' },
            ];

            function addLog(message, type = 'info') {
                const timestamp = new Date().toLocaleTimeString('ru-RU');
                const entry = { message, type, timestamp };
                logs.unshift(entry);
                eventCount++;

                if (type === 'error') errorCount++;
                if (type === 'request') apiCount++;

                if (logs.length > 100) logs.pop();
                renderLogs();
                updateStats();
            }

            function renderLogs() {
                logsContainer.innerHTML = logs.map(log => `
                    <div class="log-entry ${log.type}">
                        <span class="timestamp">[${log.timestamp}]</span>
                        ${log.message}
                    </div>
                `).join('');
                logsContainer.scrollTop = 0;
            }

            function updateStats() {
                document.getElementById('total-events').textContent = eventCount;
                document.getElementById('error-count').textContent = errorCount;
                document.getElementById('api-count').textContent = apiCount;
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString('ru-RU');
            }

            function clearLogs() {
                logs = [];
                eventCount = 0;
                errorCount = 0;
                apiCount = 0;
                renderLogs();
                updateStats();
                addLog('✅ Логи очищены', 'success');
            }

            async function testEndpoint(endpoint) {
                try {
                    const startTime = performance.now();
                    const response = await fetch(endpoint.url, { signal: AbortSignal.timeout(5000) });
                    const duration = Math.round(performance.now() - startTime);
                    const status = response.status;
                    const statusClass = status === 200 ? 'status-200' : 'status-404';
                    
                    addLog(`🌐 ${endpoint.name}: ${endpoint.url} → ${status} (${duration}ms)`, 'request');
                    return { endpoint, status, duration };
                } catch (error) {
                    addLog(`❌ ${endpoint.name}: ${error.message}`, 'error');
                    return { endpoint, status: 'error', duration: '-' };
                }
            }

            async function testAllEndpoints() {
                addLog('🧪 Начало тестирования...', 'warning');
                for (const endpoint of endpoints) {
                    await testEndpoint(endpoint);
                    await new Promise(r => setTimeout(r, 200));
                }
                addLog('✅ Тестирование завершено', 'success');
            }

            function renderEndpoints() {
                endpointsContainer.innerHTML = endpoints.map(ep => `
                    <button class="endpoint-btn status-loading" onclick="testEndpoint({name: '${ep.name}', url: '${ep.url}'})">
                        ${ep.name} → ${ep.url}
                    </button>
                `).join('');
            }

            const originalLog = console.log;
            const originalError = console.error;
            const originalWarn = console.warn;

            console.log = function(...args) {
                originalLog(...args);
                addLog(`📝 ${args.join(' ')}`, 'info');
            };

            console.error = function(...args) {
                originalError(...args);
                addLog(`❌ ${args.join(' ')}`, 'error');
            };

            console.warn = function(...args) {
                originalWarn(...args);
                addLog(`⚠️ ${args.join(' ')}`, 'warning');
            };

            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const url = args[0];
                addLog(`📤 Fetch: ${url}`, 'request');
                return originalFetch.apply(this, args)
                    .then(response => {
                        addLog(`📥 Response: ${url} → ${response.status}`, 
                            response.status >= 400 ? 'error' : 'success');
                        return response;
                    })
                    .catch(error => {
                        addLog(`❌ Fetch Error: ${url} → ${error.message}`, 'error');
                        throw error;
                    });
            };

            window.addEventListener('error', (event) => {
                addLog(`💥 JS Error: ${event.message}`, 'error');
            });

            window.addEventListener('unhandledrejection', (event) => {
                addLog(`💥 Promise Error: ${event.reason}`, 'error');
            });

            addLog('🚀 Веб-консоль запущена', 'success');
            renderEndpoints();
            updateStats();
            setTimeout(testAllEndpoints, 1000);
            setInterval(testAllEndpoints, 30000);
        </script>
    </body>
    </html>
    """
