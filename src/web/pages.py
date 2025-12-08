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
                    <input type="hidden" id="originalMasterId">
                    <div class="form-group" id="idFieldGroup" style="display:none">
                        <label for="newMasterId">ID мастера (для INKA)</label>
                        <input type="text" id="newMasterId" placeholder="m_anna_fedorova" pattern="m_[a-z_]+">
                        <small style="color:#666;font-size:11px">Формат: m_имя_фамилия (латиницей, нижний регистр). Пример: m_anna_fedorova</small>
                    </div>
                    <div class="form-group">
                        <label for="name">Имя *</label>
                        <input type="text" id="name" required oninput="suggestMasterId()">
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
                        <label for="rating">Рейтинг (0-5)</label>
                        <input type="number" id="rating" min="0" max="5" step="0.1" placeholder="4.5">
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
                document.getElementById('originalMasterId').value = '';
                document.getElementById('newMasterId').value = '';
                document.getElementById('idFieldGroup').style.display = 'none';
                document.getElementById('masterModal').style.display = 'block';
            }
            
            function editMaster(id) {
                const master = allMasters.find(m => m.id === id);
                if (!master) return;
                
                document.getElementById('modalTitle').textContent = 'Редактировать мастера';
                document.getElementById('masterId').value = master.id;
                document.getElementById('originalMasterId').value = master.id;
                document.getElementById('newMasterId').value = master.id;
                document.getElementById('idFieldGroup').style.display = 'block';
                document.getElementById('name').value = master.name || '';
                document.getElementById('phone').value = master.phone || '';
                document.getElementById('specialization').value = master.specialization || '';
                document.getElementById('telegram_id').value = master.telegram_id || '';
                document.getElementById('experience').value = master.experience || '';
                document.getElementById('rating').value = master.rating || '';
                document.getElementById('instagram').value = master.instagram || '';
                document.getElementById('bio').value = master.bio || '';
                document.getElementById('calendar_id').value = master.calendar_id || '';
                document.getElementById('status').value = master.status || 'active';
                document.getElementById('masterModal').style.display = 'block';
            }
            
            // Транслитерация для генерации ID
            function transliterate(text) {
                const ru = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',' ':'_'};
                return text.toLowerCase().split('').map(c => ru[c] || c).join('').replace(/[^a-z_]/g, '');
            }
            
            function suggestMasterId() {
                const masterId = document.getElementById('masterId').value;
                // Только для новых мастеров (без ID)
                if (!masterId) {
                    const name = document.getElementById('name').value;
                    if (name) {
                        const suggestedId = 'm_' + transliterate(name);
                        document.getElementById('newMasterId').value = suggestedId;
                    }
                }
            }
            
            function closeModal() {
                document.getElementById('masterModal').style.display = 'none';
            }
            
            async function saveMaster(event) {
                event.preventDefault();
                
                const id = document.getElementById('masterId').value;
                const originalId = document.getElementById('originalMasterId').value;
                let newMasterId = document.getElementById('newMasterId').value;
                
                // Для новых мастеров - убедиться, что ID установлен
                if (!id && !newMasterId) {
                    const name = document.getElementById('name').value;
                    if (name) {
                        newMasterId = 'm_' + transliterate(name);
                    }
                }
                
                const data = {
                    name: document.getElementById('name').value,
                    phone: document.getElementById('phone').value,
                    specialization: document.getElementById('specialization').value,
                    telegram_id: document.getElementById('telegram_id').value,
                    experience: document.getElementById('experience').value,
                    rating: document.getElementById('rating').value || '0',
                    instagram: document.getElementById('instagram').value,
                    bio: document.getElementById('bio').value,
                    calendar_id: document.getElementById('calendar_id').value,
                    status: document.getElementById('status').value
                };
                
                // Если ID изменился - добавляем new_id для обновления
                if (id && newMasterId && newMasterId !== originalId) {
                    data.new_id = newMasterId;
                }
                
                // Для нового мастера - используем ID (либо предложенный, либо сгенерированный)
                if (!id && newMasterId) {
                    data.id = newMasterId;
                }
                
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
                    <select id="statusFilter" onchange="filterClients()" style="padding:10px; border-radius:5px;">
                        <option value="all">Все</option>
                        <option value="active">Активные</option>
                        <option value="deleted">Удалённые</option>
                    </select>
                    <button class="btn" onclick="openAddModal()">➕ Добавить клиента</button>
                    <button class="btn" onclick="resetFilter()" style="background:#6c757d;">Показать все</button>
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
                    let actions = '';
                    if (isDeleted) {
                        actions = `<button class="btn-edit" onclick="restoreClient('${c.id}')">♻️ Восстановить</button>`;
                    } else {
                        actions = `<button class="btn-view" onclick="viewClient('${c.id}')">👁️ Подробнее</button>
                                   <button class="btn-edit" onclick="editClient('${c.id}')">✏️</button>
                                   <button class="btn-delete" onclick="deleteClient('${c.id}', '${c.name}')">🗑️</button>`;
                    }
                    return `<tr style="${isDeleted ? 'opacity:0.5;background:#f8d7da;' : ''}">
                        <td>${c.id ? c.id.substring(0, 8) + '...' : '-'}</td>
                        <td><strong>${c.name || '-'}</strong></td>
                        <td>${c.phone || '-'}</td>
                        <td>${c.email || '-'}</td>
                        <td>${c.telegram_id || '-'}</td>
                        <td>${createdAt}</td>
                        <td>${lastVisit}</td>
                        <td>${actions}</td>
                    </tr>`;
                }).join('');
            }
            
            function filterClients() {
                const search = document.getElementById('searchInput').value.toLowerCase();
                const status = document.getElementById('statusFilter').value;
                let filtered = allClients.filter(c => {
                    const match = (c.name && c.name.toLowerCase().includes(search)) ||
                                  (c.phone && c.phone.includes(search)) ||
                                  (c.email && c.email.toLowerCase().includes(search)) ||
                                  (c.telegram_id && c.telegram_id.includes(search));
                    if (!match) return false;
                    const isDeleted = c.notes && c.notes.includes('[DELETED]');
                    if (status === 'active') return !isDeleted;
                    if (status === 'deleted') return isDeleted;
                    return true;
                });
                renderClients(filtered);
            }

            function resetFilter() {
                document.getElementById('searchInput').value = '';
                document.getElementById('statusFilter').value = 'all';
                renderClients(allClients);
            }

            async function restoreClient(id) {
                if (!confirm('Восстановить клиента?')) return;
                try {
                    const client = allClients.find(c => c.id === id);
                    if (!client) return;
                    // Удаляем [DELETED] из notes
                    let notes = client.notes || '';
                    notes = notes.replace('[DELETED]', '').trim();
                    const data = {
                        name: client.name,
                        phone: client.phone,
                        email: client.email,
                        telegram_id: client.telegram_id,
                        notes: notes
                    };
                    const response = await fetch(`/api/clients/${id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    if (response.ok && result.success) {
                        showAlert('Клиент восстановлен!', 'success');
                        loadClients();
                    } else {
                        showAlert(result.detail || 'Ошибка восстановления', 'error');
                    }
                } catch (error) {
                    showAlert('Ошибка восстановления', 'error');
                }
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
    """INKA training page with interactive chat"""
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
            .container { max-width: 1400px; margin: 0 auto; background: white;
                        border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); overflow: hidden; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 1.8em; }
            .btn-back { background: rgba(255,255,255,0.2); color: white; border: none;
                       padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .content { padding: 0; display: grid; grid-template-columns: 1fr 350px; min-height: 600px; }
            
            /* Tabs */
            .tabs { display: flex; background: #f5f5f5; border-bottom: 2px solid #e0e0e0; }
            .tab { padding: 15px 25px; cursor: pointer; border: none; background: transparent;
                   font-size: 14px; font-weight: 500; color: #666; transition: all 0.3s; }
            .tab:hover { background: #e0e0e0; }
            .tab.active { background: white; color: #667eea; border-bottom: 2px solid #667eea; margin-bottom: -2px; }
            
            /* Main Panel */
            .main-panel { display: flex; flex-direction: column; border-right: 1px solid #e0e0e0; }
            .tab-content { display: none; flex: 1; flex-direction: column; }
            .tab-content.active { display: flex; }
            
            /* Chat */
            .chat-container { flex: 1; display: flex; flex-direction: column; }
            .chat-messages { flex: 1; overflow-y: auto; padding: 20px; background: #fafafa; max-height: 450px; }
            .message { margin-bottom: 15px; display: flex; }
            .message.user { justify-content: flex-end; }
            .message.inka { justify-content: flex-start; }
            .message-bubble { max-width: 80%; padding: 12px 16px; border-radius: 18px; }
            .message.user .message-bubble { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .message.inka .message-bubble { background: #e8e8e8; color: #333; }
            .message-time { font-size: 10px; opacity: 0.7; margin-top: 4px; }
            .typing-indicator { color: #999; font-style: italic; padding: 10px 20px; }
            
            .chat-input-container { padding: 15px; background: white; border-top: 1px solid #e0e0e0; display: flex; gap: 10px; }
            .chat-input { flex: 1; padding: 12px; border: 2px solid #e0e0e0; border-radius: 25px; outline: none; }
            .chat-input:focus { border-color: #667eea; }
            .send-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
                       border: none; width: 45px; height: 45px; border-radius: 50%; cursor: pointer; font-size: 18px; }
            .send-btn:hover { transform: scale(1.1); }
            
            /* Training Cards */
            .training-section { padding: 20px; }
            .training-card { background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 15px; border: 1px solid #e0e0e0; }
            .training-card h3 { margin-bottom: 10px; color: #333; display: flex; align-items: center; gap: 8px; }
            .training-card p { color: #666; font-size: 14px; margin-bottom: 15px; }
            .training-form { display: flex; flex-direction: column; gap: 10px; }
            .training-form input, .training-form textarea, .training-form select {
                padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
            .training-form textarea { resize: vertical; min-height: 80px; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
                  border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; }
            .btn:hover { opacity: 0.9; }
            .btn-secondary { background: #6c757d; }
            .btn-success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
            .btn-danger { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            
            /* Sidebar */
            .sidebar { background: #f8f9fa; padding: 20px; display: flex; flex-direction: column; gap: 20px; }
            .sidebar-section { background: white; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; }
            .sidebar-section h3 { font-size: 14px; color: #667eea; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
            
            /* Stats */
            .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
            .stat-item { text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 8px; color: white; }
            .stat-value { font-size: 1.5em; font-weight: bold; }
            .stat-label { font-size: 10px; opacity: 0.9; }
            
            /* Knowledge Base */
            .knowledge-list { max-height: 200px; overflow-y: auto; }
            .knowledge-item { padding: 8px; border-bottom: 1px solid #eee; font-size: 13px; display: flex;
                             justify-content: space-between; align-items: center; }
            .knowledge-item:hover { background: #f5f5f5; }
            .knowledge-type { font-size: 10px; background: #667eea; color: white; padding: 2px 6px; border-radius: 10px; }
            .delete-btn { background: none; border: none; color: #dc3545; cursor: pointer; font-size: 14px; }
            
            /* Context Hints */
            .context-hints { display: flex; flex-wrap: wrap; gap: 5px; }
            .hint-tag { background: #e0e0e0; padding: 4px 10px; border-radius: 15px; font-size: 11px;
                       cursor: pointer; transition: all 0.2s; }
            .hint-tag:hover { background: #667eea; color: white; }
            
            /* Responsive */
            @media (max-width: 900px) {
                .content { grid-template-columns: 1fr; }
                .sidebar { border-top: 1px solid #e0e0e0; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧠 Обучение ИНКИ</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            <div class="content">
                <div class="main-panel">
                    <div class="tabs">
                        <button class="tab active" onclick="showTab('chat')">💬 Интерактивный чат</button>
                        <button class="tab" onclick="showTab('scenarios')">📝 Сценарии</button>
                        <button class="tab" onclick="showTab('corrections')">✏️ Коррекции</button>
                        <button class="tab" onclick="showTab('knowledge')">📚 База знаний</button>
                    </div>
                    
                    <!-- Chat Tab -->
                    <div id="chatTab" class="tab-content active">
                        <div class="chat-container">
                            <div class="chat-messages" id="chatMessages">
                                <div class="message inka">
                                    <div class="message-bubble">
                                        Привет! Я готова к обучению. Вы можете:<br><br>
                                        • Показать мне примеры правильных ответов<br>
                                        • Исправить мои ошибки<br>
                                        • Добавить новую информацию<br>
                                        • Протестировать мои знания<br><br>
                                        Начните с любого вопроса или примера!
                                    </div>
                                </div>
                            </div>
                            <div id="typingIndicator" class="typing-indicator" style="display:none">ИНКА думает...</div>
                            <div class="chat-input-container">
                                <input type="text" class="chat-input" id="chatInput" placeholder="Напишите сообщение для обучения..." onkeypress="if(event.key==='Enter')sendTrainingMessage()">
                                <button class="send-btn" onclick="sendTrainingMessage()">➤</button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Scenarios Tab -->
                    <div id="scenariosTab" class="tab-content">
                        <div class="training-section">
                            <div class="training-card">
                                <h3>📋 Добавить сценарий диалога</h3>
                                <p>Создайте пример диалога, который ИНКА должна воспроизводить</p>
                                <div class="training-form">
                                    <select id="scenarioCategory">
                                        <option value="booking">📅 Запись на приём</option>
                                        <option value="pricing">💰 Вопросы о ценах</option>
                                        <option value="masters">👨‍🎨 Информация о мастерах</option>
                                        <option value="services">💼 Описание услуг</option>
                                        <option value="objections">🤔 Работа с возражениями</option>
                                        <option value="other">📝 Другое</option>
                                    </select>
                                    <input type="text" id="scenarioTrigger" placeholder="Вопрос клиента (например: 'Сколько стоит татуировка?')">
                                    <textarea id="scenarioResponse" placeholder="Правильный ответ ИНКИ..."></textarea>
                                    <textarea id="scenarioContext" placeholder="Дополнительный контекст (опционально)..." rows="2"></textarea>
                                    <button class="btn btn-success" onclick="addScenario()">➕ Добавить сценарий</button>
                                </div>
                            </div>
                            
                            <div class="training-card">
                                <h3>📂 Сохранённые сценарии</h3>
                                <div id="scenariosList" class="knowledge-list">
                                    <p style="color:#999;text-align:center;padding:20px">Загрузка...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Corrections Tab -->
                    <div id="correctionsTab" class="tab-content">
                        <div class="training-section">
                            <div class="training-card">
                                <h3>✏️ Исправить ответ ИНКИ</h3>
                                <p>Укажите что ИНКА сказала неправильно и как нужно отвечать</p>
                                <div class="training-form">
                                    <textarea id="wrongResponse" placeholder="Неправильный ответ ИНКИ..."></textarea>
                                    <textarea id="correctResponse" placeholder="Правильный ответ..."></textarea>
                                    <input type="text" id="correctionReason" placeholder="Причина коррекции (опционально)">
                                    <button class="btn btn-danger" onclick="addCorrection()">⚠️ Добавить коррекцию</button>
                                </div>
                            </div>
                            
                            <div class="training-card">
                                <h3>📋 История коррекций</h3>
                                <div id="correctionsList" class="knowledge-list">
                                    <p style="color:#999;text-align:center;padding:20px">Загрузка...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Knowledge Tab -->
                    <div id="knowledgeTab" class="tab-content">
                        <div class="training-section">
                            <div class="training-card">
                                <h3>📚 Добавить знание</h3>
                                <p>Добавьте факт или правило, которое ИНКА должна знать</p>
                                <div class="training-form">
                                    <select id="knowledgeType">
                                        <option value="fact">📌 Факт</option>
                                        <option value="rule">📏 Правило</option>
                                        <option value="policy">📋 Политика</option>
                                        <option value="term">📖 Термин</option>
                                        <option value="faq">❓ FAQ</option>
                                    </select>
                                    <input type="text" id="knowledgeTitle" placeholder="Название/Ключевые слова">
                                    <textarea id="knowledgeContent" placeholder="Содержание..."></textarea>
                                    <div style="display:flex;gap:10px">
                                        <button class="btn btn-success" onclick="addKnowledge()">➕ Добавить</button>
                                        <button class="btn btn-secondary" onclick="importKnowledge()">📥 Импорт из файла</button>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="training-card">
                                <h3>🗂️ База знаний</h3>
                                <div style="margin-bottom:10px">
                                    <input type="text" id="knowledgeSearch" placeholder="Поиск..." style="width:100%;padding:8px;border:1px solid #ddd;border-radius:5px" oninput="searchKnowledge()">
                                </div>
                                <div id="knowledgeList" class="knowledge-list">
                                    <p style="color:#999;text-align:center;padding:20px">Загрузка...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Sidebar -->
                <div class="sidebar">
                    <div class="sidebar-section">
                        <h3>📊 Статистика обучения</h3>
                        <div class="stats-grid" id="statsGrid">
                            <div class="stat-item"><div class="stat-value" id="totalSessions">0</div><div class="stat-label">Сессий</div></div>
                            <div class="stat-item"><div class="stat-value" id="totalKnowledge">0</div><div class="stat-label">Знаний</div></div>
                            <div class="stat-item"><div class="stat-value" id="totalCorrections">0</div><div class="stat-label">Коррекций</div></div>
                        </div>
                    </div>
                    
                    <div class="sidebar-section">
                        <h3>🎯 Быстрые действия</h3>
                        <div style="display:flex;flex-direction:column;gap:8px">
                            <button class="btn" onclick="testInka()" style="font-size:12px">🧪 Тестировать ИНКУ</button>
                            <button class="btn btn-secondary" onclick="exportTraining()" style="font-size:12px">📤 Экспорт обучения</button>
                            <button class="btn btn-secondary" onclick="resetContext()" style="font-size:12px">🔄 Сбросить контекст</button>
                        </div>
                    </div>
                    
                    <div class="sidebar-section">
                        <h3>💡 Подсказки для обучения</h3>
                        <div class="context-hints">
                            <span class="hint-tag" onclick="useHint('Как отвечать на вопрос о ценах?')">💰 Цены</span>
                            <span class="hint-tag" onclick="useHint('Как записать клиента?')">📅 Запись</span>
                            <span class="hint-tag" onclick="useHint('Как работать с возражениями?')">🤔 Возражения</span>
                            <span class="hint-tag" onclick="useHint('Расскажи о мастерах')">👨‍🎨 Мастера</span>
                            <span class="hint-tag" onclick="useHint('Как описать услуги?')">💼 Услуги</span>
                            <span class="hint-tag" onclick="useHint('Правила общения с клиентами')">📋 Правила</span>
                        </div>
                    </div>
                    
                    <div class="sidebar-section">
                        <h3>📝 Последние обучения</h3>
                        <div id="recentTrainings" style="font-size:12px;color:#666">
                            <p>Загрузка...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let chatHistory = [];
            let trainingMode = 'learn'; // learn, test, correct
            
            function showTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                event.target.classList.add('active');
                document.getElementById(tab + 'Tab').classList.add('active');
            }
            
            async function sendTrainingMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (!message) return;
                
                input.value = '';
                addMessage(message, 'user');
                document.getElementById('typingIndicator').style.display = 'block';
                
                try {
                    const response = await fetch('/api/inka-training/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            message: message,
                            mode: trainingMode,
                            history: chatHistory.slice(-10)
                        })
                    });
                    
                    const data = await response.json();
                    document.getElementById('typingIndicator').style.display = 'none';
                    
                    addMessage(data.response, 'inka');
                    chatHistory.push({role: 'user', content: message});
                    chatHistory.push({role: 'assistant', content: data.response});
                    
                    // Update stats
                    loadStats();
                    loadRecentTrainings();
                    
                    // Check if learning happened
                    if (data.learned) {
                        showNotification('✅ ИНКА обучилась новому!');
                    }
                } catch (error) {
                    document.getElementById('typingIndicator').style.display = 'none';
                    addMessage('Ошибка соединения. Попробуйте ещё раз.', 'inka');
                }
            }
            
            function addMessage(text, sender) {
                const container = document.getElementById('chatMessages');
                const time = new Date().toLocaleTimeString('ru', {hour: '2-digit', minute: '2-digit'});
                container.innerHTML += `
                    <div class="message ${sender}">
                        <div class="message-bubble">
                            ${text.replace(/\\n/g, '<br>')}
                            <div class="message-time">${time}</div>
                        </div>
                    </div>
                `;
                container.scrollTop = container.scrollHeight;
            }
            
            async function addScenario() {
                const category = document.getElementById('scenarioCategory').value;
                const trigger = document.getElementById('scenarioTrigger').value;
                const response = document.getElementById('scenarioResponse').value;
                const context = document.getElementById('scenarioContext').value;
                
                if (!trigger || !response) {
                    alert('Заполните вопрос и ответ');
                    return;
                }
                
                try {
                    const res = await fetch('/api/inka-training/scenario', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({category, trigger, response, context})
                    });
                    
                    if (res.ok) {
                        showNotification('✅ Сценарий добавлен!');
                        document.getElementById('scenarioTrigger').value = '';
                        document.getElementById('scenarioResponse').value = '';
                        document.getElementById('scenarioContext').value = '';
                        loadScenarios();
                        loadStats();
                    }
                } catch (e) {
                    alert('Ошибка сохранения');
                }
            }
            
            async function addCorrection() {
                const wrong = document.getElementById('wrongResponse').value;
                const correct = document.getElementById('correctResponse').value;
                const reason = document.getElementById('correctionReason').value;
                
                if (!wrong || !correct) {
                    alert('Заполните оба поля');
                    return;
                }
                
                try {
                    const res = await fetch('/api/inka-training/correction', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({wrong_response: wrong, correct_response: correct, reason})
                    });
                    
                    if (res.ok) {
                        showNotification('✅ Коррекция сохранена!');
                        document.getElementById('wrongResponse').value = '';
                        document.getElementById('correctResponse').value = '';
                        document.getElementById('correctionReason').value = '';
                        loadCorrections();
                        loadStats();
                    }
                } catch (e) {
                    alert('Ошибка сохранения');
                }
            }
            
            async function addKnowledge() {
                const type = document.getElementById('knowledgeType').value;
                const title = document.getElementById('knowledgeTitle').value;
                const content = document.getElementById('knowledgeContent').value;
                
                if (!title || !content) {
                    alert('Заполните название и содержание');
                    return;
                }
                
                try {
                    const res = await fetch('/api/inka-training/knowledge', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({type, title, content})
                    });
                    
                    if (res.ok) {
                        showNotification('✅ Знание добавлено!');
                        document.getElementById('knowledgeTitle').value = '';
                        document.getElementById('knowledgeContent').value = '';
                        loadKnowledge();
                        loadStats();
                    }
                } catch (e) {
                    alert('Ошибка сохранения');
                }
            }
            
            async function loadStats() {
                try {
                    const res = await fetch('/api/inka-training/stats');
                    const data = await res.json();
                    document.getElementById('totalSessions').textContent = data.total_sessions || 0;
                    document.getElementById('totalKnowledge').textContent = data.total_knowledge || 0;
                    document.getElementById('totalCorrections').textContent = data.total_corrections || 0;
                } catch (e) {
                    console.error('Error loading stats:', e);
                }
            }
            
            async function loadScenarios() {
                try {
                    const res = await fetch('/api/inka-training/scenarios');
                    const data = await res.json();
                    const container = document.getElementById('scenariosList');
                    
                    if (!data.scenarios || data.scenarios.length === 0) {
                        container.innerHTML = '<p style="color:#999;text-align:center;padding:20px">Нет сценариев</p>';
                        return;
                    }
                    
                    container.innerHTML = data.scenarios.map(s => `
                        <div class="knowledge-item">
                            <div>
                                <span class="knowledge-type">${s.category}</span>
                                <strong>${s.trigger.substring(0, 40)}...</strong>
                            </div>
                            <button class="delete-btn" onclick="deleteScenario('${s.id}')">🗑️</button>
                        </div>
                    `).join('');
                } catch (e) {
                    console.error('Error loading scenarios:', e);
                }
            }
            
            async function loadCorrections() {
                try {
                    const res = await fetch('/api/inka-training/corrections');
                    const data = await res.json();
                    const container = document.getElementById('correctionsList');
                    
                    if (!data.corrections || data.corrections.length === 0) {
                        container.innerHTML = '<p style="color:#999;text-align:center;padding:20px">Нет коррекций</p>';
                        return;
                    }
                    
                    container.innerHTML = data.corrections.map(c => `
                        <div class="knowledge-item">
                            <div>
                                <span style="color:#dc3545">✗</span> ${c.wrong_response.substring(0, 30)}...<br>
                                <span style="color:#28a745">✓</span> ${c.correct_response.substring(0, 30)}...
                            </div>
                            <button class="delete-btn" onclick="deleteCorrection('${c.id}')">🗑️</button>
                        </div>
                    `).join('');
                } catch (e) {
                    console.error('Error loading corrections:', e);
                }
            }
            
            async function loadKnowledge() {
                try {
                    const res = await fetch('/api/inka-training/knowledge');
                    const data = await res.json();
                    const container = document.getElementById('knowledgeList');
                    
                    if (!data.knowledge || data.knowledge.length === 0) {
                        container.innerHTML = '<p style="color:#999;text-align:center;padding:20px">База знаний пуста</p>';
                        return;
                    }
                    
                    container.innerHTML = data.knowledge.map(k => `
                        <div class="knowledge-item">
                            <div>
                                <span class="knowledge-type">${k.type}</span>
                                <strong>${k.title}</strong>
                            </div>
                            <button class="delete-btn" onclick="deleteKnowledge('${k.id}')">🗑️</button>
                        </div>
                    `).join('');
                } catch (e) {
                    console.error('Error loading knowledge:', e);
                }
            }
            
            async function loadRecentTrainings() {
                try {
                    const res = await fetch('/api/inka-training/recent');
                    const data = await res.json();
                    const container = document.getElementById('recentTrainings');
                    
                    if (!data.recent || data.recent.length === 0) {
                        container.innerHTML = '<p style="color:#999">Нет обучений</p>';
                        return;
                    }
                    
                    container.innerHTML = data.recent.slice(0, 5).map(r => `
                        <div style="padding:5px 0;border-bottom:1px solid #eee">
                            <strong>${r.type}</strong>: ${r.summary}<br>
                            <small style="color:#999">${r.timestamp}</small>
                        </div>
                    `).join('');
                } catch (e) {
                    console.error('Error loading recent:', e);
                }
            }
            
            function useHint(hint) {
                document.getElementById('chatInput').value = hint;
                document.getElementById('chatInput').focus();
            }
            
            async function testInka() {
                trainingMode = 'test';
                addMessage('🧪 Режим тестирования активирован. Задайте мне любой вопрос как клиент, и я отвечу. Потом вы сможете оценить мой ответ.', 'inka');
            }
            
            function resetContext() {
                chatHistory = [];
                trainingMode = 'learn';
                document.getElementById('chatMessages').innerHTML = `
                    <div class="message inka">
                        <div class="message-bubble">
                            Контекст сброшен. Готова к новому обучению!
                        </div>
                    </div>
                `;
            }
            
            async function exportTraining() {
                try {
                    const res = await fetch('/api/inka-training/export');
                    const data = await res.json();
                    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'inka_training_' + new Date().toISOString().slice(0,10) + '.json';
                    a.click();
                } catch (e) {
                    alert('Ошибка экспорта');
                }
            }
            
            function searchKnowledge() {
                const query = document.getElementById('knowledgeSearch').value.toLowerCase();
                const items = document.querySelectorAll('#knowledgeList .knowledge-item');
                items.forEach(item => {
                    const text = item.textContent.toLowerCase();
                    item.style.display = text.includes(query) ? 'flex' : 'none';
                });
            }
            
            function showNotification(text) {
                const notif = document.createElement('div');
                notif.style.cssText = 'position:fixed;top:20px;right:20px;background:#28a745;color:white;padding:15px 25px;border-radius:10px;z-index:1000;animation:fadeIn 0.3s';
                notif.textContent = text;
                document.body.appendChild(notif);
                setTimeout(() => notif.remove(), 3000);
            }
            
            function importKnowledge() {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = '.json,.txt';
                input.onchange = async (e) => {
                    const file = e.target.files[0];
                    const text = await file.text();
                    try {
                        const data = JSON.parse(text);
                        await fetch('/api/inka-training/import', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(data)
                        });
                        showNotification('✅ Данные импортированы!');
                        loadKnowledge();
                        loadStats();
                    } catch (e) {
                        alert('Ошибка импорта файла');
                    }
                };
                input.click();
            }
            
            // Delete functions
            async function deleteScenario(id) {
                if (!confirm('Удалить сценарий?')) return;
                await fetch('/api/inka-training/scenario/' + id, {method: 'DELETE'});
                loadScenarios();
            }
            
            async function deleteCorrection(id) {
                if (!confirm('Удалить коррекцию?')) return;
                await fetch('/api/inka-training/correction/' + id, {method: 'DELETE'});
                loadCorrections();
            }
            
            async function deleteKnowledge(id) {
                if (!confirm('Удалить знание?')) return;
                await fetch('/api/inka-training/knowledge/' + id, {method: 'DELETE'});
                loadKnowledge();
            }
            
            // Init
            loadStats();
            loadScenarios();
            loadCorrections();
            loadKnowledge();
            loadRecentTrainings();
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
                    <button class="tab" onclick="showTab('sync')">🔄 Синхронизация</button>
                    <button class="tab" onclick="showTab('availability')">⏰ Доступность</button>
                    <button class="tab" onclick="showTab('settings')">⚙️ Настройки</button>
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
                
                <!-- Sync Tab -->
                <div id="syncTab" class="tab-content" style="display:none">
                    <h3>🔄 Синхронизация календаря с расписанием</h3>
                    <p style="color:#666;margin:10px 0 20px">Синхронизируйте Google Calendar мастера с таблицей расписания в базе данных</p>
                    
                    <div style="display:flex;gap:20px;margin-bottom:20px;flex-wrap:wrap">
                        <div class="form-group" style="flex:1;min-width:250px">
                            <label>Выберите мастера</label>
                            <select id="syncMaster" onchange="loadSyncStatus()">
                                <option value="">Выберите мастера...</option>
                            </select>
                        </div>
                    </div>
                    
                    <!-- Sync Status -->
                    <div id="syncStatusPanel" style="display:none">
                        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:20px;margin-bottom:20px">
                            <!-- Calendar Status -->
                            <div style="background:#f8f9fa;padding:20px;border-radius:10px">
                                <h4>📅 Google Calendar</h4>
                                <div id="calendarStatus">
                                    <p>Загрузка...</p>
                                </div>
                            </div>
                            
                            <!-- DB Schedule Status -->
                            <div style="background:#f8f9fa;padding:20px;border-radius:10px">
                                <h4>🗄️ Расписание в БД</h4>
                                <div id="dbScheduleStatus">
                                    <p>Загрузка...</p>
                                </div>
                            </div>
                            
                            <!-- Bookings Status -->
                            <div style="background:#f8f9fa;padding:20px;border-radius:10px">
                                <h4>📝 Записи клиентов</h4>
                                <div id="bookingsStatus">
                                    <p>Загрузка...</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Actions -->
                        <div style="background:#e8f4fd;padding:20px;border-radius:10px;margin-bottom:20px">
                            <h4>⚡ Действия</h4>
                            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:15px">
                                <button class="btn btn-primary" onclick="previewSync()">👁️ Предпросмотр синхронизации</button>
                                <button class="btn" style="background:#28a745;color:white" onclick="syncToDb()">📥 Синхронизировать в БД</button>
                                <button class="btn" style="background:#17a2b8;color:white" onclick="createDefaultSchedule()">📋 Создать стандартное расписание</button>
                            </div>
                        </div>
                        
                        <!-- Schedule Table -->
                        <div style="background:#fff;border:1px solid #ddd;border-radius:10px;overflow:hidden">
                            <h4 style="padding:15px;background:#f8f9fa;margin:0;border-bottom:1px solid #ddd">📊 Текущее расписание в БД</h4>
                            <div style="overflow-x:auto">
                                <table style="width:100%;border-collapse:collapse" id="scheduleTable">
                                    <thead>
                                        <tr style="background:#667eea;color:white">
                                            <th style="padding:12px;text-align:left">День</th>
                                            <th style="padding:12px;text-align:center">Начало</th>
                                            <th style="padding:12px;text-align:center">Конец</th>
                                            <th style="padding:12px;text-align:center">Работает</th>
                                            <th style="padding:12px;text-align:center">Действия</th>
                                        </tr>
                                    </thead>
                                    <tbody id="scheduleTableBody">
                                        <tr><td colspan="5" style="padding:20px;text-align:center">Нет данных</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        
                        <!-- Preview Results -->
                        <div id="syncPreviewResults" style="display:none;margin-top:20px;background:#fff3cd;padding:20px;border-radius:10px">
                            <h4>👁️ Предпросмотр изменений</h4>
                            <div id="previewContent"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Edit Schedule Modal -->
                <div id="editScheduleModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1000;justify-content:center;align-items:center">
                    <div style="background:white;padding:30px;border-radius:15px;width:90%;max-width:500px;box-shadow:0 10px 40px rgba(0,0,0,0.3)">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
                            <h3>✏️ Редактирование расписания</h3>
                            <button onclick="closeEditModal()" style="background:none;border:none;font-size:24px;cursor:pointer">&times;</button>
                        </div>
                        <form id="editScheduleForm" onsubmit="saveScheduleEntry(event)">
                            <input type="hidden" id="edit_entry_id">
                            <div class="form-group" style="margin-bottom:15px">
                                <label style="display:block;margin-bottom:5px;font-weight:bold">День недели</label>
                                <select id="edit_day_of_week" style="width:100%;padding:10px;border:2px solid #e0e0e0;border-radius:5px" disabled>
                                    <option value="monday">Понедельник</option>
                                    <option value="tuesday">Вторник</option>
                                    <option value="wednesday">Среда</option>
                                    <option value="thursday">Четверг</option>
                                    <option value="friday">Пятница</option>
                                    <option value="saturday">Суббота</option>
                                    <option value="sunday">Воскресенье</option>
                                </select>
                            </div>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:15px">
                                <div class="form-group">
                                    <label style="display:block;margin-bottom:5px;font-weight:bold">Начало работы</label>
                                    <input type="time" id="edit_start_time" style="width:100%;padding:10px;border:2px solid #e0e0e0;border-radius:5px" required>
                                </div>
                                <div class="form-group">
                                    <label style="display:block;margin-bottom:5px;font-weight:bold">Конец работы</label>
                                    <input type="time" id="edit_end_time" style="width:100%;padding:10px;border:2px solid #e0e0e0;border-radius:5px" required>
                                </div>
                            </div>
                            <div class="form-group" style="margin-bottom:15px">
                                <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
                                    <input type="checkbox" id="edit_is_working" style="width:20px;height:20px">
                                    <span style="font-weight:bold">Рабочий день</span>
                                </label>
                            </div>
                            <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px">
                                <button type="button" onclick="closeEditModal()" style="padding:10px 20px;border:2px solid #e0e0e0;border-radius:5px;background:white;cursor:pointer">Отмена</button>
                                <button type="submit" style="padding:10px 20px;border:none;border-radius:5px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;cursor:pointer">💾 Сохранить</button>
                            </div>
                        </form>
                    </div>
                </div>
                
                <!-- Settings Tab -->
                <div id="settingsTab" class="tab-content" style="display:none">
                    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(400px, 1fr));gap:20px">
                        <!-- Salon Calendar Settings -->
                        <div style="background:#f8f9fa;padding:20px;border-radius:10px">
                            <h3>🏠 Календарь салона</h3>
                            <p style="color:#666;margin:10px 0">Общий календарь для отображения всех записей</p>
                            <div class="form-group">
                                <label>Google Calendar ID салона</label>
                                <input type="text" id="salonCalendarId" placeholder="xxx@group.calendar.google.com">
                                <small style="color:#888">Оставьте пустым для использования только внутренней системы записей</small>
                            </div>
                            <button class="btn btn-primary" onclick="saveSalonCalendar()">💾 Сохранить</button>
                        </div>
                        
                        <!-- Instructions -->
                        <div style="background:#e8f4fd;padding:20px;border-radius:10px">
                            <h3>📖 Как добавить календарь мастера</h3>
                            <ol style="padding-left:20px;line-height:1.8">
                                <li><strong>Откройте</strong> <a href="https://calendar.google.com" target="_blank">Google Calendar</a></li>
                                <li><strong>Создайте</strong> новый календарь для мастера (+ → Создать календарь)</li>
                                <li><strong>Откройте</strong> настройки созданного календаря (⋮ → Настройки)</li>
                                <li><strong>Найдите</strong> раздел "Интеграция календаря"</li>
                                <li><strong>Скопируйте</strong> "Идентификатор календаря" (выглядит как xxx@group.calendar.google.com)</li>
                                <li><strong>Вставьте</strong> ID в поле "Google Calendar ID" при редактировании мастера</li>
                            </ol>
                            
                            <h4 style="margin-top:20px">⚠️ Важно для работы:</h4>
                            <ul style="padding-left:20px;line-height:1.8">
                                <li><strong>Откройте доступ</strong> к календарю для сервисного аккаунта:<br>
                                    <code style="background:#fff;padding:2px 6px;border-radius:3px;font-size:12px">telegram-bot-sheets-sa@tattoo-480007.iam.gserviceaccount.com</code></li>
                                <li>Добавьте этот email в настройках календаря → "Доступ для отдельных пользователей"</li>
                                <li>Дайте права "Внесение изменений"</li>
                            </ul>
                        </div>
                        
                        <!-- Masters without calendar -->
                        <div style="background:#fff3cd;padding:20px;border-radius:10px">
                            <h3>⚠️ Мастера без календаря</h3>
                            <div id="mastersWithoutCalendar">
                                <p>Загрузка...</p>
                            </div>
                            <button class="btn" style="margin-top:10px" onclick="window.location.href='/admin/masters'">
                                ✏️ Редактировать мастеров
                            </button>
                        </div>
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
                    
                    // Update masters without calendar list
                    updateMastersWithoutCalendar();
                    
                } catch (e) {
                    console.error('Error loading masters:', e);
                }
            }
            
            function updateMastersWithoutCalendar() {
                const withoutCalendar = masters.filter(m => m.status === 'active' && !m.calendar_id);
                const container = document.getElementById('mastersWithoutCalendar');
                
                if (withoutCalendar.length === 0) {
                    container.innerHTML = '<p style="color:green">✅ Все мастера имеют настроенные календари!</p>';
                } else {
                    container.innerHTML = withoutCalendar.map(m => `
                        <div style="padding:8px;margin:5px 0;background:#fff;border-radius:5px;display:flex;justify-content:space-between;align-items:center">
                            <span><strong>${m.name}</strong> - ${m.specialization || 'не указано'}</span>
                            <a href="/admin/masters" style="color:#667eea">Настроить →</a>
                        </div>
                    `).join('');
                }
            }
            
            async function saveSalonCalendar() {
                const calendarId = document.getElementById('salonCalendarId').value;
                try {
                    const response = await fetch('/api/settings/salon-calendar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ calendar_id: calendarId })
                    });
                    const result = await response.json();
                    if (result.success) {
                        alert('✅ Календарь салона сохранён!');
                    } else {
                        alert('❌ Ошибка: ' + (result.detail || 'Неизвестная ошибка'));
                    }
                } catch (e) {
                    alert('❌ Ошибка сохранения: ' + e.message);
                }
            }
            
            function showTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
                
                event.target.classList.add('active');
                document.getElementById(tab + 'Tab').style.display = 'block';
                
                if (tab === 'salon') loadSalonCalendar();
                if (tab === 'masters' && currentMasterId) loadMasterCalendar();
                if (tab === 'settings') updateMastersWithoutCalendar();
                if (tab === 'sync') populateSyncMasterSelector();
            }
            
            // ===== SYNC FUNCTIONS =====
            let syncMasterId = null;
            
            function populateSyncMasterSelector() {
                const select = document.getElementById('syncMaster');
                select.innerHTML = '<option value="">Выберите мастера...</option>' +
                    masters.filter(m => m.status === 'active')
                        .map(m => `<option value="${m.id}" ${m.calendar_id ? '' : '(нет календаря)'}>${m.name} ${m.calendar_id ? '✅' : '⚠️'}</option>`)
                        .join('');
            }
            
            async function loadSyncStatus() {
                const masterId = document.getElementById('syncMaster').value;
                if (!masterId) {
                    document.getElementById('syncStatusPanel').style.display = 'none';
                    return;
                }
                
                syncMasterId = masterId;
                document.getElementById('syncStatusPanel').style.display = 'block';
                
                try {
                    const res = await fetch(`/api/calendar/sync/${masterId}`);
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const data = await res.json();
                    
                    // Update Calendar Status
                    document.getElementById('calendarStatus').innerHTML = (data.calendar_connected && data.calendar_id)
                        ? `<p style="color:green">✅ Подключен</p>
                           <p style="font-size:12px;color:#666">ID: ${data.calendar_id?.substring(0, 30)}...</p>
                           <p>📅 События (7 дней): <strong>${data.calendar_events || 0}</strong></p>`
                        : `<p style="color:red">❌ Не подключен</p>
                           <p style="font-size:12px">Настройте Calendar ID в профиле мастера</p>`;
                    
                    // Update DB Schedule Status
                    const scheduleCount = data.db_schedule_entries || 0;
                    document.getElementById('dbScheduleStatus').innerHTML = 
                        `<p>Записей расписания: <strong>${scheduleCount}</strong></p>
                         ${scheduleCount === 0 ? '<p style="color:orange">⚠️ Нет расписания</p>' : '<p style="color:green">✅ Расписание есть</p>'}`;
                    
                    // Update Bookings Status
                    const bookingCount = data.db_bookings || 0;
                    document.getElementById('bookingsStatus').innerHTML = 
                        `<p>Активных записей: <strong>${bookingCount}</strong></p>`;
                    
                    // Update Schedule Table
                    renderScheduleTable(data.schedule || []);
                    
                } catch (e) {
                    console.error('Error loading sync status:', e);
                    alert('Ошибка загрузки статуса синхронизации');
                }
            }
            
            // Store current schedule data for editing
            let currentScheduleData = [];
            
            function renderScheduleTable(schedule) {
                currentScheduleData = schedule; // Store for editing
                const dayNames = {
                    'monday': 'Понедельник', 'tuesday': 'Вторник', 'wednesday': 'Среда',
                    'thursday': 'Четверг', 'friday': 'Пятница', 'saturday': 'Суббота', 'sunday': 'Воскресенье'
                };
                const dayOrder = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
                
                // Sort by day of week
                schedule.sort((a, b) => dayOrder.indexOf(a.day_of_week) - dayOrder.indexOf(b.day_of_week));
                
                const tbody = document.getElementById('scheduleTableBody');
                if (!schedule.length) {
                    tbody.innerHTML = '<tr><td colspan="5" style="padding:20px;text-align:center;color:#666">Расписание не настроено. Создайте стандартное расписание.</td></tr>';
                    return;
                }
                
                tbody.innerHTML = schedule.map(s => {
                    const isWorking = s.is_working?.toString().toLowerCase() === 'true';
                    return `<tr style="background:${isWorking ? '#e8f5e9' : '#ffebee'}">
                        <td style="padding:12px">${dayNames[s.day_of_week] || s.day_of_week}</td>
                        <td style="padding:12px;text-align:center">${s.start_time || '-'}</td>
                        <td style="padding:12px;text-align:center">${s.end_time || '-'}</td>
                        <td style="padding:12px;text-align:center">${isWorking ? '✅ Да' : '❌ Нет'}</td>
                        <td style="padding:12px;text-align:center">
                            <button onclick="editScheduleEntry('${s.id}')" style="padding:5px 10px;cursor:pointer;background:#ffc107;border:none;border-radius:3px" title="Редактировать">✏️</button>
                            <button onclick="toggleWorkDay('${s.id}', ${!isWorking})" style="padding:5px 10px;cursor:pointer;background:${isWorking ? '#dc3545' : '#28a745'};border:none;border-radius:3px;color:white" title="${isWorking ? 'Отключить' : 'Включить'}">${isWorking ? '🚫' : '✅'}</button>
                        </td>
                    </tr>`;
                }).join('');
            }
            
            function editScheduleEntry(entryId) {
                const entry = currentScheduleData.find(s => s.id === entryId);
                if (!entry) {
                    alert('Запись не найдена');
                    return;
                }
                
                // Fill form
                document.getElementById('edit_entry_id').value = entry.id;
                document.getElementById('edit_day_of_week').value = entry.day_of_week || 'monday';
                document.getElementById('edit_start_time').value = entry.start_time || '10:00';
                document.getElementById('edit_end_time').value = entry.end_time || '19:00';
                document.getElementById('edit_is_working').checked = entry.is_working?.toString().toLowerCase() === 'true';
                
                // Show modal
                document.getElementById('editScheduleModal').style.display = 'flex';
            }
            
            function closeEditModal() {
                document.getElementById('editScheduleModal').style.display = 'none';
            }
            
            async function saveScheduleEntry(event) {
                event.preventDefault();
                
                const entryId = document.getElementById('edit_entry_id').value;
                const data = {
                    day_of_week: document.getElementById('edit_day_of_week').value,
                    start_time: document.getElementById('edit_start_time').value,
                    end_time: document.getElementById('edit_end_time').value,
                    is_working: document.getElementById('edit_is_working').checked ? 'true' : 'false'
                };
                
                try {
                    const res = await fetch(`/api/schedule/${entryId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    if (res.ok) {
                        closeEditModal();
                        loadSyncStatus(); // Refresh the table
                        alert('✅ Расписание обновлено');
                    } else {
                        const error = await res.json();
                        alert('Ошибка: ' + (error.detail || 'Не удалось сохранить'));
                    }
                } catch (e) {
                    console.error('Error saving schedule:', e);
                    alert('Ошибка сохранения');
                }
            }
            
            async function previewSync() {
                if (!syncMasterId) return alert('Выберите мастера');
                
                try {
                    const res = await fetch(`/api/calendar/sync/${syncMasterId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'preview' })
                    });
                    const data = await res.json();
                    
                    const preview = document.getElementById('syncPreviewResults');
                    preview.style.display = 'block';
                    
                    const dayNames = {
                        'monday': 'Понедельник', 'tuesday': 'Вторник', 'wednesday': 'Среда',
                        'thursday': 'Четверг', 'friday': 'Пятница', 'saturday': 'Суббота', 'sunday': 'Воскресенье'
                    };
                    
                    let html = `<p>${data.message}</p>`;
                    if (Object.keys(data.detected_working_days || {}).length > 0) {
                        html += '<table style="width:100%;margin-top:10px;border-collapse:collapse">';
                        html += '<tr style="background:#667eea;color:white"><th style="padding:8px">День</th><th style="padding:8px">Начало</th><th style="padding:8px">Конец</th></tr>';
                        for (const [day, hours] of Object.entries(data.detected_working_days)) {
                            html += `<tr><td style="padding:8px;border:1px solid #ddd">${dayNames[day] || day}</td>
                                    <td style="padding:8px;border:1px solid #ddd;text-align:center">${hours.start}</td>
                                    <td style="padding:8px;border:1px solid #ddd;text-align:center">${hours.end}</td></tr>`;
                        }
                        html += '</table>';
                    } else {
                        html += '<p style="color:orange">⚠️ Не найдено событий о рабочем времени в календаре. Используйте "Создать стандартное расписание".</p>';
                    }
                    
                    document.getElementById('previewContent').innerHTML = html;
                    
                } catch (e) {
                    console.error('Error previewing sync:', e);
                    alert('Ошибка предпросмотра');
                }
            }
            
            async function syncToDb() {
                if (!syncMasterId) return alert('Выберите мастера');
                if (!confirm('Синхронизировать расписание из календаря в БД?')) return;
                
                try {
                    const res = await fetch(`/api/calendar/sync/${syncMasterId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'sync_to_db' })
                    });
                    const data = await res.json();
                    
                    alert(data.message);
                    loadSyncStatus();
                    
                } catch (e) {
                    console.error('Error syncing:', e);
                    alert('Ошибка синхронизации');
                }
            }
            
            async function createDefaultSchedule() {
                if (!syncMasterId) return alert('Выберите мастера');
                
                const startTime = prompt('Время начала работы (формат HH:MM):', '10:00');
                if (!startTime) return;
                
                const endTime = prompt('Время окончания работы (формат HH:MM):', '19:00');
                if (!endTime) return;
                
                const workDays = confirm('Включить воскресенье как рабочий день?') 
                    ? ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    : ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
                
                try {
                    const res = await fetch(`/api/calendar/sync/${syncMasterId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            action: 'create_default_schedule',
                            default_hours: { start: startTime, end: endTime },
                            working_days: workDays
                        })
                    });
                    const data = await res.json();
                    
                    alert(data.message);
                    loadSyncStatus();
                    
                } catch (e) {
                    console.error('Error creating schedule:', e);
                    alert('Ошибка создания расписания');
                }
            }
            
            async function toggleWorkDay(entryId, newValue) {
                try {
                    const res = await fetch(`/api/schedule/${entryId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ is_working: newValue ? 'TRUE' : 'FALSE' })
                    });
                    
                    if (res.ok) {
                        loadSyncStatus();
                    } else {
                        alert('Ошибка обновления');
                    }
                } catch (e) {
                    console.error('Error toggling work day:', e);
                }
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
                    
                    if (!bookingsRes.ok || !mastersRes.ok || !clientsRes.ok || !servicesRes.ok) {
                        throw new Error('Failed to fetch data from API');
                    }
                    
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
                    if (!res.ok) {
                        throw new Error(`HTTP Error: ${res.status}`);
                    }
                    const data = await res.json();
                    
                    if (!data.success) {
                        throw new Error(data.detail || 'API returned error');
                    }
                    
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
                            
                            const eventsArr = (data.calendar_events || data.events || []);
                            const slotEvents = eventsArr.filter(e => {
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
                            <button class="btn btn-primary" onclick="window.location.href='/admin/bookings'">Открыть записи</button>
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


@admin_router.get("/admins", response_class=HTMLResponse)
async def admins_page():
    """Admins management page"""
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Управление Админами - Admin Panel</title>
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
            .btn-password { background: #f39c12; color: white; border: none; padding: 8px 12px;
                           border-radius: 4px; cursor: pointer; margin-right: 5px; }
            .btn-toggle { background: #27ae60; color: white; border: none; padding: 8px 12px;
                         border-radius: 4px; cursor: pointer; margin-right: 5px; }
            .btn-toggle.inactive { background: #95a5a6; }
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
            .role-superadmin { color: #9b59b6; font-weight: bold; }
            .role-admin { color: #3498db; font-weight: bold; }
            .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
            .search-box input { flex: 1; padding: 10px; border: 2px solid #e0e0e0; border-radius: 5px; }
            .alert { padding: 15px; border-radius: 5px; margin-bottom: 20px; display: none; }
            .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .password-hint { font-size: 12px; color: #666; margin-top: 5px; }
            .info-box { background: #e3f2fd; border: 1px solid #bbdefb; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .info-box h3 { color: #1976d2; margin-bottom: 10px; }
            .info-box p { color: #333; font-size: 14px; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👤 Управление Админами</h1>
                <button class="btn-back" onclick="window.location.href='/'">← Назад</button>
            </div>
            
            <div class="content">
                <div id="alert" class="alert"></div>
                
                <div class="info-box">
                    <h3>ℹ️ Информация</h3>
                    <p>
                        <strong>Роли:</strong><br>
                        • <span class="role-superadmin">Superadmin</span> - полные права, нельзя удалить последнего<br>
                        • <span class="role-admin">Admin</span> - доступ к админ-панели<br><br>
                        <strong>Telegram ID</strong> - нужен для доступа к боту как админ
                    </p>
                </div>
                
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Поиск по имени или роли..." oninput="filterAdmins()">
                    <button class="btn" onclick="openAddModal()">➕ Добавить админа</button>
                </div>
                
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Логин</th>
                                <th>Роль</th>
                                <th>Telegram ID</th>
                                <th>Создан</th>
                                <th>Последний вход</th>
                                <th>Статус</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody id="adminsList">
                            <tr><td colspan="8" style="text-align:center">Загрузка...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Add/Edit Admin Modal -->
        <div id="adminModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modalTitle">Добавить админа</h2>
                    <span class="close" onclick="closeModal()">&times;</span>
                </div>
                <form id="adminForm" onsubmit="saveAdmin(event)">
                    <input type="hidden" id="adminId" name="adminId">
                    
                    <div class="form-group">
                        <label for="username">Логин *</label>
                        <input type="text" id="username" name="username" required minlength="3">
                    </div>
                    
                    <div class="form-group" id="passwordGroup">
                        <label for="password">Пароль *</label>
                        <input type="password" id="password" name="password" minlength="6">
                        <p class="password-hint">Минимум 6 символов</p>
                    </div>
                    
                    <div class="form-group">
                        <label for="role">Роль</label>
                        <select id="role" name="role">
                            <option value="admin">Admin</option>
                            <option value="superadmin">Superadmin</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="telegram_id">Telegram ID</label>
                        <input type="text" id="telegram_id" name="telegram_id" placeholder="123456789">
                        <p class="password-hint">Числовой ID пользователя Telegram (для бота)</p>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn btn-cancel" onclick="closeModal()">Отмена</button>
                        <button type="submit" class="btn btn-save">Сохранить</button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- Change Password Modal -->
        <div id="passwordModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>🔐 Изменить пароль</h2>
                    <span class="close" onclick="closePasswordModal()">&times;</span>
                </div>
                <form id="passwordForm" onsubmit="changePassword(event)">
                    <input type="hidden" id="pwdAdminId">
                    <p id="pwdAdminName" style="margin-bottom: 20px; font-weight: bold; color: #333;"></p>
                    
                    <div class="form-group">
                        <label for="newPassword">Новый пароль *</label>
                        <input type="password" id="newPassword" name="newPassword" required minlength="6">
                        <p class="password-hint">Минимум 6 символов</p>
                    </div>
                    
                    <div class="form-group">
                        <label for="confirmPassword">Подтвердите пароль *</label>
                        <input type="password" id="confirmPassword" name="confirmPassword" required minlength="6">
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn btn-cancel" onclick="closePasswordModal()">Отмена</button>
                        <button type="submit" class="btn btn-save">Изменить пароль</button>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
            let allAdmins = [];
            
            async function loadAdmins() {
                try {
                    const response = await fetch('/api/admins');
                    allAdmins = await response.json();
                    renderAdmins(allAdmins);
                } catch (error) {
                    console.error('Error loading admins:', error);
                    showAlert('Ошибка загрузки данных', 'error');
                }
            }
            
            function renderAdmins(admins) {
                const tbody = document.getElementById('adminsList');
                if (!admins || admins.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center">Нет админов</td></tr>';
                    return;
                }
                tbody.innerHTML = admins.map(a => {
                    const statusClass = a.is_active ? 'status-active' : 'status-inactive';
                    const statusText = a.is_active ? 'Активен' : 'Неактивен';
                    const roleClass = a.role === 'superadmin' ? 'role-superadmin' : 'role-admin';
                    const roleText = a.role === 'superadmin' ? 'Superadmin' : 'Admin';
                    const createdAt = a.created_at ? new Date(a.created_at).toLocaleDateString('ru-RU') : '-';
                    const lastLogin = a.last_login ? new Date(a.last_login).toLocaleString('ru-RU') : 'Никогда';
                    const toggleText = a.is_active ? '⏸️' : '▶️';
                    const toggleClass = a.is_active ? '' : 'inactive';
                    
                    return `<tr>
                        <td>${a.id ? a.id.substring(0, 12) + '...' : '-'}</td>
                        <td><strong>${a.username || '-'}</strong></td>
                        <td class="${roleClass}">${roleText}</td>
                        <td>${a.telegram_id || '-'}</td>
                        <td>${createdAt}</td>
                        <td>${lastLogin}</td>
                        <td class="${statusClass}">${statusText}</td>
                        <td>
                            <button class="btn-edit" onclick="editAdmin('${a.id}')" title="Редактировать">✏️</button>
                            <button class="btn-password" onclick="openPasswordModal('${a.id}', '${a.username}')" title="Изменить пароль">🔐</button>
                            <button class="btn-toggle ${toggleClass}" onclick="toggleStatus('${a.id}')" title="${a.is_active ? 'Деактивировать' : 'Активировать'}">${toggleText}</button>
                            <button class="btn-delete" onclick="deleteAdmin('${a.id}', '${a.username}')" title="Удалить">🗑️</button>
                        </td>
                    </tr>`;
                }).join('');
            }
            
            function filterAdmins() {
                const search = document.getElementById('searchInput').value.toLowerCase();
                const filtered = allAdmins.filter(a => 
                    (a.username && a.username.toLowerCase().includes(search)) ||
                    (a.role && a.role.toLowerCase().includes(search)) ||
                    (a.telegram_id && a.telegram_id.toString().includes(search))
                );
                renderAdmins(filtered);
            }
            
            function openAddModal() {
                document.getElementById('modalTitle').textContent = 'Добавить админа';
                document.getElementById('adminForm').reset();
                document.getElementById('adminId').value = '';
                document.getElementById('password').required = true;
                document.getElementById('passwordGroup').style.display = 'block';
                document.getElementById('adminModal').style.display = 'block';
            }
            
            function editAdmin(id) {
                const admin = allAdmins.find(a => a.id === id);
                if (!admin) return;
                
                document.getElementById('modalTitle').textContent = 'Редактировать админа';
                document.getElementById('adminId').value = admin.id;
                document.getElementById('username').value = admin.username || '';
                document.getElementById('role').value = admin.role || 'admin';
                document.getElementById('telegram_id').value = admin.telegram_id || '';
                document.getElementById('password').required = false;
                document.getElementById('password').value = '';
                document.getElementById('passwordGroup').style.display = 'none';
                document.getElementById('adminModal').style.display = 'block';
            }
            
            function closeModal() {
                document.getElementById('adminModal').style.display = 'none';
            }
            
            function openPasswordModal(id, username) {
                document.getElementById('pwdAdminId').value = id;
                document.getElementById('pwdAdminName').textContent = `Админ: ${username}`;
                document.getElementById('passwordForm').reset();
                document.getElementById('passwordModal').style.display = 'block';
            }
            
            function closePasswordModal() {
                document.getElementById('passwordModal').style.display = 'none';
            }
            
            async function saveAdmin(event) {
                event.preventDefault();
                
                const id = document.getElementById('adminId').value;
                
                const data = {
                    username: document.getElementById('username').value,
                    role: document.getElementById('role').value,
                    telegram_id: document.getElementById('telegram_id').value || null
                };
                
                // Only include password for new admins
                if (!id) {
                    data.password = document.getElementById('password').value;
                }
                
                try {
                    const url = id ? `/api/admins/${id}` : '/api/admins';
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
                        loadAdmins();
                    } else {
                        showAlert(result.detail || result.message || 'Ошибка сохранения', 'error');
                    }
                } catch (error) {
                    console.error('Save error:', error);
                    showAlert('Ошибка сохранения', 'error');
                }
            }
            
            async function changePassword(event) {
                event.preventDefault();
                
                const adminId = document.getElementById('pwdAdminId').value;
                const newPassword = document.getElementById('newPassword').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                
                if (newPassword !== confirmPassword) {
                    showAlert('Пароли не совпадают', 'error');
                    return;
                }
                
                try {
                    const response = await fetch(`/api/admins/${adminId}/change-password`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ new_password: newPassword })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert(result.message || 'Пароль изменен!', 'success');
                        closePasswordModal();
                    } else {
                        showAlert(result.detail || result.message || 'Ошибка изменения пароля', 'error');
                    }
                } catch (error) {
                    console.error('Password change error:', error);
                    showAlert('Ошибка изменения пароля', 'error');
                }
            }
            
            async function toggleStatus(id) {
                const admin = allAdmins.find(a => a.id === id);
                if (!admin) return;
                
                const action = admin.is_active ? 'деактивировать' : 'активировать';
                if (!confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} админа "${admin.username}"?`)) return;
                
                try {
                    const response = await fetch(`/api/admins/${id}/toggle-status`, { method: 'PUT' });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert(result.message || 'Статус изменен!', 'success');
                        loadAdmins();
                    } else {
                        showAlert(result.detail || 'Ошибка изменения статуса', 'error');
                    }
                } catch (error) {
                    console.error('Toggle error:', error);
                    showAlert('Ошибка изменения статуса', 'error');
                }
            }
            
            async function deleteAdmin(id, name) {
                if (!confirm(`Удалить админа "${name}"? Это действие нельзя отменить!`)) return;
                
                try {
                    const response = await fetch(`/api/admins/${id}`, { method: 'DELETE' });
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showAlert(result.message || 'Админ удален!', 'success');
                        loadAdmins();
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
                const adminModal = document.getElementById('adminModal');
                const passwordModal = document.getElementById('passwordModal');
                if (event.target === adminModal) {
                    closeModal();
                }
                if (event.target === passwordModal) {
                    closePasswordModal();
                }
            }
            
            // Load data on page load
            loadAdmins();
        </script>
    </body>
    </html>
    """
