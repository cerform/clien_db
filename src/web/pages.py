"""Admin pages for web interface"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.get("")
async def admin_root():
    """Redirect to main admin dashboard"""
    return RedirectResponse(url="/", status_code=302)

@admin_router.get("/")
async def admin_slash():
    """Admin root with slash"""
    return RedirectResponse(url="/", status_code=302)

@admin_router.get("/masters", response_class=HTMLResponse)
async def masters_page():
    """Masters management page"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Мастера - Admin Panel</title>
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
                padding: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
            
            .btn-back {
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .btn-back:hover {
                background: rgba(255,255,255,0.3);
            }
            
            .content {
                padding: 30px;
            }
            
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin-bottom: 20px;
            }
            
            .btn:hover {
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .table-container {
                overflow-x: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            
            th {
                background: #f5f5f5;
                font-weight: bold;
            }
            
            tr:hover {
                background: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👥 Управление Мастерами</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            
            <div class="content">
                <button class="btn" onclick="addMaster()">➕ Добавить мастера</button>
                
                <div class="table-container">
                    <table id="mastersTable">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Имя</th>
                                <th>Специализация</th>
                                <th>Опыт (лет)</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody id="mastersList">
                            <tr><td colspan="5" style="text-align:center">Загрузка...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script>
            async function loadMasters() {
                try {
                    const response = await fetch('/api/masters');
                    const masters = await response.json();
                    
                    const tbody = document.getElementById('mastersList');
                    if (masters.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">Нет мастеров</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = masters.map(m => `<tr><td>${m.id || '-'}</td><td>${m.name || '-'}</td><td>${m.specialization || '-'}</td><td>${m.experience_years || '-'}</td><td><button onclick="editMaster(${m.id})" style="margin-right:5px">✏️ Редактировать</button><button onclick="deleteMaster(${m.id})" style="background:#e74c3c">🗑️ Удалить</button></td></tr>`).join('');
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('mastersList').innerHTML = '<tr><td colspan="5">Ошибка загрузки</td></tr>';
                }
            }
            
            function addMaster() {
                alert('Функция добавления мастера будет реализована');
            }
            
            function editMaster(id) {
                alert('Функция редактирования мастера будет реализована');
            }
            
            function deleteMaster(id) {
                if (confirm('Вы уверены?')) {
                    alert('Функция удаления мастера будет реализована');
                }
            }
            
            loadMasters();
        </script>
    </body>
    </html>
    """

@admin_router.get("/services", response_class=HTMLResponse)
async def services_page():
    """Services management page"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Услуги - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 30px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; border: none; padding: 10px 20px; border-radius: 5px;
                  cursor: pointer; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💼 Управление Услугами</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <button class="btn">➕ Добавить услугу</button>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Название</th>
                            <th>Цена</th>
                            <th>Длительность (мин)</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="5" style="text-align:center">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

@admin_router.get("/clients", response_class=HTMLResponse)
async def clients_page():
    """Clients management page"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Клиенты - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 30px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; border: none; padding: 10px 20px; border-radius: 5px;
                  cursor: pointer; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👤 Управление Клиентами</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Имя</th>
                            <th>Телефон</th>
                            <th>Email</th>
                            <th>Записей</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="5" style="text-align:center">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

@admin_router.get("/bookings", response_class=HTMLResponse)
async def bookings_page():
    """Bookings management page"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Записи - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 30px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📅 Управление Записями</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Клиент</th>
                            <th>Мастер</th>
                            <th>Услуга</th>
                            <th>Дата и время</th>
                            <th>Статус</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="6" style="text-align:center">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

@admin_router.get("/inka-training", response_class=HTMLResponse)
async def inka_training_page():
    """INKA training page"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Обучение ИНКИ - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 30px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; border: none; padding: 10px 20px; border-radius: 5px;
                  cursor: pointer; }
            textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 20px; }
            .stat-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
                       padding: 20px; border-radius: 8px; text-align: center; }
            .stat-value { font-size: 2em; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧠 Обучение ИНКИ</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <h2>📈 Статистика</h2>
                <div class="stats" id="stats"></div>
                
                <h2 style="margin-top:30px">📚 Добавить данные для обучения</h2>
                <textarea id="trainingText" placeholder="Введите текст для обучения..." rows="5"></textarea>
                <button class="btn" style="margin-top:10px" onclick="trainInka()">🚀 Обучить ИНКУ</button>
            </div>
        </div>
        
        <script>
            async function loadStats() {
                const response = await fetch('/api/inka-training-stats');
                const data = await response.json();
                
                const statsHTML = `<div class="stat-box"><div class="stat-value">${data.total_sessions || 0}</div><div>Всего сеансов</div></div><div class="stat-box"><div class="stat-value">${data.successful_trainings || 0}</div><div>Успешных</div></div><div class="stat-box"><div class="stat-value">${(data.average_score || 0).toFixed(2)}</div><div>Средний рейтинг</div></div>`;
                document.getElementById('stats').innerHTML = statsHTML;
            }
            
            async function trainInka() {
                const text = document.getElementById('trainingText').value;
                if (!text) {
                    alert('Введите текст для обучения');
                    return;
                }
                
                try {
                    const response = await fetch('/api/inka-training', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text })
                    });
                    const result = await response.json();
                    alert('Обучение запущено!');
                    document.getElementById('trainingText').value = '';
                    loadStats();
                } catch (error) {
                    alert('Ошибка: ' + error);
                }
            }
            
            loadStats();
        </script>
    </body>
    </html>
    """

@admin_router.get("/analytics", response_class=HTMLResponse)
async def analytics_page():
    """Analytics page"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Аналитика - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 30px; }
            .chart { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📈 Аналитика</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <h2>📊 Статистика системы</h2>
                <div class="chart">
                    <p>Графики и аналитика будут добавлены...</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
