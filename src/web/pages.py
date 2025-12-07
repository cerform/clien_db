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
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   min-height: 100vh; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); overflow: hidden; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; transition: all 0.3s; }
            .btn-back:hover { background: rgba(255,255,255,0.3); }
            .content { padding: 30px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; border: none; padding: 10px 20px; border-radius: 5px;
                  cursor: pointer; margin-bottom: 20px; transition: all 0.3s; }
            .btn:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
            .btn-edit { background: #3498db; color: white; border: none; padding: 8px 12px;
                       border-radius: 4px; cursor: pointer; margin-right: 5px; }
            .btn-delete { background: #e74c3c; color: white; border: none; padding: 8px 12px;
                         border-radius: 4px; cursor: pointer; }
            .table-container { overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; font-weight: bold; }
            tr:hover { background: #f9f9f9; }
            
            /* Modal styles */
            .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0;
                    width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
            .modal-content { background-color: white; margin: 5% auto; padding: 30px;
                            border-radius: 10px; width: 90%; max-width: 500px;
                            box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .modal-header { display: flex; justify-content: space-between; align-items: center;
                           margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
            .modal-header h2 { color: #333; }
            .close { color: #aaa; font-size: 28px; font-weight: bold; cursor: pointer; }
            .close:hover { color: #333; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; color: #333; font-weight: 500; }
            .form-group input, .form-group select, .form-group textarea {
                width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px;
                font-size: 14px; transition: border-color 0.3s; }
            .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
                outline: none; border-color: #667eea; }
            .form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
            .btn-cancel { background: #95a5a6; }
            .btn-save { background: #27ae60; }
            .status-active { color: #27ae60; font-weight: bold; }
            .status-inactive { color: #e74c3c; font-weight: bold; }
            .rating { color: #f39c12; }
            .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
            .search-box input { flex: 1; padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px; }
            .alert { padding: 15px; border-radius: 5px; margin-bottom: 20px; display: none; }
            .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👥 Управление Мастерами</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            
            <div class="content">
                <div id="alert" class="alert"></div>
                
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Поиск по имени или специализации..." oninput="filterMasters()">
                    <button class="btn" onclick="openAddModal()">➕ Добавить мастера</button>
                </div>
                
                <div class="table-container">
                    <table id="mastersTable">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Имя</th>
                                <th>Телефон</th>
                                <th>Специализация</th>
                                <th>Рейтинг</th>
                                <th>Статус</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody id="mastersList">
                            <tr><td colspan="7" style="text-align:center">Загрузка...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Add/Edit Modal -->
        <div id="masterModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modalTitle">Добавить мастера</h2>
                    <span class="close" onclick="closeModal()">&times;</span>
                </div>
                <form id="masterForm" onsubmit="saveMaster(event)">
                    <input type="hidden" id="masterId">
                    <div class="form-group">
                        <label for="name">Имя *</label>
                        <input type="text" id="name" required>
                    </div>
                    <div class="form-group">
                        <label for="phone">Телефон *</label>
                        <input type="tel" id="phone" required placeholder="+7 (999) 123-45-67">
                    </div>
                    <div class="form-group">
                        <label for="specialization">Специализация *</label>
                        <select id="specialization" required>
                            <option value="">Выберите...</option>
                            <option value="Татуировка">Татуировка</option>
                            <option value="Перманентный макияж">Перманентный макияж</option>
                            <option value="Пирсинг">Пирсинг</option>
                            <option value="Удаление тату">Удаление тату</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="telegram_id">Telegram ID</label>
                        <input type="text" id="telegram_id" placeholder="123456789">
                    </div>
                    <div class="form-group">
                        <label for="experience">Опыт (лет)</label>
                        <input type="number" id="experience" min="0" max="50">
                    </div>
                    <div class="form-group">
                        <label for="instagram">Instagram</label>
                        <input type="text" id="instagram" placeholder="@username">
                    </div>
                    <div class="form-group">
                        <label for="bio">Описание</label>
                        <textarea id="bio" rows="3" placeholder="Краткое описание мастера..."></textarea>
                    </div>
                    <div class="form-group">
                        <label for="calendar_id">Google Calendar ID</label>
                        <input type="text" id="calendar_id" placeholder="xxx@group.calendar.google.com">
                        <small style="color:#666;font-size:11px">ID календаря мастера для синхронизации записей</small>
                    </div>
                    <div class="form-group">
                        <label for="status">Статус</label>
                        <select id="status">
                            <option value="active">Активен</option>
                            <option value="inactive">Неактивен</option>
                        </select>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn btn-cancel" onclick="closeModal()">Отмена</button>
                        <button type="submit" class="btn btn-save">Сохранить</button>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            let allMasters = [];
            
            async function loadMasters() {
                try {
                    const response = await fetch('/api/masters');
                    allMasters = await response.json();
                    renderMasters(allMasters);
                } catch (error) {
                    console.error('Error loading masters:', error);
                    showAlert('Ошибка загрузки данных', 'error');
                }
            }
            
            function renderMasters(masters) {
                const tbody = document.getElementById('mastersList');
                if (!masters || masters.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center">Нет мастеров</td></tr>';
                    return;
                }
                tbody.innerHTML = masters.map(m => {
                    const statusClass = m.status === 'active' ? 'status-active' : 'status-inactive';
                    const statusText = m.status === 'active' ? 'Активен' : 'Неактивен';
                    const rating = m.rating ? `⭐ ${m.rating}` : '-';
                    return `<tr>
                        <td>${m.id ? m.id.substring(0, 8) + '...' : '-'}</td>
                        <td><strong>${m.name || '-'}</strong></td>
                        <td>${m.phone || '-'}</td>
                        <td>${m.specialization || '-'}</td>
                        <td class="rating">${rating}</td>
                        <td class="${statusClass}">${statusText}</td>
                        <td>
                            <button class="btn-edit" onclick="editMaster('${m.id}')">✏️ Редактировать</button>
                            <button class="btn-delete" onclick="deleteMaster('${m.id}', '${m.name}')">🗑️ Удалить</button>
                        </td>
                    </tr>`;
                }).join('');
            }
            
            function filterMasters() {
                const search = document.getElementById('searchInput').value.toLowerCase();
                const filtered = allMasters.filter(m => 
                    (m.name && m.name.toLowerCase().includes(search)) ||
                    (m.specialization && m.specialization.toLowerCase().includes(search)) ||
                    (m.phone && m.phone.includes(search))
                );
                renderMasters(filtered);
            }
            
            function openAddModal() {
                document.getElementById('modalTitle').textContent = 'Добавить мастера';
                document.getElementById('masterForm').reset();
                document.getElementById('masterId').value = '';
                document.getElementById('masterModal').style.display = 'block';
            }
            
            function editMaster(id) {
                const master = allMasters.find(m => m.id === id);
                if (!master) return;
                
                document.getElementById('modalTitle').textContent = 'Редактировать мастера';
                document.getElementById('masterId').value = master.id;
                document.getElementById('name').value = master.name || '';
                document.getElementById('phone').value = master.phone || '';
                document.getElementById('specialization').value = master.specialization || '';
                document.getElementById('telegram_id').value = master.telegram_id || '';
                document.getElementById('experience').value = master.experience || '';
                document.getElementById('instagram').value = master.instagram || '';
                document.getElementById('bio').value = master.bio || '';
                document.getElementById('calendar_id').value = master.calendar_id || '';
                document.getElementById('status').value = master.status || 'active';
                document.getElementById('masterModal').style.display = 'block';
            }
            
            function closeModal() {
                document.getElementById('masterModal').style.display = 'none';
            }
            
            async function saveMaster(event) {
                event.preventDefault();
                
                const id = document.getElementById('masterId').value;
                const data = {
                    name: document.getElementById('name').value,
                    phone: document.getElementById('phone').value,
                    specialization: document.getElementById('specialization').value,
                    telegram_id: document.getElementById('telegram_id').value,
                    experience: document.getElementById('experience').value,
                    instagram: document.getElementById('instagram').value,
                    bio: document.getElementById('bio').value,
                    calendar_id: document.getElementById('calendar_id').value,
                    status: document.getElementById('status').value
                };
                
                try {
                    const url = id ? `/api/masters/${id}` : '/api/masters';
                    const method = id ? 'PUT' : 'POST';
                    
                    const response = await fetch(url, {
                        method: method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert(result.message || 'Сохранено успешно!', 'success');
                        closeModal();
                        loadMasters();
                    } else {
                        showAlert(result.detail || result.message || 'Ошибка сохранения', 'error');
                    }
                } catch (error) {
                    console.error('Save error:', error);
                    showAlert('Ошибка сохранения', 'error');
                }
            }
            
            async function deleteMaster(id, name) {
                if (!confirm(`Удалить мастера "${name}"?`)) return;
                
                try {
                    const response = await fetch(`/api/masters/${id}`, { method: 'DELETE' });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert(result.message || 'Мастер удален!', 'success');
                        loadMasters();
                    } else {
                        showAlert(result.detail || 'Ошибка удаления', 'error');
                    }
                } catch (error) {
                    console.error('Delete error:', error);
                    showAlert('Ошибка удаления', 'error');
                }
            }
            
            function showAlert(message, type) {
                const alert = document.getElementById('alert');
                alert.textContent = message;
                alert.className = `alert alert-${type}`;
                alert.style.display = 'block';
                setTimeout(() => { alert.style.display = 'none'; }, 5000);
            }
            
            // Close modal on outside click
            window.onclick = function(event) {
                const modal = document.getElementById('masterModal');
                if (event.target === modal) {
                    closeModal();
                }
            }
            
            // Load data on page load
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
                     color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .btn-back:hover { background: rgba(255,255,255,0.3); }
            .content { padding: 30px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; border: none; padding: 10px 20px; border-radius: 5px;
                  cursor: pointer; margin-bottom: 20px; transition: all 0.3s; }
            .btn:hover { transform: scale(1.05); }
            .btn-edit { background: #3498db; color: white; border: none; padding: 8px 12px;
                       border-radius: 4px; cursor: pointer; margin-right: 5px; }
            .btn-delete { background: #e74c3c; color: white; border: none; padding: 8px 12px;
                         border-radius: 4px; cursor: pointer; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; font-weight: bold; }
            tr:hover { background: #f9f9f9; }
            
            .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0;
                    width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
            .modal-content { background-color: white; margin: 5% auto; padding: 30px;
                            border-radius: 10px; width: 90%; max-width: 500px; }
            .modal-header { display: flex; justify-content: space-between; align-items: center;
                           margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
            .close { color: #aaa; font-size: 28px; font-weight: bold; cursor: pointer; }
            .close:hover { color: #333; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; color: #333; font-weight: 500; }
            .form-group input, .form-group select, .form-group textarea {
                width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px; }
            .form-group input:focus, .form-group select:focus { outline: none; border-color: #667eea; }
            .form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
            .btn-cancel { background: #95a5a6; }
            .btn-save { background: #27ae60; }
            .price-badge { background: #27ae60; color: white; padding: 5px 10px; border-radius: 20px;
                          font-weight: bold; }
            .duration-badge { background: #3498db; color: white; padding: 5px 10px; border-radius: 20px; }
            .status-active { color: #27ae60; }
            .status-inactive { color: #e74c3c; }
            .search-box { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
            .search-box input { flex: 1; padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px; min-width: 200px; }
            .currency-select { padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px; background: white; cursor: pointer; font-size: 14px; }
            .currency-select:hover { border-color: #667eea; }
            .alert { padding: 15px; border-radius: 5px; margin-bottom: 20px; display: none; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💼 Управление Услугами</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <div id="alert" class="alert"></div>
                
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Поиск услуги..." oninput="filterServices()">
                    <select id="currencySelect" class="currency-select" onchange="changeCurrency()">
                        <option value="ILS">₪ Шекель (ILS)</option>
                        <option value="RUB">₽ Рубль (RUB)</option>
                        <option value="USD">$ Доллар (USD)</option>
                        <option value="EUR">€ Евро (EUR)</option>
                    </select>
                    <button class="btn" onclick="openAddModal()">➕ Добавить услугу</button>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Название</th>
                            <th>Описание</th>
                            <th>Цена</th>
                            <th>Длительность</th>
                            <th>Категория</th>
                            <th>Статус</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody id="servicesList">
                        <tr><td colspan="8" style="text-align:center">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Modal -->
        <div id="serviceModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modalTitle">Добавить услугу</h2>
                    <span class="close" onclick="closeModal()">&times;</span>
                </div>
                <form id="serviceForm" onsubmit="saveService(event)">
                    <input type="hidden" id="serviceId">
                    <div class="form-group">
                        <label for="name">Название *</label>
                        <input type="text" id="name" required>
                    </div>
                    <div class="form-group">
                        <label for="description">Описание</label>
                        <textarea id="description" rows="3" placeholder="Описание услуги..."></textarea>
                    </div>
                    <div class="form-group">
                        <label for="price">Цена (от) *</label>
                        <input type="number" id="price" min="0" required placeholder="3000">
                    </div>
                    <div class="form-group">
                        <label for="price_to">Цена (до)</label>
                        <input type="number" id="price_to" min="0" placeholder="10000">
                    </div>
                    <div class="form-group">
                        <label for="duration">Длительность (мин) *</label>
                        <input type="number" id="duration" min="15" step="15" required placeholder="60">
                    </div>
                    <div class="form-group">
                        <label for="category">Категория</label>
                        <select id="category">
                            <option value="tattoo">Татуировка</option>
                            <option value="permanent">Перманентный макияж</option>
                            <option value="piercing">Пирсинг</option>
                            <option value="removal">Удаление тату</option>
                            <option value="consultation">Консультация</option>
                            <option value="other">Другое</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="active">Статус</label>
                        <select id="active">
                            <option value="TRUE">Активна</option>
                            <option value="FALSE">Неактивна</option>
                        </select>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn btn-cancel" onclick="closeModal()">Отмена</button>
                        <button type="submit" class="btn btn-save">Сохранить</button>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            let allServices = [];
            let currentCurrency = localStorage.getItem('currency') || 'ILS';
            const currencySymbols = {
                'ILS': '₪',
                'RUB': '₽',
                'USD': '$',
                'EUR': '€'
            };
            
            function changeCurrency() {
                currentCurrency = document.getElementById('currencySelect').value;
                localStorage.setItem('currency', currentCurrency);
                renderServices(allServices);
            }
            
            function formatPrice(priceFrom, priceTo) {
                const symbol = currencySymbols[currentCurrency] || '₪';
                if (priceFrom && priceTo && priceFrom !== priceTo) {
                    return `${priceFrom} - ${priceTo} ${symbol}`;
                }
                return `${priceFrom || 0} ${symbol}`;
            }
            
            async function loadServices() {
                try {
                    const response = await fetch('/api/services');
                    allServices = await response.json();
                    renderServices(allServices);
                } catch (error) {
                    console.error('Error loading services:', error);
                    showAlert('Ошибка загрузки', 'error');
                }
            }
            
            function renderServices(services) {
                // Установить выбранную валюту
                document.getElementById('currencySelect').value = currentCurrency;
                
                const tbody = document.getElementById('servicesList');
                if (!services || services.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center">Нет услуг</td></tr>';
                    return;
                }
                tbody.innerHTML = services.map(s => {
                    const price = formatPrice(s.price_from, s.price_to);
                    const statusClass = s.active === 'TRUE' || s.active === true ? 'status-active' : 'status-inactive';
                    const statusText = s.active === 'TRUE' || s.active === true ? '✅ Активна' : '❌ Неактивна';
                    const categoryMap = {
                        'tattoo': 'Татуировка', 'permanent': 'Перманент', 'piercing': 'Пирсинг',
                        'removal': 'Удаление', 'consultation': 'Консультация', 'other': 'Другое'
                    };
                    return `<tr>
                        <td>${s.id ? s.id.substring(0, 8) + '...' : '-'}</td>
                        <td><strong>${s.name || '-'}</strong></td>
                        <td>${(s.description || '-').substring(0, 50)}${s.description && s.description.length > 50 ? '...' : ''}</td>
                        <td><span class="price-badge">${price}</span></td>
                        <td><span class="duration-badge">${s.duration_min || 60} мин</span></td>
                        <td>${categoryMap[s.category] || s.category || '-'}</td>
                        <td class="${statusClass}">${statusText}</td>
                        <td>
                            <button class="btn-edit" onclick="editService('${s.id}')">✏️</button>
                            <button class="btn-delete" onclick="deleteService('${s.id}', '${s.name}')">🗑️</button>
                        </td>
                    </tr>`;
                }).join('');
            }
            
            function filterServices() {
                const search = document.getElementById('searchInput').value.toLowerCase();
                const filtered = allServices.filter(s => 
                    (s.name && s.name.toLowerCase().includes(search)) ||
                    (s.description && s.description.toLowerCase().includes(search)) ||
                    (s.category && s.category.toLowerCase().includes(search))
                );
                renderServices(filtered);
            }
            
            function openAddModal() {
                document.getElementById('modalTitle').textContent = 'Добавить услугу';
                document.getElementById('serviceForm').reset();
                document.getElementById('serviceId').value = '';
                document.getElementById('serviceModal').style.display = 'block';
            }
            
            function editService(id) {
                const service = allServices.find(s => s.id === id);
                if (!service) return;
                
                document.getElementById('modalTitle').textContent = 'Редактировать услугу';
                document.getElementById('serviceId').value = service.id;
                document.getElementById('name').value = service.name || '';
                document.getElementById('description').value = service.description || '';
                document.getElementById('price').value = service.price_from || '';
                document.getElementById('price_to').value = service.price_to || '';
                document.getElementById('duration').value = service.duration_min || '';
                document.getElementById('category').value = service.category || 'other';
                document.getElementById('active').value = service.active === 'TRUE' || service.active === true ? 'TRUE' : 'FALSE';
                document.getElementById('serviceModal').style.display = 'block';
            }
            
            function closeModal() {
                document.getElementById('serviceModal').style.display = 'none';
            }
            
            async function saveService(event) {
                event.preventDefault();
                
                const id = document.getElementById('serviceId').value;
                const data = {
                    name: document.getElementById('name').value,
                    description: document.getElementById('description').value,
                    price: document.getElementById('price').value,
                    price_from: document.getElementById('price').value,
                    price_to: document.getElementById('price_to').value || document.getElementById('price').value,
                    duration: document.getElementById('duration').value,
                    duration_min: document.getElementById('duration').value,
                    category: document.getElementById('category').value,
                    active: document.getElementById('active').value
                };
                
                try {
                    const url = id ? `/api/services/${id}` : '/api/services';
                    const method = id ? 'PUT' : 'POST';
                    
                    const response = await fetch(url, {
                        method: method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert(result.message || 'Сохранено!', 'success');
                        closeModal();
                        loadServices();
                    } else {
                        showAlert(result.detail || 'Ошибка', 'error');
                    }
                } catch (error) {
                    showAlert('Ошибка сохранения', 'error');
                }
            }
            
            async function deleteService(id, name) {
                if (!confirm(`Удалить услугу "${name}"?`)) return;
                
                try {
                    const response = await fetch(`/api/services/${id}`, { method: 'DELETE' });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert('Услуга удалена!', 'success');
                        loadServices();
                    } else {
                        showAlert(result.detail || 'Ошибка', 'error');
                    }
                } catch (error) {
                    showAlert('Ошибка удаления', 'error');
                }
            }
            
            function showAlert(message, type) {
                const alert = document.getElementById('alert');
                alert.textContent = message;
                alert.className = `alert alert-${type}`;
                alert.style.display = 'block';
                setTimeout(() => { alert.style.display = 'none'; }, 5000);
            }
            
            window.onclick = function(event) {
                if (event.target === document.getElementById('serviceModal')) closeModal();
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
            .container { max-width: 1400px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 30px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; border: none; padding: 10px 20px; border-radius: 5px;
                  cursor: pointer; margin-bottom: 20px; transition: all 0.3s; }
            .btn:hover { transform: scale(1.05); }
            .btn-view { background: #3498db; color: white; border: none; padding: 8px 12px;
                       border-radius: 4px; cursor: pointer; margin-right: 5px; }
            .btn-edit { background: #f39c12; color: white; border: none; padding: 8px 12px;
                       border-radius: 4px; cursor: pointer; margin-right: 5px; }
            .btn-delete { background: #e74c3c; color: white; border: none; padding: 8px 12px;
                         border-radius: 4px; cursor: pointer; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; font-weight: bold; }
            tr:hover { background: #f9f9f9; }
            
            .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0;
                    width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); overflow: auto; }
            .modal-content { background-color: white; margin: 3% auto; padding: 30px;
                            border-radius: 10px; width: 90%; max-width: 600px; }
            .modal-header { display: flex; justify-content: space-between; align-items: center;
                           margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
            .close { color: #aaa; font-size: 28px; cursor: pointer; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; color: #333; font-weight: 500; }
            .form-group input, .form-group textarea {
                width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px; }
            .form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
            .btn-cancel { background: #95a5a6; }
            .btn-save { background: #27ae60; }
            .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
            .search-box input { flex: 1; padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px; }
            .alert { padding: 15px; border-radius: 5px; margin-bottom: 20px; display: none; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
            
            .client-details { margin-top: 20px; }
            .detail-card { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 15px; }
            .detail-row { display: flex; margin-bottom: 10px; }
            .detail-label { font-weight: bold; width: 150px; color: #666; }
            .detail-value { flex: 1; }
            .bookings-list { margin-top: 20px; }
            .booking-item { background: #fff; border: 1px solid #e0e0e0; padding: 15px;
                           border-radius: 8px; margin-bottom: 10px; }
            .booking-status { display: inline-block; padding: 3px 10px; border-radius: 15px;
                             font-size: 12px; font-weight: bold; }
            .status-pending { background: #fff3cd; color: #856404; }
            .status-confirmed { background: #cce5ff; color: #004085; }
            .status-completed { background: #d4edda; color: #155724; }
            .status-cancelled { background: #f8d7da; color: #721c24; }
            .stats-row { display: flex; gap: 20px; margin-top: 20px; }
            .stat-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       color: white; padding: 15px 25px; border-radius: 8px; text-align: center; }
            .stat-value { font-size: 24px; font-weight: bold; }
            .stat-label { font-size: 12px; opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👤 Управление Клиентами</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <div id="alert" class="alert"></div>
                
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Поиск по имени, телефону или email..." oninput="filterClients()">
                    <button class="btn" onclick="openAddModal()">➕ Добавить клиента</button>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Имя</th>
                            <th>Телефон</th>
                            <th>Email</th>
                            <th>Telegram</th>
                            <th>Дата регистрации</th>
                            <th>Последний визит</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody id="clientsList">
                        <tr><td colspan="8" style="text-align:center">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Add/Edit Modal -->
        <div id="clientModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modalTitle">Добавить клиента</h2>
                    <span class="close" onclick="closeModal()">&times;</span>
                </div>
                <form id="clientForm" onsubmit="saveClient(event)">
                    <input type="hidden" id="clientId">
                    <div class="form-group">
                        <label for="name">Имя *</label>
                        <input type="text" id="name" required>
                    </div>
                    <div class="form-group">
                        <label for="phone">Телефон *</label>
                        <input type="tel" id="phone" required placeholder="+7 (999) 123-45-67">
                    </div>
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" id="email" placeholder="email@example.com">
                    </div>
                    <div class="form-group">
                        <label for="telegram_id">Telegram ID</label>
                        <input type="text" id="telegram_id" placeholder="123456789">
                    </div>
                    <div class="form-group">
                        <label for="notes">Заметки</label>
                        <textarea id="notes" rows="3" placeholder="Дополнительная информация о клиенте..."></textarea>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn btn-cancel" onclick="closeModal()">Отмена</button>
                        <button type="submit" class="btn btn-save">Сохранить</button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- View Client Modal -->
        <div id="viewClientModal" class="modal">
            <div class="modal-content" style="max-width: 700px;">
                <div class="modal-header">
                    <h2>Информация о клиенте</h2>
                    <span class="close" onclick="closeViewModal()">&times;</span>
                </div>
                <div id="clientDetails" class="client-details">
                    <p>Загрузка...</p>
                </div>
            </div>
        </div>
        
        <script>
            let allClients = [];
            
            async function loadClients() {
                try {
                    const response = await fetch('/api/clients');
                    allClients = await response.json();
                    renderClients(allClients);
                } catch (error) {
                    console.error('Error loading clients:', error);
                    showAlert('Ошибка загрузки', 'error');
                }
            }
            
            function renderClients(clients) {
                const tbody = document.getElementById('clientsList');
                if (!clients || clients.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center">Нет клиентов</td></tr>';
                    return;
                }
                tbody.innerHTML = clients.map(c => {
                    const createdAt = c.created_at ? new Date(c.created_at).toLocaleDateString('ru-RU') : '-';
                    const lastVisit = c.last_visit ? new Date(c.last_visit).toLocaleDateString('ru-RU') : '-';
                    const isDeleted = c.notes && c.notes.includes('[DELETED]');
                    if (isDeleted) return '';
                    return `<tr>
                        <td>${c.id ? c.id.substring(0, 8) + '...' : '-'}</td>
                        <td><strong>${c.name || '-'}</strong></td>
                        <td>${c.phone || '-'}</td>
                        <td>${c.email || '-'}</td>
                        <td>${c.telegram_id || '-'}</td>
                        <td>${createdAt}</td>
                        <td>${lastVisit}</td>
                        <td>
                            <button class="btn-view" onclick="viewClient('${c.id}')">👁️ Подробнее</button>
                            <button class="btn-edit" onclick="editClient('${c.id}')">✏️</button>
                            <button class="btn-delete" onclick="deleteClient('${c.id}', '${c.name}')">🗑️</button>
                        </td>
                    </tr>`;
                }).filter(row => row).join('');
            }
            
            function filterClients() {
                const search = document.getElementById('searchInput').value.toLowerCase();
                const filtered = allClients.filter(c => 
                    (c.name && c.name.toLowerCase().includes(search)) ||
                    (c.phone && c.phone.includes(search)) ||
                    (c.email && c.email.toLowerCase().includes(search)) ||
                    (c.telegram_id && c.telegram_id.includes(search))
                );
                renderClients(filtered);
            }
            
            function openAddModal() {
                document.getElementById('modalTitle').textContent = 'Добавить клиента';
                document.getElementById('clientForm').reset();
                document.getElementById('clientId').value = '';
                document.getElementById('clientModal').style.display = 'block';
            }
            
            function editClient(id) {
                const client = allClients.find(c => c.id === id);
                if (!client) return;
                
                document.getElementById('modalTitle').textContent = 'Редактировать клиента';
                document.getElementById('clientId').value = client.id;
                document.getElementById('name').value = client.name || '';
                document.getElementById('phone').value = client.phone || '';
                document.getElementById('email').value = client.email || '';
                document.getElementById('telegram_id').value = client.telegram_id || '';
                document.getElementById('notes').value = client.notes || '';
                document.getElementById('clientModal').style.display = 'block';
            }
            
            async function viewClient(id) {
                try {
                    const response = await fetch(`/api/clients/${id}`);
                    const client = await response.json();
                    
                    const createdAt = client.created_at ? new Date(client.created_at).toLocaleDateString('ru-RU') : '-';
                    const lastVisit = client.last_visit ? new Date(client.last_visit).toLocaleDateString('ru-RU') : '-';
                    
                    let bookingsHtml = '';
                    if (client.bookings && client.bookings.length > 0) {
                        bookingsHtml = `<div class="bookings-list">
                            <h3>📅 История записей (${client.bookings.length})</h3>
                            ${client.bookings.slice(0, 5).map(b => {
                                const statusClass = 'status-' + (b.status || 'pending');
                                const statusMap = {pending: 'Ожидает', confirmed: 'Подтверждена', completed: 'Завершена', cancelled: 'Отменена'};
                                return `<div class="booking-item">
                                    <div><strong>📆 ${b.date || '-'} в ${b.time || '-'}</strong></div>
                                    <div>Услуга: ${b.service_id || '-'} | Мастер: ${b.master_id || '-'}</div>
                                    <div>Цена: ${b.price || 0} ₽ <span class="booking-status ${statusClass}">${statusMap[b.status] || b.status}</span></div>
                                </div>`;
                            }).join('')}
                            ${client.bookings.length > 5 ? `<p>... и ещё ${client.bookings.length - 5} записей</p>` : ''}
                        </div>`;
                    } else {
                        bookingsHtml = '<p>Записей пока нет</p>';
                    }
                    
                    document.getElementById('clientDetails').innerHTML = `
                        <div class="detail-card">
                            <div class="detail-row"><span class="detail-label">👤 Имя:</span><span class="detail-value">${client.name || '-'}</span></div>
                            <div class="detail-row"><span class="detail-label">📞 Телефон:</span><span class="detail-value">${client.phone || '-'}</span></div>
                            <div class="detail-row"><span class="detail-label">📧 Email:</span><span class="detail-value">${client.email || '-'}</span></div>
                            <div class="detail-row"><span class="detail-label">💬 Telegram:</span><span class="detail-value">${client.telegram_id || '-'}</span></div>
                            <div class="detail-row"><span class="detail-label">📝 Заметки:</span><span class="detail-value">${client.notes || '-'}</span></div>
                            <div class="detail-row"><span class="detail-label">📅 Регистрация:</span><span class="detail-value">${createdAt}</span></div>
                            <div class="detail-row"><span class="detail-label">🕐 Последний визит:</span><span class="detail-value">${lastVisit}</span></div>
                        </div>
                        <div class="stats-row">
                            <div class="stat-box"><div class="stat-value">${client.total_bookings || 0}</div><div class="stat-label">Всего записей</div></div>
                            <div class="stat-box"><div class="stat-value">${client.total_spent || 0} ₽</div><div class="stat-label">Потрачено</div></div>
                        </div>
                        ${bookingsHtml}
                    `;
                    
                    document.getElementById('viewClientModal').style.display = 'block';
                } catch (error) {
                    console.error('Error viewing client:', error);
                    showAlert('Ошибка загрузки данных клиента', 'error');
                }
            }
            
            function closeModal() {
                document.getElementById('clientModal').style.display = 'none';
            }
            
            function closeViewModal() {
                document.getElementById('viewClientModal').style.display = 'none';
            }
            
            async function saveClient(event) {
                event.preventDefault();
                
                const id = document.getElementById('clientId').value;
                const data = {
                    name: document.getElementById('name').value,
                    phone: document.getElementById('phone').value,
                    email: document.getElementById('email').value,
                    telegram_id: document.getElementById('telegram_id').value,
                    notes: document.getElementById('notes').value
                };
                
                try {
                    const url = id ? `/api/clients/${id}` : '/api/clients';
                    const method = id ? 'PUT' : 'POST';
                    
                    const response = await fetch(url, {
                        method: method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert(result.message || 'Сохранено!', 'success');
                        closeModal();
                        loadClients();
                    } else {
                        showAlert(result.detail || 'Ошибка', 'error');
                    }
                } catch (error) {
                    showAlert('Ошибка сохранения', 'error');
                }
            }
            
            async function deleteClient(id, name) {
                if (!confirm(`Удалить клиента "${name}"?\\n\\nВнимание: история записей будет сохранена!`)) return;
                
                try {
                    const response = await fetch(`/api/clients/${id}`, { method: 'DELETE' });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert('Клиент удален!', 'success');
                        loadClients();
                    } else {
                        showAlert(result.detail || 'Ошибка', 'error');
                    }
                } catch (error) {
                    showAlert('Ошибка удаления', 'error');
                }
            }
            
            function showAlert(message, type) {
                const alert = document.getElementById('alert');
                alert.textContent = message;
                alert.className = `alert alert-${type}`;
                alert.style.display = 'block';
                setTimeout(() => { alert.style.display = 'none'; }, 5000);
            }
            
            window.onclick = function(event) {
                if (event.target === document.getElementById('clientModal')) closeModal();
                if (event.target === document.getElementById('viewClientModal')) closeViewModal();
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
            .container { max-width: 1400px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 30px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; border: none; padding: 10px 20px; border-radius: 5px;
                  cursor: pointer; transition: all 0.3s; }
            .btn:hover { transform: scale(1.05); }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; font-weight: bold; }
            tr:hover { background: #f9f9f9; }
            
            .filters { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }
            .filters select, .filters input { padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px; }
            .filters select:focus, .filters input:focus { outline: none; border-color: #667eea; }
            
            .status-badge { display: inline-block; padding: 5px 12px; border-radius: 20px;
                           font-size: 12px; font-weight: bold; }
            .status-pending { background: #fff3cd; color: #856404; }
            .status-confirmed { background: #cce5ff; color: #004085; }
            .status-completed { background: #d4edda; color: #155724; }
            .status-cancelled { background: #f8d7da; color: #721c24; }
            
            .action-btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer;
                         margin-right: 5px; font-size: 12px; }
            .btn-confirm { background: #28a745; color: white; }
            .btn-complete { background: #17a2b8; color: white; }
            .btn-cancel { background: #dc3545; color: white; }
            .btn-view { background: #6c757d; color: white; }
            
            .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0;
                    width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); overflow: auto; }
            .modal-content { background-color: white; margin: 3% auto; padding: 30px;
                            border-radius: 10px; width: 90%; max-width: 600px; }
            .modal-header { display: flex; justify-content: space-between; align-items: center;
                           margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
            .close { color: #aaa; font-size: 28px; cursor: pointer; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; color: #333; font-weight: 500; }
            .form-group input, .form-group select, .form-group textarea {
                width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px; }
            .form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
            .btn-save { background: #27ae60; }
            .btn-cancel-modal { background: #95a5a6; }
            
            .alert { padding: 15px; border-radius: 5px; margin-bottom: 20px; display: none; }
            .alert-success { background: #d4edda; color: #155724; }
            .alert-error { background: #f8d7da; color: #721c24; }
            
            .stats-row { display: flex; gap: 15px; margin-bottom: 20px; }
            .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white; padding: 15px 20px; border-radius: 8px; text-align: center; flex: 1; }
            .stat-card .value { font-size: 24px; font-weight: bold; }
            .stat-card .label { font-size: 12px; opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📅 Управление Записями</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <div id="alert" class="alert"></div>
                
                <div class="stats-row" id="statsRow">
                    <div class="stat-card"><div class="value" id="totalBookings">0</div><div class="label">Всего записей</div></div>
                    <div class="stat-card"><div class="value" id="pendingBookings">0</div><div class="label">Ожидают</div></div>
                    <div class="stat-card"><div class="value" id="confirmedBookings">0</div><div class="label">Подтверждены</div></div>
                    <div class="stat-card"><div class="value" id="completedBookings">0</div><div class="label">Выполнены</div></div>
                </div>
                
                <div class="filters">
                    <select id="statusFilter" onchange="filterBookings()">
                        <option value="">Все статусы</option>
                        <option value="pending">Ожидает</option>
                        <option value="confirmed">Подтверждена</option>
                        <option value="completed">Завершена</option>
                        <option value="cancelled">Отменена</option>
                    </select>
                    <select id="masterFilter" onchange="filterBookings()">
                        <option value="">Все мастера</option>
                    </select>
                    <input type="date" id="dateFrom" onchange="filterBookings()" placeholder="Дата от">
                    <input type="date" id="dateTo" onchange="filterBookings()" placeholder="Дата до">
                    <button class="btn" onclick="openAddModal()">➕ Новая запись</button>
                    <button class="btn" style="background: #17a2b8;" onclick="loadBookings()">🔄 Обновить</button>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Клиент</th>
                            <th>Мастер</th>
                            <th>Услуга</th>
                            <th>Дата</th>
                            <th>Время</th>
                            <th>Цена</th>
                            <th>Статус</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody id="bookingsList">
                        <tr><td colspan="9" style="text-align:center">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Add/Edit Booking Modal -->
        <div id="bookingModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modalTitle">Новая запись</h2>
                    <span class="close" onclick="closeModal()">&times;</span>
                </div>
                <form id="bookingForm" onsubmit="saveBooking(event)">
                    <input type="hidden" id="bookingId">
                    <div class="form-group">
                        <label for="client_id">Клиент *</label>
                        <select id="client_id" required></select>
                    </div>
                    <div class="form-group">
                        <label for="master_id">Мастер *</label>
                        <select id="master_id" required></select>
                    </div>
                    <div class="form-group">
                        <label for="service_id">Услуга *</label>
                        <select id="service_id" required></select>
                    </div>
                    <div class="form-group">
                        <label for="date">Дата *</label>
                        <input type="date" id="date" required>
                    </div>
                    <div class="form-group">
                        <label for="time">Время *</label>
                        <input type="time" id="time" required>
                    </div>
                    <div class="form-group">
                        <label for="notes">Заметки</label>
                        <textarea id="notes" rows="3" placeholder="Дополнительная информация..."></textarea>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn btn-cancel-modal" onclick="closeModal()">Отмена</button>
                        <button type="submit" class="btn btn-save">Сохранить</button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- Cancel Reason Modal -->
        <div id="cancelModal" class="modal">
            <div class="modal-content" style="max-width: 400px;">
                <div class="modal-header">
                    <h2>Отмена записи</h2>
                    <span class="close" onclick="closeCancelModal()">&times;</span>
                </div>
                <div class="form-group">
                    <label for="cancelReason">Причина отмены</label>
                    <textarea id="cancelReason" rows="3" placeholder="Укажите причину отмены..."></textarea>
                </div>
                <input type="hidden" id="cancelBookingId">
                <div class="form-actions">
                    <button class="btn btn-cancel-modal" onclick="closeCancelModal()">Назад</button>
                    <button class="btn btn-cancel" onclick="confirmCancel()">Отменить запись</button>
                </div>
            </div>
        </div>
        
        <script>
            let allBookings = [];
            let clients = [];
            let masters = [];
            let services = [];
            
            async function loadData() {
                try {
                    const [clientsRes, mastersRes, servicesRes] = await Promise.all([
                        fetch('/api/clients'),
                        fetch('/api/masters'),
                        fetch('/api/services')
                    ]);
                    clients = await clientsRes.json();
                    masters = await mastersRes.json();
                    services = await servicesRes.json();
                    
                    // Populate filters and form selects
                    const masterFilter = document.getElementById('masterFilter');
                    masterFilter.innerHTML = '<option value="">Все мастера</option>' + 
                        masters.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
                    
                    document.getElementById('client_id').innerHTML = 
                        '<option value="">Выберите клиента...</option>' +
                        clients.filter(c => !c.notes || !c.notes.includes('[DELETED]'))
                            .map(c => `<option value="${c.id}">${c.name} (${c.phone || 'без телефона'})</option>`).join('');
                    
                    document.getElementById('master_id').innerHTML = 
                        '<option value="">Выберите мастера...</option>' +
                        masters.filter(m => m.status === 'active')
                            .map(m => `<option value="${m.id}">${m.name}</option>`).join('');
                    
                    document.getElementById('service_id').innerHTML = 
                        '<option value="">Выберите услугу...</option>' +
                        services.filter(s => s.active === 'TRUE' || s.active === true)
                            .map(s => `<option value="${s.id}">${s.name} (${s.price_from || 0} ₽)</option>`).join('');
                    
                    await loadBookings();
                } catch (error) {
                    console.error('Error loading data:', error);
                    showAlert('Ошибка загрузки данных', 'error');
                }
            }
            
            async function loadBookings() {
                try {
                    const response = await fetch('/api/bookings');
                    allBookings = await response.json();
                    updateStats();
                    filterBookings();
                } catch (error) {
                    console.error('Error loading bookings:', error);
                    document.getElementById('bookingsList').innerHTML = '<tr><td colspan="9">Ошибка загрузки</td></tr>';
                }
            }
            
            function updateStats() {
                document.getElementById('totalBookings').textContent = allBookings.length;
                document.getElementById('pendingBookings').textContent = allBookings.filter(b => b.status === 'pending').length;
                document.getElementById('confirmedBookings').textContent = allBookings.filter(b => b.status === 'confirmed').length;
                document.getElementById('completedBookings').textContent = allBookings.filter(b => b.status === 'completed').length;
            }
            
            function filterBookings() {
                const status = document.getElementById('statusFilter').value;
                const masterId = document.getElementById('masterFilter').value;
                const dateFrom = document.getElementById('dateFrom').value;
                const dateTo = document.getElementById('dateTo').value;
                
                let filtered = [...allBookings];
                
                if (status) filtered = filtered.filter(b => b.status === status);
                if (masterId) filtered = filtered.filter(b => b.master_id === masterId);
                if (dateFrom) filtered = filtered.filter(b => b.date >= dateFrom);
                if (dateTo) filtered = filtered.filter(b => b.date <= dateTo);
                
                renderBookings(filtered);
            }
            
            function renderBookings(bookings) {
                const tbody = document.getElementById('bookingsList');
                if (!bookings || bookings.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center">Нет записей</td></tr>';
                    return;
                }
                
                const statusMap = {pending: 'Ожидает', confirmed: 'Подтверждена', completed: 'Завершена', cancelled: 'Отменена'};
                
                tbody.innerHTML = bookings.map(b => {
                    const client = clients.find(c => c.id === b.client_id);
                    const master = masters.find(m => m.id === b.master_id);
                    const service = services.find(s => s.id === b.service_id);
                    
                    const statusClass = 'status-' + (b.status || 'pending');
                    const statusText = statusMap[b.status] || b.status || 'Неизвестен';
                    
                    let actions = '';
                    if (b.status === 'pending') {
                        actions = `<button class="action-btn btn-confirm" onclick="confirmBooking('${b.id}')">✅ Подтвердить</button>
                                   <button class="action-btn btn-cancel" onclick="openCancelModal('${b.id}')">❌ Отменить</button>`;
                    } else if (b.status === 'confirmed') {
                        actions = `<button class="action-btn btn-complete" onclick="completeBooking('${b.id}')">✓ Выполнено</button>
                                   <button class="action-btn btn-cancel" onclick="openCancelModal('${b.id}')">❌ Отменить</button>`;
                    }
                    
                    return `<tr>
                        <td>${b.id ? b.id.substring(0, 8) + '...' : '-'}</td>
                        <td>${client ? client.name : b.client_id || '-'}</td>
                        <td>${master ? master.name : b.master_id || '-'}</td>
                        <td>${service ? service.name : b.service_id || '-'}</td>
                        <td>${b.date || '-'}</td>
                        <td>${b.time || '-'}</td>
                        <td>${b.price || 0} ₽</td>
                        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                        <td>${actions}</td>
                    </tr>`;
                }).join('');
            }
            
            function openAddModal() {
                document.getElementById('modalTitle').textContent = 'Новая запись';
                document.getElementById('bookingForm').reset();
                document.getElementById('bookingId').value = '';
                // Set default date to today
                document.getElementById('date').valueAsDate = new Date();
                document.getElementById('bookingModal').style.display = 'block';
            }
            
            function closeModal() {
                document.getElementById('bookingModal').style.display = 'none';
            }
            
            function openCancelModal(id) {
                document.getElementById('cancelBookingId').value = id;
                document.getElementById('cancelReason').value = '';
                document.getElementById('cancelModal').style.display = 'block';
            }
            
            function closeCancelModal() {
                document.getElementById('cancelModal').style.display = 'none';
            }
            
            async function saveBooking(event) {
                event.preventDefault();
                
                const data = {
                    client_id: document.getElementById('client_id').value,
                    master_id: document.getElementById('master_id').value,
                    service_id: document.getElementById('service_id').value,
                    date: document.getElementById('date').value,
                    time: document.getElementById('time').value,
                    notes: document.getElementById('notes').value
                };
                
                try {
                    const response = await fetch('/api/bookings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert(result.message || 'Запись создана!', 'success');
                        closeModal();
                        loadBookings();
                    } else {
                        showAlert(result.detail || 'Ошибка создания', 'error');
                    }
                } catch (error) {
                    showAlert('Ошибка сохранения', 'error');
                }
            }
            
            async function confirmBooking(id) {
                try {
                    const response = await fetch(`/api/bookings/${id}/confirm`, { method: 'POST' });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert('Запись подтверждена!', 'success');
                        loadBookings();
                    } else {
                        showAlert(result.detail || 'Ошибка', 'error');
                    }
                } catch (error) {
                    showAlert('Ошибка подтверждения', 'error');
                }
            }
            
            async function completeBooking(id) {
                try {
                    const response = await fetch(`/api/bookings/${id}/complete`, { method: 'POST' });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert('Запись выполнена!', 'success');
                        loadBookings();
                    } else {
                        showAlert(result.detail || 'Ошибка', 'error');
                    }
                } catch (error) {
                    showAlert('Ошибка', 'error');
                }
            }
            
            async function confirmCancel() {
                const id = document.getElementById('cancelBookingId').value;
                const reason = document.getElementById('cancelReason').value;
                
                try {
                    const response = await fetch(`/api/bookings/${id}`, {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ reason })
                    });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert('Запись отменена!', 'success');
                        closeCancelModal();
                        loadBookings();
                    } else {
                        showAlert(result.detail || 'Ошибка', 'error');
                    }
                } catch (error) {
                    showAlert('Ошибка отмены', 'error');
                }
            }
            
            function showAlert(message, type) {
                const alert = document.getElementById('alert');
                alert.textContent = message;
                alert.className = `alert alert-${type}`;
                alert.style.display = 'block';
                setTimeout(() => { alert.style.display = 'none'; }, 5000);
            }
            
            window.onclick = function(event) {
                if (event.target === document.getElementById('bookingModal')) closeModal();
                if (event.target === document.getElementById('cancelModal')) closeCancelModal();
            }
            
            loadData();
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
            .container { max-width: 1400px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 30px; }
            
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                         gap: 20px; margin-bottom: 30px; }
            .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white; padding: 25px; border-radius: 10px; text-align: center; }
            .stat-card.green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
            .stat-card.orange { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            .stat-card.blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
            .stat-value { font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }
            .stat-label { font-size: 0.9em; opacity: 0.9; }
            
            .charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                          gap: 20px; margin-top: 30px; }
            .chart-card { background: #f8f9fa; padding: 25px; border-radius: 10px;
                         border: 1px solid #e0e0e0; }
            .chart-card h3 { margin-bottom: 20px; color: #333; }
            
            .bar-chart { display: flex; flex-direction: column; gap: 10px; }
            .bar-item { display: flex; align-items: center; gap: 15px; }
            .bar-label { width: 120px; font-size: 14px; color: #666; }
            .bar-container { flex: 1; background: #e0e0e0; border-radius: 10px; height: 25px; overflow: hidden; }
            .bar { height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  border-radius: 10px; display: flex; align-items: center; justify-content: flex-end;
                  padding-right: 10px; color: white; font-size: 12px; font-weight: bold;
                  min-width: 30px; transition: width 0.5s ease; }
            
            .pie-chart { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; }
            .pie-item { display: flex; align-items: center; gap: 10px; }
            .pie-color { width: 20px; height: 20px; border-radius: 4px; }
            .pie-text { font-size: 14px; color: #333; }
            
            .table-container { margin-top: 30px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
            th { background: #f5f5f5; font-weight: bold; }
            
            .refresh-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; border: none; padding: 10px 20px; border-radius: 5px;
                          cursor: pointer; margin-bottom: 20px; }
            .refresh-btn:hover { transform: scale(1.05); }
            
            .loading { text-align: center; padding: 40px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📈 Аналитика</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <button class="refresh-btn" onclick="loadAnalytics()">🔄 Обновить данные</button>
                
                <div id="loading" class="loading">Загрузка данных...</div>
                
                <div id="analyticsContent" style="display: none;">
                    <!-- Stats Grid -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" id="totalClients">0</div>
                            <div class="stat-label">👤 Всего клиентов</div>
                        </div>
                        <div class="stat-card green">
                            <div class="stat-value" id="totalBookings">0</div>
                            <div class="stat-label">📅 Всего записей</div>
                        </div>
                        <div class="stat-card orange">
                            <div class="stat-value" id="totalRevenue">0 ₽</div>
                            <div class="stat-label">💰 Общий доход</div>
                        </div>
                        <div class="stat-card blue">
                            <div class="stat-value" id="conversionRate">0%</div>
                            <div class="stat-label">📊 Конверсия</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="newClientsMonth">0</div>
                            <div class="stat-label">🆕 Новых за месяц</div>
                        </div>
                    </div>
                    
                    <!-- Charts -->
                    <div class="charts-grid">
                        <div class="chart-card">
                            <h3>📊 Статусы записей</h3>
                            <div class="pie-chart" id="statusChart"></div>
                        </div>
                        
                        <div class="chart-card">
                            <h3>👨‍🎨 Топ мастеров по записям</h3>
                            <div class="bar-chart" id="masterChart"></div>
                        </div>
                        
                        <div class="chart-card">
                            <h3>💰 Доход по месяцам</h3>
                            <div class="bar-chart" id="revenueChart"></div>
                        </div>
                    </div>
                    
                    <!-- Recent Activity -->
                    <div class="table-container">
                        <h3 style="margin-bottom: 15px;">📋 Последние записи</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Дата</th>
                                    <th>Клиент</th>
                                    <th>Мастер</th>
                                    <th>Услуга</th>
                                    <th>Сумма</th>
                                    <th>Статус</th>
                                </tr>
                            </thead>
                            <tbody id="recentBookings">
                                <tr><td colspan="6">Загрузка...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let clients = [];
            let masters = [];
            let services = [];
            
            async function loadAnalytics() {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('analyticsContent').style.display = 'none';
                
                try {
                    const [analyticsRes, statsRes, clientsRes, mastersRes, servicesRes, bookingsRes] = await Promise.all([
                        fetch('/api/analytics'),
                        fetch('/api/stats'),
                        fetch('/api/clients'),
                        fetch('/api/masters'),
                        fetch('/api/services'),
                        fetch('/api/bookings')
                    ]);
                    
                    const analytics = await analyticsRes.json();
                    const stats = await statsRes.json();
                    clients = await clientsRes.json();
                    masters = await mastersRes.json();
                    services = await servicesRes.json();
                    const bookings = await bookingsRes.json();
                    
                    // Update stats
                    document.getElementById('totalClients').textContent = analytics.total_clients || stats.clients_count || 0;
                    document.getElementById('totalBookings').textContent = analytics.total_bookings || stats.bookings_count || 0;
                    document.getElementById('totalRevenue').textContent = (stats.total_revenue || 0).toLocaleString() + ' ₽';
                    document.getElementById('conversionRate').textContent = (analytics.conversion_rate || 0) + '%';
                    document.getElementById('newClientsMonth').textContent = analytics.new_clients_this_month || 0;
                    
                    // Status distribution
                    const statusColors = {
                        pending: '#ffc107', confirmed: '#17a2b8', completed: '#28a745', cancelled: '#dc3545'
                    };
                    const statusNames = {
                        pending: 'Ожидает', confirmed: 'Подтверждена', completed: 'Завершена', cancelled: 'Отменена'
                    };
                    const statusDist = analytics.status_distribution || {};
                    document.getElementById('statusChart').innerHTML = Object.entries(statusDist)
                        .map(([status, count]) => `
                            <div class="pie-item">
                                <div class="pie-color" style="background: ${statusColors[status] || '#999'}"></div>
                                <span class="pie-text">${statusNames[status] || status}: ${count}</span>
                            </div>
                        `).join('') || '<p>Нет данных</p>';
                    
                    // Top masters
                    const masterBookings = analytics.bookings_by_master || {};
                    const maxBookings = Math.max(...Object.values(masterBookings), 1);
                    document.getElementById('masterChart').innerHTML = Object.entries(masterBookings)
                        .slice(0, 5)
                        .map(([masterId, count]) => {
                            const master = masters.find(m => m.id === masterId);
                            const name = master ? master.name : masterId.substring(0, 8) + '...';
                            const width = (count / maxBookings * 100);
                            return `
                                <div class="bar-item">
                                    <div class="bar-label">${name}</div>
                                    <div class="bar-container">
                                        <div class="bar" style="width: ${width}%">${count}</div>
                                    </div>
                                </div>
                            `;
                        }).join('') || '<p>Нет данных</p>';
                    
                    // Revenue by month
                    const revenueByMonth = analytics.revenue_by_month || {};
                    const maxRevenue = Math.max(...Object.values(revenueByMonth), 1);
                    document.getElementById('revenueChart').innerHTML = Object.entries(revenueByMonth)
                        .sort((a, b) => a[0].localeCompare(b[0]))
                        .slice(-6)
                        .map(([month, revenue]) => {
                            const width = (revenue / maxRevenue * 100);
                            return `
                                <div class="bar-item">
                                    <div class="bar-label">${month}</div>
                                    <div class="bar-container">
                                        <div class="bar" style="width: ${width}%">${revenue.toLocaleString()} ₽</div>
                                    </div>
                                </div>
                            `;
                        }).join('') || '<p>Нет данных</p>';
                    
                    // Recent bookings
                    const statusBadges = {
                        pending: '<span style="background:#ffc107;color:#000;padding:3px 8px;border-radius:10px;font-size:12px">Ожидает</span>',
                        confirmed: '<span style="background:#17a2b8;color:#fff;padding:3px 8px;border-radius:10px;font-size:12px">Подтверждена</span>',
                        completed: '<span style="background:#28a745;color:#fff;padding:3px 8px;border-radius:10px;font-size:12px">Завершена</span>',
                        cancelled: '<span style="background:#dc3545;color:#fff;padding:3px 8px;border-radius:10px;font-size:12px">Отменена</span>'
                    };
                    
                    document.getElementById('recentBookings').innerHTML = bookings
                        .sort((a, b) => (b.date + b.time).localeCompare(a.date + a.time))
                        .slice(0, 10)
                        .map(b => {
                            const client = clients.find(c => c.id === b.client_id);
                            const master = masters.find(m => m.id === b.master_id);
                            const service = services.find(s => s.id === b.service_id);
                            return `<tr>
                                <td>${b.date || '-'} ${b.time || ''}</td>
                                <td>${client ? client.name : '-'}</td>
                                <td>${master ? master.name : '-'}</td>
                                <td>${service ? service.name : '-'}</td>
                                <td>${b.price || 0} ₽</td>
                                <td>${statusBadges[b.status] || b.status}</td>
                            </tr>`;
                        }).join('') || '<tr><td colspan="6">Нет записей</td></tr>';
                    
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('analyticsContent').style.display = 'block';
                    
                } catch (error) {
                    console.error('Error loading analytics:', error);
                    document.getElementById('loading').innerHTML = 'Ошибка загрузки данных. <a href="javascript:loadAnalytics()">Попробовать снова</a>';
                }
            }
            
            loadAnalytics();
        </script>
    </body>
    </html>
    """


@admin_router.get("/schedule", response_class=HTMLResponse)
async def schedule_page():
    """Schedule page with Google Calendar integration"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Расписание - Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   min-height: 100vh; padding: 20px; }
            .container { max-width: 1600px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 20px; }
            
            .tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
            .tab { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer;
                  background: #f0f0f0; font-size: 14px; transition: all 0.3s; }
            .tab:hover { background: #e0e0e0; }
            .tab.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            
            .calendar-controls { display: flex; gap: 20px; margin-bottom: 20px; align-items: center; flex-wrap: wrap; }
            .date-nav { display: flex; gap: 10px; align-items: center; }
            .date-nav button { background: #667eea; color: white; border: none; padding: 8px 15px;
                              border-radius: 5px; cursor: pointer; }
            .date-nav span { font-size: 1.2em; font-weight: bold; min-width: 200px; text-align: center; }
            
            .view-toggle { display: flex; gap: 5px; }
            .view-btn { padding: 8px 15px; border: 1px solid #667eea; border-radius: 5px;
                       cursor: pointer; background: white; }
            .view-btn.active { background: #667eea; color: white; }
            
            .calendar-grid { display: grid; grid-template-columns: 80px repeat(7, 1fr); gap: 1px;
                            background: #e0e0e0; border-radius: 10px; overflow: hidden; }
            .calendar-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white; padding: 15px 5px; text-align: center; font-weight: bold; }
            .time-slot { background: #f5f5f5; padding: 5px; text-align: center; font-size: 12px;
                        min-height: 60px; display: flex; align-items: center; justify-content: center; }
            .day-column { background: white; min-height: 60px; padding: 2px; position: relative; }
            .day-column:hover { background: #f0f8ff; }
            
            .event { position: relative; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 5px 8px; border-radius: 5px; margin: 2px;
                    font-size: 11px; cursor: pointer; overflow: hidden; }
            .event:hover { transform: scale(1.02); z-index: 10; }
            .event.pending { background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%); color: #333; }
            .event.confirmed { background: linear-gradient(135deg, #17a2b8 0%, #138496 100%); }
            .event.completed { background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%); }
            .event.cancelled { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); opacity: 0.6; }
            
            .master-calendar { margin-top: 20px; }
            .master-selector { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
            .master-chip { padding: 10px 20px; border: 2px solid #667eea; border-radius: 20px;
                          cursor: pointer; background: white; transition: all 0.3s; }
            .master-chip:hover { background: #f0f0ff; }
            .master-chip.active { background: #667eea; color: white; }
            .master-chip .calendar-status { font-size: 10px; margin-left: 5px; }
            .master-chip .calendar-status.connected { color: #28a745; }
            .master-chip .calendar-status.disconnected { color: #dc3545; }
            
            .legend { display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap; }
            .legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
            .legend-color { width: 20px; height: 20px; border-radius: 4px; }
            
            .availability-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px; }
            .time-slot-btn { padding: 15px; border: 2px solid #e0e0e0; border-radius: 8px;
                            text-align: center; cursor: pointer; transition: all 0.3s; }
            .time-slot-btn.available { border-color: #28a745; background: #e8f5e9; }
            .time-slot-btn.available:hover { background: #28a745; color: white; }
            .time-slot-btn.busy { border-color: #dc3545; background: #ffebee; cursor: not-allowed; opacity: 0.6; }
            
            .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; }
            .modal.show { display: flex; }
            .modal-content { background: white; padding: 30px; border-radius: 10px; max-width: 500px;
                            width: 90%; max-height: 90vh; overflow-y: auto; }
            .modal-header { display: flex; justify-content: space-between; margin-bottom: 20px; }
            .modal-header h2 { color: #333; }
            .close-btn { background: none; border: none; font-size: 24px; cursor: pointer; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group input, .form-group select, .form-group textarea {
                width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .btn-secondary { background: #6c757d; color: white; }
            
            .salon-view { margin-top: 20px; }
            .master-row { display: flex; align-items: stretch; margin-bottom: 10px; background: #f8f9fa;
                         border-radius: 8px; overflow: hidden; }
            .master-info { width: 150px; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; display: flex; flex-direction: column; justify-content: center; }
            .master-info .name { font-weight: bold; margin-bottom: 5px; }
            .master-info .status { font-size: 11px; opacity: 0.8; }
            .master-timeline { flex: 1; display: flex; overflow-x: auto; padding: 10px; gap: 5px; }
            .timeline-event { padding: 8px 12px; border-radius: 5px; font-size: 12px; white-space: nowrap;
                             background: #667eea; color: white; }
            
            .loading { text-align: center; padding: 40px; color: #666; }
            
            @media (max-width: 768px) {
                .calendar-grid { grid-template-columns: 60px repeat(7, 1fr); }
                .calendar-header { padding: 10px 2px; font-size: 12px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📅 Расписание</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <!-- Tabs -->
                <div class="tabs">
                    <button class="tab active" onclick="showTab('salon')">🏠 Календарь салона</button>
                    <button class="tab" onclick="showTab('masters')">👨‍🎨 Календари мастеров</button>
                    <button class="tab" onclick="showTab('availability')">⏰ Доступность</button>
                </div>
                
                <!-- Salon Calendar -->
                <div id="salonTab" class="tab-content">
                    <div class="calendar-controls">
                        <div class="date-nav">
                            <button onclick="prevWeek()">← Пред.</button>
                            <span id="currentWeek">Загрузка...</span>
                            <button onclick="nextWeek()">След. →</button>
                        </div>
                        <button class="btn btn-primary" onclick="goToToday()">Сегодня</button>
                    </div>
                    
                    <div class="salon-view" id="salonCalendar">
                        <div class="loading">Загрузка расписания...</div>
                    </div>
                    
                    <div class="legend">
                        <div class="legend-item"><div class="legend-color" style="background:#ffc107"></div> Ожидает</div>
                        <div class="legend-item"><div class="legend-color" style="background:#17a2b8"></div> Подтверждена</div>
                        <div class="legend-item"><div class="legend-color" style="background:#28a745"></div> Завершена</div>
                        <div class="legend-item"><div class="legend-color" style="background:#dc3545"></div> Отменена</div>
                    </div>
                </div>
                
                <!-- Masters Calendars -->
                <div id="mastersTab" class="tab-content" style="display:none">
                    <div class="master-selector" id="masterSelector">
                        <div class="loading">Загрузка мастеров...</div>
                    </div>
                    
                    <div class="calendar-controls">
                        <div class="date-nav">
                            <button onclick="prevWeekMaster()">← Пред.</button>
                            <span id="currentWeekMaster">Загрузка...</span>
                            <button onclick="nextWeekMaster()">След. →</button>
                        </div>
                        <button class="btn btn-primary" onclick="openAddEventModal()">+ Добавить событие</button>
                    </div>
                    
                    <div id="masterCalendar">
                        <p style="text-align:center;color:#666;padding:40px">Выберите мастера для просмотра календаря</p>
                    </div>
                </div>
                
                <!-- Availability Check -->
                <div id="availabilityTab" class="tab-content" style="display:none">
                    <h3>Проверка доступности</h3>
                    <div style="display:flex;gap:20px;margin:20px 0;flex-wrap:wrap">
                        <div class="form-group" style="flex:1;min-width:200px">
                            <label>Мастер</label>
                            <select id="availMaster" onchange="checkAvailability()">
                                <option value="">Выберите мастера</option>
                            </select>
                        </div>
                        <div class="form-group" style="flex:1;min-width:200px">
                            <label>Дата</label>
                            <input type="date" id="availDate" onchange="checkAvailability()">
                        </div>
                    </div>
                    
                    <h4>Доступные слоты:</h4>
                    <div class="availability-grid" id="availabilityGrid">
                        <p>Выберите мастера и дату</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Add Event Modal -->
        <div class="modal" id="addEventModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Добавить событие</h2>
                    <button class="close-btn" onclick="closeModal()">&times;</button>
                </div>
                <form onsubmit="saveEvent(event)">
                    <div class="form-group">
                        <label>Название</label>
                        <input type="text" id="eventTitle" required placeholder="Например: Рабочий день">
                    </div>
                    <div class="form-group">
                        <label>Дата и время начала</label>
                        <input type="datetime-local" id="eventStart" required>
                    </div>
                    <div class="form-group">
                        <label>Продолжительность (минут)</label>
                        <input type="number" id="eventDuration" value="60" min="15" step="15">
                    </div>
                    <div style="display:flex;gap:10px;justify-content:flex-end">
                        <button type="button" class="btn btn-secondary" onclick="closeModal()">Отмена</button>
                        <button type="submit" class="btn btn-primary">Сохранить</button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- Event Details Modal -->
        <div class="modal" id="eventDetailsModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Детали записи</h2>
                    <button class="close-btn" onclick="closeEventDetails()">&times;</button>
                </div>
                <div id="eventDetailsContent"></div>
            </div>
        </div>
        
        <script>
            let masters = [];
            let currentMasterId = null;
            let currentWeekStart = new Date();
            let masterWeekStart = new Date();
            
            // Set to Monday
            currentWeekStart.setDate(currentWeekStart.getDate() - currentWeekStart.getDay() + 1);
            masterWeekStart.setDate(masterWeekStart.getDate() - masterWeekStart.getDay() + 1);
            
            async function loadMasters() {
                try {
                    const res = await fetch('/api/masters');
                    masters = await res.json();
                    
                    // Populate master selector
                    document.getElementById('masterSelector').innerHTML = masters
                        .filter(m => m.status === 'active')
                        .map(m => `
                            <div class="master-chip ${currentMasterId === m.id ? 'active' : ''}" onclick="selectMaster('${m.id}')">
                                ${m.name}
                                <span class="calendar-status ${m.calendar_id ? 'connected' : 'disconnected'}">
                                    ${m.calendar_id ? '●' : '○'}
                                </span>
                            </div>
                        `).join('') || '<p>Нет активных мастеров</p>';
                    
                    // Populate availability selector
                    document.getElementById('availMaster').innerHTML = 
                        '<option value="">Выберите мастера</option>' +
                        masters.filter(m => m.status === 'active')
                            .map(m => `<option value="${m.id}">${m.name}</option>`).join('');
                    
                } catch (e) {
                    console.error('Error loading masters:', e);
                }
            }
            
            function showTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
                
                event.target.classList.add('active');
                document.getElementById(tab + 'Tab').style.display = 'block';
                
                if (tab === 'salon') loadSalonCalendar();
                if (tab === 'masters' && currentMasterId) loadMasterCalendar();
            }
            
            function formatDate(date) {
                return date.toISOString().split('T')[0];
            }
            
            function formatWeek(date) {
                const end = new Date(date);
                end.setDate(end.getDate() + 6);
                const options = { day: 'numeric', month: 'short' };
                return `${date.toLocaleDateString('ru', options)} - ${end.toLocaleDateString('ru', options)}`;
            }
            
            function prevWeek() {
                currentWeekStart.setDate(currentWeekStart.getDate() - 7);
                loadSalonCalendar();
            }
            
            function nextWeek() {
                currentWeekStart.setDate(currentWeekStart.getDate() + 7);
                loadSalonCalendar();
            }
            
            function goToToday() {
                currentWeekStart = new Date();
                currentWeekStart.setDate(currentWeekStart.getDate() - currentWeekStart.getDay() + 1);
                loadSalonCalendar();
            }
            
            function prevWeekMaster() {
                masterWeekStart.setDate(masterWeekStart.getDate() - 7);
                loadMasterCalendar();
            }
            
            function nextWeekMaster() {
                masterWeekStart.setDate(masterWeekStart.getDate() + 7);
                loadMasterCalendar();
            }
            
            async function loadSalonCalendar() {
                document.getElementById('currentWeek').textContent = formatWeek(currentWeekStart);
                
                const startDate = formatDate(currentWeekStart);
                const endDate = formatDate(new Date(currentWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000));
                
                try {
                    // Get all bookings and masters
                    const [bookingsRes, mastersRes, clientsRes, servicesRes] = await Promise.all([
                        fetch('/api/bookings'),
                        fetch('/api/masters'),
                        fetch('/api/clients'),
                        fetch('/api/services')
                    ]);
                    
                    const bookings = await bookingsRes.json();
                    const mastersData = await mastersRes.json();
                    const clients = await clientsRes.json();
                    const services = await servicesRes.json();
                    
                    const activeMasters = mastersData.filter(m => m.status === 'active');
                    const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
                    
                    let html = '';
                    
                    for (const master of activeMasters) {
                        const masterBookings = bookings.filter(b => {
                            if (b.master_id !== master.id) return false;
                            const bookingDate = new Date(b.date);
                            const weekEnd = new Date(currentWeekStart.getTime() + 7 * 24 * 60 * 60 * 1000);
                            return bookingDate >= currentWeekStart && bookingDate < weekEnd;
                        });
                        
                        html += `
                            <div class="master-row">
                                <div class="master-info">
                                    <div class="name">${master.name}</div>
                                    <div class="status">${master.calendar_id ? '📅 Календарь подключен' : '⚠️ Нет календаря'}</div>
                                </div>
                                <div class="master-timeline">
                        `;
                        
                        for (let i = 0; i < 7; i++) {
                            const day = new Date(currentWeekStart);
                            day.setDate(day.getDate() + i);
                            const dateStr = formatDate(day);
                            
                            const dayBookings = masterBookings.filter(b => b.date === dateStr);
                            
                            if (dayBookings.length === 0) {
                                html += `<div class="timeline-event" style="background:#e0e0e0;color:#999">${days[i]} - свободно</div>`;
                            } else {
                                for (const b of dayBookings) {
                                    const client = clients.find(c => c.id === b.client_id);
                                    const service = services.find(s => s.id === b.service_id);
                                    const statusColors = {
                                        pending: '#ffc107', confirmed: '#17a2b8', 
                                        completed: '#28a745', cancelled: '#dc3545'
                                    };
                                    html += `
                                        <div class="timeline-event" style="background:${statusColors[b.status] || '#667eea'}"
                                             onclick="showEventDetails('${b.id}', '${client?.name || ''}', '${service?.name || ''}', '${b.date}', '${b.time}', '${b.status}', '${b.price || 0}')">
                                            ${days[i]} ${b.time || ''}<br>${client?.name?.split(' ')[0] || 'Клиент'}
                                        </div>
                                    `;
                                }
                            }
                        }
                        
                        html += '</div></div>';
                    }
                    
                    document.getElementById('salonCalendar').innerHTML = html || '<p style="text-align:center;padding:40px">Нет активных мастеров</p>';
                    
                } catch (e) {
                    console.error('Error loading salon calendar:', e);
                    document.getElementById('salonCalendar').innerHTML = '<p style="color:red;text-align:center">Ошибка загрузки</p>';
                }
            }
            
            function selectMaster(masterId) {
                currentMasterId = masterId;
                document.querySelectorAll('.master-chip').forEach(c => c.classList.remove('active'));
                event.target.closest('.master-chip').classList.add('active');
                loadMasterCalendar();
            }
            
            async function loadMasterCalendar() {
                if (!currentMasterId) return;
                
                document.getElementById('currentWeekMaster').textContent = formatWeek(masterWeekStart);
                
                const startDate = formatDate(masterWeekStart);
                const endDate = formatDate(new Date(masterWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000));
                
                try {
                    const res = await fetch(`/api/calendar/master/${currentMasterId}?start_date=${startDate}&end_date=${endDate}`);
                    const data = await res.json();
                    
                    const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
                    const hours = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00'];
                    
                    let html = `<div class="calendar-grid">`;
                    
                    // Header row
                    html += '<div class="calendar-header">Время</div>';
                    for (let i = 0; i < 7; i++) {
                        const day = new Date(masterWeekStart);
                        day.setDate(day.getDate() + i);
                        html += `<div class="calendar-header">${days[i]}<br>${day.getDate()}</div>`;
                    }
                    
                    // Time slots
                    for (const hour of hours) {
                        html += `<div class="time-slot">${hour}</div>`;
                        
                        for (let i = 0; i < 7; i++) {
                            const day = new Date(masterWeekStart);
                            day.setDate(day.getDate() + i);
                            const dateStr = formatDate(day);
                            
                            const slotEvents = data.events.filter(e => {
                                const eventDate = e.start?.substring(0, 10);
                                const eventHour = e.start?.substring(11, 16);
                                return eventDate === dateStr && eventHour === hour;
                            });
                            
                            html += '<div class="day-column">';
                            for (const evt of slotEvents) {
                                const statusClass = evt.status || '';
                                html += `
                                    <div class="event ${statusClass}" 
                                         onclick="showEventDetails('${evt.id}', '${evt.client_name || evt.title}', '${evt.service_name || ''}', '${dateStr}', '${hour}', '${evt.status || 'event'}', '${evt.price || ''}')">
                                        ${evt.title || evt.client_name || 'Занято'}
                                    </div>
                                `;
                            }
                            html += '</div>';
                        }
                    }
                    
                    html += '</div>';
                    
                    document.getElementById('masterCalendar').innerHTML = html;
                    
                } catch (e) {
                    console.error('Error loading master calendar:', e);
                    document.getElementById('masterCalendar').innerHTML = '<p style="color:red;text-align:center">Ошибка загрузки календаря</p>';
                }
            }
            
            async function checkAvailability() {
                const masterId = document.getElementById('availMaster').value;
                const date = document.getElementById('availDate').value;
                
                if (!masterId || !date) {
                    document.getElementById('availabilityGrid').innerHTML = '<p>Выберите мастера и дату</p>';
                    return;
                }
                
                try {
                    const res = await fetch(`/api/calendar/availability/${masterId}?date=${date}`);
                    const data = await res.json();
                    
                    const allSlots = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00'];
                    
                    document.getElementById('availabilityGrid').innerHTML = allSlots.map(slot => {
                        const isAvailable = data.available_slots.includes(slot);
                        return `
                            <div class="time-slot-btn ${isAvailable ? 'available' : 'busy'}"
                                 ${isAvailable ? `onclick="bookSlot('${masterId}', '${date}', '${slot}')"` : ''}>
                                ${slot}
                                <br><small>${isAvailable ? '✓ Свободно' : '✕ Занято'}</small>
                            </div>
                        `;
                    }).join('');
                    
                } catch (e) {
                    console.error('Error checking availability:', e);
                    document.getElementById('availabilityGrid').innerHTML = '<p style="color:red">Ошибка проверки</p>';
                }
            }
            
            function bookSlot(masterId, date, time) {
                window.location.href = `/bookings?master=${masterId}&date=${date}&time=${time}`;
            }
            
            function openAddEventModal() {
                if (!currentMasterId) {
                    alert('Сначала выберите мастера');
                    return;
                }
                document.getElementById('addEventModal').classList.add('show');
            }
            
            function closeModal() {
                document.getElementById('addEventModal').classList.remove('show');
            }
            
            async function saveEvent(e) {
                e.preventDefault();
                
                const title = document.getElementById('eventTitle').value;
                const start = document.getElementById('eventStart').value;
                const duration = document.getElementById('eventDuration').value;
                
                try {
                    const res = await fetch('/api/calendar/event', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            master_id: currentMasterId,
                            title: title,
                            start_time: start,
                            duration: parseInt(duration)
                        })
                    });
                    
                    if (res.ok) {
                        alert('Событие добавлено!');
                        closeModal();
                        loadMasterCalendar();
                    } else {
                        const err = await res.json();
                        alert('Ошибка: ' + (err.detail || 'Не удалось создать событие'));
                    }
                } catch (e) {
                    console.error('Error saving event:', e);
                    alert('Ошибка сохранения');
                }
            }
            
            function showEventDetails(id, clientName, serviceName, date, time, status, price) {
                const statusNames = {
                    pending: 'Ожидает подтверждения',
                    confirmed: 'Подтверждена',
                    completed: 'Завершена',
                    cancelled: 'Отменена',
                    event: 'Событие календаря'
                };
                
                document.getElementById('eventDetailsContent').innerHTML = `
                    <p><strong>Клиент:</strong> ${clientName || '-'}</p>
                    <p><strong>Услуга:</strong> ${serviceName || '-'}</p>
                    <p><strong>Дата:</strong> ${date}</p>
                    <p><strong>Время:</strong> ${time}</p>
                    <p><strong>Статус:</strong> ${statusNames[status] || status}</p>
                    ${price ? `<p><strong>Стоимость:</strong> ${price} ₽</p>` : ''}
                    ${id.startsWith('booking_') ? `
                        <div style="margin-top:20px;display:flex;gap:10px">
                            <button class="btn btn-primary" onclick="window.location.href='/bookings'">Открыть записи</button>
                        </div>
                    ` : ''}
                `;
                document.getElementById('eventDetailsModal').classList.add('show');
            }
            
            function closeEventDetails() {
                document.getElementById('eventDetailsModal').classList.remove('show');
            }
            
            // Initialize
            document.getElementById('availDate').value = formatDate(new Date());
            loadMasters();
            loadSalonCalendar();
        </script>
    </body>
    </html>
    """
