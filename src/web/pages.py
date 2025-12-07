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
        <script>
            // Define event handlers BEFORE they are called
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
        </script>
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
                    tbody.innerHTML = masters.map(m => {
                        return `<tr><td>${m.id || '-'}</td><td>${m.name || '-'}</td><td>${m.specialization || '-'}</td><td>${m.phone || '-'}</td><td><button class="btn-edit" data-id="${m.id}" style="margin-right:5px">✏️ Редактировать</button><button class="btn-delete" data-id="${m.id}" style="background:#e74c3c">🗑️ Удалить</button></td></tr>`;
                    }).join('');
                    document.querySelectorAll('.btn-edit').forEach(btn => {
                        btn.addEventListener('click', () => editMaster(btn.dataset.id));
                    });
                    document.querySelectorAll('.btn-delete').forEach(btn => {
                        btn.addEventListener('click', () => deleteMaster(btn.dataset.id));
                    });
                } catch (error) {
                    console.error('Error loading masters:', error);
                    document.getElementById('mastersList').innerHTML = '<tr><td colspan="5">Ошибка загрузки</td></tr>';
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
        <script>
            function editService(id) {
                alert('Редактирование услуги ' + id);
            }
            
            function deleteService(id) {
                if (confirm('Удалить услугу?')) {
                    alert('Функция удаления будет реализована');
                }
            }
        </script>
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
                    <tbody id="servicesList">
                        <tr><td colspan="5" style="text-align:center">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        <script>
            async function loadServices() {
                try {
                    const response = await fetch('/api/services');
                    const services = await response.json();
                    const tbody = document.getElementById('servicesList');
                    if (!services || services.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">Нет услуг</td></tr>';
                        return;
                    }
                    tbody.innerHTML = services.map(s => {
                        const price = s.price_from && s.price_to ? `${s.price_from} - ${s.price_to}` : (s.price_from || '-');
                        return `<tr><td>${s.id || '-'}</td><td>${s.name || '-'}</td><td>${price}</td><td>${s.duration_min || '-'}</td><td><button class="btn-edit" data-id="${s.id}" style="margin-right:5px">✏️</button><button class="btn-delete" data-id="${s.id}" style="background:#e74c3c">🗑️</button></td></tr>`;
                    }).join('');
                    document.querySelectorAll('.btn-edit').forEach(btn => {
                        btn.addEventListener('click', () => editService(btn.dataset.id));
                    });
                    document.querySelectorAll('.btn-delete').forEach(btn => {
                        btn.addEventListener('click', () => deleteService(btn.dataset.id));
                    });
                } catch (error) {
                    console.error('Error loading services:', error);
                    document.getElementById('servicesList').innerHTML = '<tr><td colspan="5">Ошибка загрузки</td></tr>';
                }
            }
            
            loadServices();
        </script>
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
        <script>
            function deleteClient(id) {
                if (confirm('Удалить клиента?')) {
                    alert('Функция удаления будет реализована');
                }
            }
            
            function viewClient(id) {
                alert('Просмотр клиента ' + id);
            }
        </script>
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
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody id="clientsList">
                        <tr><td colspan="5" style="text-align:center">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        <script>
            async function loadClients() {
                try {
                    const response = await fetch('/api/clients');
                    const clients = await response.json();
                    const tbody = document.getElementById('clientsList');
                    if (!clients || clients.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">Нет клиентов</td></tr>';
                        return;
                    }
                    tbody.innerHTML = clients.map(c => {
                        return `<tr><td>${c.id || '-'}</td><td>${c.name || '-'}</td><td>${c.phone || '-'}</td><td>${c.email || '-'}</td><td><button class="btn-view" data-id="${c.id}" style="margin-right:5px">👁️</button><button class="btn-delete" data-id="${c.id}" style="background:#e74c3c">🗑️</button></td></tr>`;
                    }).join('');
                    document.querySelectorAll('.btn-view').forEach(btn => {
                        btn.addEventListener('click', () => viewClient(btn.dataset.id));
                    });
                    document.querySelectorAll('.btn-delete').forEach(btn => {
                        btn.addEventListener('click', () => deleteClient(btn.dataset.id));
                    });
                } catch (error) {
                    console.error('Error loading clients:', error);
                    document.getElementById('clientsList').innerHTML = '<tr><td colspan="5">Ошибка загрузки</td></tr>';
                }
            }
            
            loadClients();
        </script>
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
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody id="bookingsList">
                        <tr><td colspan="7" style="text-align:center">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        <script>
            async function loadBookings() {
                try {
                    const response = await fetch('/api/bookings');
                    const bookings = await response.json();
                    
                    const tbody = document.getElementById('bookingsList');
                    if (!bookings || bookings.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center">Нет записей</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = bookings.map(b => {
                        return `<tr><td>${b.id || '-'}</td><td>${b.client_id || '-'}</td><td>${b.master_id || '-'}</td><td>${b.service_id || '-'}</td><td>${b.date || '-'} ${b.time || ''}</td><td>${b.status || '-'}</td><td><button class="btn-cancel" data-id="${b.id}" style="background:#e74c3c">❌</button></td></tr>`;
                    }).join('');
                    
                    document.querySelectorAll('.btn-cancel').forEach(btn => {
                        btn.addEventListener('click', () => cancelBooking(btn.dataset.id));
                    });
                } catch (error) {
                    console.error('Error loading bookings:', error);
                    document.getElementById('bookingsList').innerHTML = '<tr><td colspan="7">Ошибка загрузки</td></tr>';
                }
            }
            
            function cancelBooking(id) {
                if (confirm('Отменить запись?')) {
                    alert('Функция отмены будет реализована');
                }
            }
            
            loadBookings();
        </script>
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
        <script>
            async function trainInka() {
                const text = document.getElementById('trainingText').value;
                if (!text) {
                    alert('Введите текст для обучения');
                    return;
                }
                try {
                    const response = await fetch('/api/inka-training', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text})
                    });
                    if (response.ok) {
                        alert('Обучение начато!');
                        document.getElementById('trainingText').value = '';
                    } else {
                        alert('Ошибка при обучении');
                    }
                } catch (error) {
                    console.error('Training error:', error);
                    alert('Ошибка подключения');
                }
            }
        </script>
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
