"""
FastAPI Web Interface для управления БД
"""

import os
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional, List, Dict

from src.config import get_config
from src.services.admin_db_manager import DatabaseManager, InkaLearningSystem
from src.web.auth import check_admin_password
from src.web.api import routers

logger = logging.getLogger(__name__)

# Initialize managers
db_manager: Optional[DatabaseManager] = None
learning_system: Optional[InkaLearningSystem] = None

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    global db_manager, learning_system
    
    config = get_config()
    
    app = FastAPI(
        title="Tattoo Bot Admin",
        description="Веб-интерфейс для управления БД тату-салона",
        version="1.0.0"
    )
    
    # Initialize managers
    try:
        from src.db.sheets_client import GoogleSheetsClient
        
        # Get credentials file path from env or use default
        creds_file = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")
        
        sheets_client = GoogleSheetsClient(
            credentials_file=creds_file,
            spreadsheet_id=config.google_spreadsheet_id
        )
        db_manager = DatabaseManager(sheets_client)
        try:
            learning_system = InkaLearningSystem(sheets_client)
        except Exception as inka_error:
            logger.warning(f"⚠️ INKA Learning System initialization failed (non-critical): {inka_error}")
            learning_system = None
        
        logger.info("✅ Database managers initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize database manager: {e}")
        db_manager = None
        learning_system = None
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Include API routers
    app.include_router(routers.api_router)
    
    # Include admin pages router
    from src.web.pages import admin_router
    app.include_router(admin_router)
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Главная страница"""
        return get_dashboard_html()
    
    @app.get("/login", response_class=HTMLResponse)
    async def login_page():
        """Страница входа"""
        return get_login_html()
    
    @app.post("/api/login")
    async def login(request: Request):
        """Вход в систему"""
        try:
            body = await request.json()
            password = body.get("password", "")
            
            if check_admin_password(password, get_config().admin_password):
                return {
                    "success": True,
                    "token": "admin_token_123",  # В production использовать JWT
                    "message": "Успешный вход"
                }
            else:
                return {
                    "success": False,
                    "message": "Неверный пароль"
                }
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "message": "Ошибка входа"}
    
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Favicon"""
        favicon_path = Path(__file__).parent / "static" / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        return JSONResponse(status_code=404, content={})
    
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
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            
            .header {
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
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👨‍💼 Админ Панель</h1>
                <p>Управление БД Тату-Салона</p>
            </div>
            
            <div class="content">
                <div class="nav">
                    <div></div>
                    <button class="btn btn-logout" onclick="logout()">Выход</button>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Загрузка...</p>
                </div>
                
                <div id="stats" class="stats"></div>
                
                <h2>📊 Управление</h2>
                <div class="grid" id="menu">
                    <div class="card" onclick="goTo('/admin/masters')">
                        <div class="card-icon">👥</div>
                        <h3>Мастера</h3>
                        <p>Добавить, редактировать, удалить мастеров</p>
                    </div>
                    
                    <div class="card" onclick="goTo('/admin/services')">
                        <div class="card-icon">💼</div>
                        <h3>Услуги</h3>
                        <p>Управление доступными услугами</p>
                    </div>
                    
                    <div class="card" onclick="goTo('/admin/clients')">
                        <div class="card-icon">👤</div>
                        <h3>Клиенты</h3>
                        <p>Просмотр и управление клиентами</p>
                    </div>
                    
                    <div class="card" onclick="goTo('/admin/bookings')">
                        <div class="card-icon">📅</div>
                        <h3>Записи</h3>
                        <p>Управление расписанием и записями</p>
                    </div>
                    
                    <div class="card" onclick="goTo('/admin/inka-training')">
                        <div class="card-icon">🧠</div>
                        <h3>Обучение ИНКИ</h3>
                        <p>Обучение ассистента и статистика</p>
                    </div>
                    
                    <div class="card" onclick="goTo('/admin/analytics')">
                        <div class="card-icon">📈</div>
                        <h3>Аналитика</h3>
                        <p>Статистика и отчеты</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Load stats
            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    
                    const statsDiv = document.getElementById('stats');
                    statsDiv.innerHTML = `
                        <div class="stat-box">
                            <div class="stat-value">${data.clients_count}</div>
                            <div class="stat-label">Клиентов</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${data.masters_count}</div>
                            <div class="stat-label">Мастеров</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${data.services_count}</div>
                            <div class="stat-label">Услуг</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">${data.bookings_count}</div>
                            <div class="stat-label">Записей</div>
                        </div>
                    `;
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }
            
            function goTo(path) {
                window.location.href = path;
            }
            
            function logout() {
                localStorage.removeItem('admin_token');
                window.location.href = '/login';
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
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .login-box {
                background: white;
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
    </head>
    <body>
        <div class="login-box">
            <h1>🔐 Вход</h1>
            
            <div class="error" id="error"></div>
            
            <form id="loginForm" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label for="password">Пароль администратора:</label>
                    <input type="password" id="password" name="password" required autofocus>
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
                        body: JSON.stringify({ password })
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
