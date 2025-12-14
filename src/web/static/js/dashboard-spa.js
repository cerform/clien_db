/**
 * Dashboard SPA - Single Page Application for Tattoo Salon
 * Handles tab navigation and dynamic data loading
 */

// Global state
let allClients = [];
let allMasters = [];
let allBookings = [];
let allServices = [];
let allAdmins = [];

// ==================== TAB NAVIGATION ====================

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');

            // Load data for the tab if not loaded yet
            loadTabData(tabName);
        });
    });
}

// ==================== DATA LOADING ====================

async function loadTabData(tabName) {
    switch(tabName) {
        case 'dashboard':
            if (document.getElementById('stats-container').innerHTML.includes('spinner')) {
                await loadDashboardStats();
            }
            break;
        case 'clients':
            if (allClients.length === 0) {
                await loadClients();
            }
            break;
        case 'masters':
            if (allMasters.length === 0) {
                await loadMasters();
            }
            break;
        case 'bookings':
            if (allBookings.length === 0) {
                await loadBookings();
            }
            break;
        case 'services':
            if (allServices.length === 0) {
                await loadServices();
            }
            break;
        case 'inka':
            if (document.getElementById('inka-container').innerHTML.includes('spinner')) {
                await loadInkaStats();
            }
            break;
        case 'training':
            if (allConversations.length === 0) {
                await loadTrainingData();
            }
            break;
        case 'admins':
            await loadAdmins();
            break;
    }
}

// ==================== DASHBOARD STATS ====================

async function loadDashboardStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        const container = document.getElementById('stats-container');
        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-icon blue">👥</div>
                <div class="stat-value">${stats.total_clients}</div>
                <div class="stat-label">Всего клиентов</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon green">✂️</div>
                <div class="stat-value">${stats.total_masters}</div>
                <div class="stat-label">Мастеров</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon orange">📅</div>
                <div class="stat-value">${stats.active_bookings}</div>
                <div class="stat-label">Активных записей</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon purple">💰</div>
                <div class="stat-value">${formatCurrency(stats.revenue_month)}</div>
                <div class="stat-label">Выручка за месяц</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon blue">📊</div>
                <div class="stat-value">${stats.total_bookings}</div>
                <div class="stat-label">Всего записей</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon green">💼</div>
                <div class="stat-value">${stats.total_services}</div>
                <div class="stat-label">Услуг</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon orange">👤</div>
                <div class="stat-value">+${stats.new_clients_week}</div>
                <div class="stat-label">Новых за неделю</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon purple">✅</div>
                <div class="stat-value">${stats.completion_rate}%</div>
                <div class="stat-label">Процент завершения</div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading stats:', error);
        showError('stats-container', 'Не удалось загрузить статистику');
    }
}

// ==================== CLIENTS ====================

async function loadClients() {
    try {
        const response = await fetch('/api/clients');
        allClients = await response.json();
        renderClients(allClients);

        // Setup search
        document.getElementById('clients-search').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = allClients.filter(client =>
                client.name.toLowerCase().includes(query) ||
                client.email.toLowerCase().includes(query) ||
                client.phone.includes(query)
            );
            renderClients(filtered);
        });
    } catch (error) {
        console.error('Error loading clients:', error);
        showError('clients-container', 'Не удалось загрузить клиентов');
    }
}

function renderClients(clients) {
    const container = document.getElementById('clients-container');

    if (clients.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">👥</div>
                <p>Клиентов не найдено</p>
            </div>
        `;
        return;
    }

    container.innerHTML = clients.map(client => `
        <div class="data-card">
            <div class="data-card-header">
                <div>
                    <div class="data-card-title">${client.name}</div>
                    <div class="data-card-subtitle">Клиент #${client.id}</div>
                </div>
                <span class="badge badge-success">Активен</span>
            </div>
            <div class="data-card-body">
                <div class="data-row">
                    <span class="data-label">📧 Email</span>
                    <span class="data-value">${client.email}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">📱 Телефон</span>
                    <span class="data-value">${client.phone}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">🗓️ Регистрация</span>
                    <span class="data-value">${formatDate(client.created_at)}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">🔄 Визитов</span>
                    <span class="data-value">${client.visits_count}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">📅 Последний визит</span>
                    <span class="data-value">${formatDate(client.last_visit)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// ==================== MASTERS ====================

async function loadMasters() {
    try {
        const response = await fetch('/api/masters');
        allMasters = await response.json();
        renderMasters(allMasters);

        // Setup search
        document.getElementById('masters-search').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = allMasters.filter(master =>
                master.name.toLowerCase().includes(query) ||
                master.specialization.toLowerCase().includes(query)
            );
            renderMasters(filtered);
        });
    } catch (error) {
        console.error('Error loading masters:', error);
        showError('masters-container', 'Не удалось загрузить мастеров');
    }
}

function renderMasters(masters) {
    const container = document.getElementById('masters-container');

    if (masters.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✂️</div>
                <p>Мастеров не найдено</p>
            </div>
        `;
        return;
    }

    container.innerHTML = masters.map(master => `
        <div class="data-card">
            <div class="data-card-header">
                <div>
                    <div class="data-card-title">${master.name}</div>
                    <div class="data-card-subtitle">${master.specialization}</div>
                </div>
                <span class="badge ${master.is_active ? 'badge-success' : 'badge-danger'}">
                    ${master.is_active ? 'Активен' : 'Неактивен'}
                </span>
            </div>
            <div class="data-card-body">
                <div class="data-row">
                    <span class="data-label">⭐ Рейтинг</span>
                    <span class="data-value rating">${'★'.repeat(Math.floor(master.rating))}${'☆'.repeat(5 - Math.floor(master.rating))} ${master.rating}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">✅ Работ выполнено</span>
                    <span class="data-value">${master.completed_works}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">📧 Email</span>
                    <span class="data-value">${master.email}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">📱 Телефон</span>
                    <span class="data-value">${master.phone}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// ==================== BOOKINGS ====================

async function loadBookings() {
    try {
        const response = await fetch('/api/bookings');
        allBookings = await response.json();
        renderBookings(allBookings);

        // Setup search
        document.getElementById('bookings-search').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = allBookings.filter(booking =>
                booking.client_name.toLowerCase().includes(query) ||
                booking.master_name.toLowerCase().includes(query) ||
                booking.service_name.toLowerCase().includes(query) ||
                booking.booking_date.includes(query)
            );
            renderBookings(filtered);
        });
    } catch (error) {
        console.error('Error loading bookings:', error);
        showError('bookings-container', 'Не удалось загрузить записи');
    }
}

function renderBookings(bookings) {
    const container = document.getElementById('bookings-container');

    if (bookings.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📅</div>
                <p>Записей не найдено</p>
            </div>
        `;
        return;
    }

    // Sort bookings by date (most recent first)
    bookings.sort((a, b) => new Date(b.booking_date) - new Date(a.booking_date));

    container.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Клиент</th>
                    <th>Мастер</th>
                    <th>Услуга</th>
                    <th>Дата</th>
                    <th>Время</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                ${bookings.map(booking => `
                    <tr>
                        <td>#${booking.id}</td>
                        <td>${booking.client_name}</td>
                        <td>${booking.master_name}</td>
                        <td>${booking.service_name}</td>
                        <td>${formatDate(booking.booking_date)}</td>
                        <td>${booking.start_time} - ${booking.end_time}</td>
                        <td><span class="badge ${getStatusBadgeClass(booking.status)}">${getStatusText(booking.status)}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// ==================== SERVICES ====================

async function loadServices() {
    try {
        const response = await fetch('/api/services');
        allServices = await response.json();
        renderServices(allServices);

        // Setup search
        document.getElementById('services-search').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = allServices.filter(service =>
                service.name.toLowerCase().includes(query) ||
                service.category.toLowerCase().includes(query) ||
                service.description.toLowerCase().includes(query)
            );
            renderServices(filtered);
        });
    } catch (error) {
        console.error('Error loading services:', error);
        showError('services-container', 'Не удалось загрузить услуги');
    }
}

function renderServices(services) {
    const container = document.getElementById('services-container');

    if (services.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💼</div>
                <p>Услуг не найдено</p>
            </div>
        `;
        return;
    }

    container.innerHTML = services.map(service => `
        <div class="data-card">
            <div class="data-card-header">
                <div>
                    <div class="data-card-title">${service.name}</div>
                    <div class="data-card-subtitle">${service.description}</div>
                </div>
                <span class="badge ${service.is_active ? 'badge-success' : 'badge-danger'}">
                    ${service.is_active ? 'Активна' : 'Неактивна'}
                </span>
            </div>
            <div class="data-card-body">
                <div class="data-row">
                    <span class="data-label">💰 Цена</span>
                    <span class="data-value">${formatCurrency(service.price)}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">⏱️ Длительность</span>
                    <span class="data-value">${service.duration_minutes} мин</span>
                </div>
                <div class="data-row">
                    <span class="data-label">📂 Категория</span>
                    <span class="data-value">${getCategoryText(service.category)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// ==================== INKA AI STATS ====================

async function loadInkaStats() {
    try {
        const response = await fetch('/api/inka-training-stats');
        const stats = await response.json();

        const container = document.getElementById('inka-container');
        container.innerHTML = `
            <div class="stats-grid mb-xl">
                <div class="stat-card">
                    <div class="stat-icon blue">💬</div>
                    <div class="stat-value">${stats.total_conversations}</div>
                    <div class="stat-label">Всего диалогов</div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon green">📨</div>
                    <div class="stat-value">${stats.total_messages}</div>
                    <div class="stat-label">Сообщений</div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon orange">⚡</div>
                    <div class="stat-value">${stats.avg_response_time}s</div>
                    <div class="stat-label">Среднее время ответа</div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon purple">⭐</div>
                    <div class="stat-value">${stats.satisfaction_rate}%</div>
                    <div class="stat-label">Удовлетворённость</div>
                </div>
            </div>

            <div class="card mb-xl">
                <div class="card-header">
                    <h3 class="card-title">🎯 Топ интентов</h3>
                </div>
                <div class="card-body">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Интент</th>
                                <th>Количество</th>
                                <th>Процент</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${stats.top_intents.map(intent => `
                                <tr>
                                    <td>${getIntentText(intent.intent)}</td>
                                    <td>${intent.count}</td>
                                    <td>
                                        <div class="flex items-center gap-md">
                                            <div style="width: 100px; height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden;">
                                                <div style="width: ${intent.percentage}%; height: 100%; background: var(--accent-primary);"></div>
                                            </div>
                                            <span>${intent.percentage}%</span>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">🌍 Языки</h3>
                </div>
                <div class="card-body">
                    <div class="grid grid-3">
                        <div class="text-center p-lg">
                            <div class="stat-value text-accent">${stats.languages.ru}</div>
                            <div class="stat-label">🇷🇺 Русский</div>
                        </div>
                        <div class="text-center p-lg">
                            <div class="stat-value text-accent">${stats.languages.en}</div>
                            <div class="stat-label">🇬🇧 English</div>
                        </div>
                        <div class="text-center p-lg">
                            <div class="stat-value text-accent">${stats.languages.he}</div>
                            <div class="stat-label">🇮🇱 עברית</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading INKA stats:', error);
        showError('inka-container', 'Не удалось загрузить статистику INKA');
    }
}

// ==================== ADMINS ====================

async function loadAdmins() {
    try {
        const response = await fetch('/api/admin/admins');
        const data = await response.json();
        allAdmins = data.admins;
        renderAdmins(allAdmins);
    } catch (error) {
        console.error('Error loading admins:', error);
        showError('admins-container', 'Не удалось загрузить администраторов');
    }
}

function renderAdmins(admins) {
    const container = document.getElementById('admins-container');

    if (admins.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🛡️</div>
                <p>Администраторов не найдено</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody>
                ${admins.map(adminId => `
                    <tr>
                        <td>${adminId}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="deleteAdmin(${adminId})">Удалить</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function openAddAdminModal() {
    openModal('Добавить администратора', `
        <form id="admin-form">
            <div class="form-group">
                <label for="admin-id">Telegram ID</label>
                <input type="number" id="admin-id" name="admin_id" class="form-input" required>
            </div>
        </form>
    `, saveAdmin);
}

async function saveAdmin() {
    const form = document.getElementById('admin-form');
    const formData = new FormData(form);
    const adminData = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/api/admin/admins', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ admin_id: parseInt(adminData.admin_id) }),
        });

        if (response.ok) {
            closeModal();
            loadAdmins();
        }
    } catch (error) {
        console.error('Error saving admin:', error);
    }
}

async function deleteAdmin(adminId) {
    if (!confirm(`Вы уверены, что хотите удалить администратора с ID ${adminId}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/admins/${adminId}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            loadAdmins();
        }
    } catch (error) {
        console.error('Error deleting admin:', error);
    }
}

// ==================== UTILITY FUNCTIONS ====================

function formatCurrency(amount) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function getStatusBadgeClass(status) {
    const classes = {
        'confirmed': 'badge-success',
        'pending': 'badge-warning',
        'completed': 'badge-info',
        'cancelled': 'badge-danger'
    };
    return classes[status] || 'badge-secondary';
}

function getStatusText(status) {
    const texts = {
        'confirmed': 'Подтверждена',
        'pending': 'Ожидание',
        'completed': 'Завершена',
        'cancelled': 'Отменена'
    };
    return texts[status] || status;
}

function getCategoryText(category) {
    const texts = {
        'tattoo': 'Татуировка',
        'consultation': 'Консультация',
        'coverup': 'Перекрытие'
    };
    return texts[category] || category;
}

function getIntentText(intent) {
    const texts = {
        'booking_inquiry': '📅 Запрос на запись',
        'price_question': '💰 Вопрос о цене',
        'portfolio_request': '🎨 Запрос портфолио',
        'cancellation': '❌ Отмена записи',
        'general_info': 'ℹ️ Общая информация'
    };
    return texts[intent] || intent;
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">❌</div>
            <p>${message}</p>
        </div>
    `;
}

// ==================== TRAINING TAB ====================

let allConversations = [];
let currentConversation = null;
let trainingFilters = {
    status: 'all',
    period: 'month',
    lang: 'all'
};

async function loadTrainingData() {
    try {
        // Load training conversations (mock data for now)
        const response = await fetch('/api/training/conversations');
        if (response.ok) {
            allConversations = await response.json();
        } else {
            // Use mock data
            allConversations = generateMockConversations();
        }

        updateTrainingStats();
        renderConversations(allConversations);
        setupTrainingFilters();
    } catch (error) {
        console.error('Error loading training data:', error);
        // Use mock data on error
        allConversations = generateMockConversations();
        updateTrainingStats();
        renderConversations(allConversations);
        setupTrainingFilters();
    }
}

function generateMockConversations() {
    const statuses = ['needs_review', 'reviewed', 'has_corrections'];
    const languages = ['ru', 'en', 'he'];
    const conversations = [];

    for (let i = 1; i <= 25; i++) {
        const daysAgo = Math.floor(Math.random() * 30);
        const date = new Date();
        date.setDate(date.getDate() - daysAgo);

        conversations.push({
            id: i,
            user_id: 100000 + i,
            user_name: `Клиент ${i}`,
            status: statuses[Math.floor(Math.random() * statuses.length)],
            language: languages[Math.floor(Math.random() * languages.length)],
            created_at: date.toISOString(),
            messages_count: Math.floor(Math.random() * 10) + 2,
            preview: 'Здравствуйте! Хочу записаться на татуировку...',
            has_corrections: Math.random() > 0.7,
            reviewed: Math.random() > 0.5
        });
    }

    return conversations.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

function updateTrainingStats() {
    const total = allConversations.length;
    const reviewed = allConversations.filter(c => c.reviewed).length;
    const corrections = allConversations.filter(c => c.has_corrections).length;
    const accuracy = total > 0 ? ((total - corrections) / total * 100).toFixed(1) : 100;

    document.getElementById('total-conversations-count').textContent = total;
    document.getElementById('reviewed-count').textContent = reviewed;
    document.getElementById('corrections-count').textContent = corrections;
    document.getElementById('accuracy-rate').textContent = accuracy + '%';
}

function setupTrainingFilters() {
    document.getElementById('training-filter-status').addEventListener('change', (e) => {
        trainingFilters.status = e.target.value;
        filterAndRenderConversations();
    });

    document.getElementById('training-filter-period').addEventListener('change', (e) => {
        trainingFilters.period = e.target.value;
        filterAndRenderConversations();
    });

    document.getElementById('training-filter-lang').addEventListener('change', (e) => {
        trainingFilters.lang = e.target.value;
        filterAndRenderConversations();
    });
}

function filterAndRenderConversations() {
    let filtered = [...allConversations];

    // Filter by status
    if (trainingFilters.status !== 'all') {
        if (trainingFilters.status === 'needs_review') {
            filtered = filtered.filter(c => !c.reviewed);
        } else if (trainingFilters.status === 'reviewed') {
            filtered = filtered.filter(c => c.reviewed);
        } else if (trainingFilters.status === 'has_corrections') {
            filtered = filtered.filter(c => c.has_corrections);
        }
    }

    // Filter by period
    if (trainingFilters.period !== 'all') {
        const now = new Date();
        const cutoff = new Date();

        if (trainingFilters.period === 'today') {
            cutoff.setHours(0, 0, 0, 0);
        } else if (trainingFilters.period === 'week') {
            cutoff.setDate(cutoff.getDate() - 7);
        } else if (trainingFilters.period === 'month') {
            cutoff.setMonth(cutoff.getMonth() - 1);
        }

        filtered = filtered.filter(c => new Date(c.created_at) >= cutoff);
    }

    // Filter by language
    if (trainingFilters.lang !== 'all') {
        filtered = filtered.filter(c => c.language === trainingFilters.lang);
    }

    renderConversations(filtered);
}

function renderConversations(conversations) {
    const container = document.getElementById('training-conversations-container');

    if (conversations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <p>Нет диалогов для отображения</p>
            </div>
        `;
        return;
    }

    container.innerHTML = conversations.map(conv => `
        <div class="conversation-item" onclick="openConversationModal(${conv.id})">
            <div class="conversation-header">
                <div>
                    <strong>Диалог #${conv.id}</strong>
                    <span class="text-secondary"> • ${conv.user_name}</span>
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    ${conv.reviewed ? '<span class="badge badge-success">Проверено</span>' : '<span class="badge badge-warning">Требует проверки</span>'}
                    ${conv.has_corrections ? '<span class="badge badge-info">Есть исправления</span>' : ''}
                </div>
            </div>
            <div class="conversation-meta">
                <span>📅 ${formatDate(conv.created_at)}</span>
                <span>💬 ${conv.messages_count} сообщений</span>
                <span>🌍 ${getLanguageLabel(conv.language)}</span>
            </div>
            <div class="conversation-preview">
                ${conv.preview}
            </div>
        </div>
    `).join('');
}

function getLanguageLabel(lang) {
    const labels = {
        'ru': '🇷🇺 Русский',
        'en': '🇬🇧 English',
        'he': '🇮🇱 עברית'
    };
    return labels[lang] || lang;
}

async function openConversationModal(conversationId) {
    currentConversation = allConversations.find(c => c.id === conversationId);
    if (!currentConversation) return;

    document.getElementById('modal-conversation-id').textContent = conversationId;

    // Load messages (mock for now)
    const messages = generateMockMessages(conversationId);

    const messagesContainer = document.getElementById('modal-conversation-messages');
    messagesContainer.innerHTML = messages.map(msg => `
        <div class="message-bubble ${msg.role}">
            <div class="message-header">
                <span>${msg.role === 'user' ? '👤 Клиент' : '🤖 INKA'}</span>
                <span>${formatTime(msg.timestamp)}</span>
            </div>
            <div class="message-text">${msg.text}</div>
            ${msg.role === 'bot' ? `
                <div class="correction-panel" style="display: ${msg.has_correction ? 'block' : 'none'};">
                    <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500;">
                        📝 Улучшенный ответ:
                    </label>
                    <textarea class="correction-input" placeholder="Введите исправленный ответ...">${msg.correction || ''}</textarea>
                    <button class="btn btn-sm btn-primary" style="margin-top: 0.5rem;" onclick="saveCorrection(${msg.id})">
                        Сохранить исправление
                    </button>
                </div>
                <button class="btn btn-sm btn-outline" style="margin-top: 0.5rem;" onclick="toggleCorrectionPanel(this)">
                    ${msg.has_correction ? 'Скрыть исправление' : '✏️ Добавить исправление'}
                </button>
            ` : ''}
        </div>
    `).join('');

    document.getElementById('conversation-detail-modal').style.display = 'flex';
}

function generateMockMessages(convId) {
    return [
        {
            id: convId * 100 + 1,
            role: 'user',
            text: 'Здравствуйте! Хочу записаться на татуировку',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            has_correction: false
        },
        {
            id: convId * 100 + 2,
            role: 'bot',
            text: 'Здравствуйте! Конечно, помогу вам записаться. Какой стиль татуировки вас интересует?',
            timestamp: new Date(Date.now() - 3500000).toISOString(),
            has_correction: false,
            correction: null
        },
        {
            id: convId * 100 + 3,
            role: 'user',
            text: 'Мне нужна маленькая татуировка в стиле минимализм',
            timestamp: new Date(Date.now() - 3400000).toISOString(),
            has_correction: false
        },
        {
            id: convId * 100 + 4,
            role: 'bot',
            text: 'Отлично! У нас есть отличный мастер по минимализму - Екатерина Смирнова. Когда вам было бы удобно прийти?',
            timestamp: new Date(Date.now() - 3300000).toISOString(),
            has_correction: Math.random() > 0.5,
            correction: 'Отличный выбор! Для минимализма рекомендую мастера Екатерину Смирнову (рейтинг 4.9). Маленькая татуировка займёт около 60 минут и стоит 5000₽. Когда вам было бы удобно прийти?'
        }
    ];
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

function closeConversationModal() {
    document.getElementById('conversation-detail-modal').style.display = 'none';
    currentConversation = null;
}

function toggleCorrectionPanel(button) {
    const panel = button.previousElementSibling;
    if (panel.style.display === 'none' || !panel.style.display) {
        panel.style.display = 'block';
        button.textContent = 'Скрыть исправление';
    } else {
        panel.style.display = 'none';
        button.textContent = '✏️ Добавить исправление';
    }
}

function saveCorrection(messageId) {
    console.log('Saving correction for message', messageId);
    alert('✅ Исправление сохранено! INKA будет учитывать это в будущих ответах.');
    // TODO: Send to API
}

function markAsReviewed() {
    if (!currentConversation) return;

    currentConversation.reviewed = true;
    allConversations = allConversations.map(c =>
        c.id === currentConversation.id ? currentConversation : c
    );

    updateTrainingStats();
    filterAndRenderConversations();
    closeConversationModal();

    alert('✅ Диалог отмечен как проверенный!');
    // TODO: Send to API
}

// ==================== LIVE CHAT WITH OPENAI ====================

let chatHistory = [];

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addChatMessage('user', message);
    input.value = '';

    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        // Get chat settings
        const model = document.getElementById('chat-model').value;
        const temperature = parseFloat(document.getElementById('chat-temperature').value);
        const language = document.getElementById('chat-language').value;

        // Send to API
        const response = await fetch('/api/chat/inka', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                model: model,
                temperature: temperature,
                language: language,
                chat_history: chatHistory
            })
        });

        removeTypingIndicator(typingId);

        if (response.ok) {
            const data = await response.json();
            addChatMessage('bot', data.response);

            // Update chat history
            chatHistory.push({
                role: 'user',
                content: message
            });
            chatHistory.push({
                role: 'assistant',
                content: data.response
            });

            // Update status if needed
            if (data.model_used) {
                updateChatStatus(`Используется ${data.model_used}`, 'success');
            }
        } else {
            const error = await response.json();
            addChatMessage('error', `Ошибка: ${error.detail || 'Не удалось получить ответ от INKA'}`);
            updateChatStatus('Ошибка подключения', 'danger');
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        console.error('Chat error:', error);
        addChatMessage('error', 'Ошибка соединения с сервером. Проверьте подключение.');
        updateChatStatus('Офлайн', 'danger');
    }
}

function addChatMessage(role, text) {
    const container = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const timestamp = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

    let style = '';
    let icon = '';

    if (role === 'user') {
        style = `
            padding: var(--spacing-md);
            background: rgba(92, 124, 250, 0.15);
            border-radius: var(--border-radius-md);
            border-left: 4px solid var(--accent-primary);
            margin-left: auto;
            max-width: 80%;
        `;
        icon = '👤';
    } else if (role === 'bot') {
        style = `
            padding: var(--spacing-md);
            background: var(--bg-secondary);
            border-radius: var(--border-radius-md);
            border-left: 4px solid var(--success);
            margin-right: auto;
            max-width: 80%;
        `;
        icon = '🤖';
    } else if (role === 'error') {
        style = `
            padding: var(--spacing-md);
            background: rgba(250, 82, 82, 0.1);
            border-radius: var(--border-radius-md);
            border-left: 4px solid var(--danger);
            margin-right: auto;
            max-width: 80%;
        `;
        icon = '⚠️';
    }

    messageDiv.style.cssText = style;
    messageDiv.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-xs);">
            <strong>${icon} ${role === 'user' ? 'Вы' : role === 'bot' ? 'INKA' : 'Ошибка'}</strong>
            <span style="font-size: 0.75rem; color: var(--text-tertiary);">${timestamp}</span>
        </div>
        <div style="color: var(--text-primary); white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(text)}</div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function addTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    const id = 'typing-' + Date.now();
    typingDiv.id = id;

    typingDiv.style.cssText = `
        padding: var(--spacing-md);
        background: var(--bg-secondary);
        border-radius: var(--border-radius-md);
        border-left: 4px solid var(--success);
        margin-right: auto;
        max-width: 80%;
    `;

    typingDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: var(--spacing-sm);">
            <strong>🤖 INKA</strong>
            <div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>
            <span style="color: var(--text-secondary); font-size: 0.875rem;">печатает...</span>
        </div>
    `;

    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;

    return id;
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

function clearChat() {
    if (!confirm('Вы уверены, что хотите очистить историю чата?')) return;

    const container = document.getElementById('chat-messages');
    container.innerHTML = `
        <div class="chat-message system" style="
            padding: var(--spacing-md);
            background: rgba(92, 124, 250, 0.1);
            border-radius: var(--border-radius-md);
            border-left: 4px solid var(--accent-primary);
            font-size: 0.875rem;
            color: var(--text-secondary);
        ">
            <strong>Система:</strong> Чат очищен. Начните новый диалог для тестирования INKA.
        </div>
    `;

    chatHistory = [];
    updateChatStatus('Онлайн', 'success');
}

function updateChatStatus(text, type) {
    const statusBadge = document.getElementById('chat-status');
    if (statusBadge) {
        statusBadge.textContent = text;
        statusBadge.className = `badge badge-${type}`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== MODAL FORM HANDLING ====================

function openModal(title, saveCallback) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    const saveBtn = document.getElementById('modal-save-btn');
    saveBtn.onclick = saveCallback;

    document.getElementById('form-modal').style.display = 'flex';
}

function setModalBody(html) {
    document.getElementById('modal-body').innerHTML = html;
}

function closeModal() {
    document.getElementById('form-modal').style.display = 'none';
}


// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadDashboardStats();
    initAddButtons();
});

function initAddButtons() {
    document.querySelector('#clients-tab .btn-primary').addEventListener('click', () => {
        openModal('Добавить клиента', saveClient);
        setModalBody(getClientFormHtml());
    });
    document.querySelector('#masters-tab .btn-primary').addEventListener('click', () => {
        openModal('Добавить мастера', saveMaster);
        setModalBody(getMasterFormHtml());
    });
    document.querySelector('#services-tab .btn-primary').addEventListener('click', () => {
        openModal('Добавить услугу', saveService);
        setModalBody(getServiceFormHtml());
    });
    document.querySelector('#bookings-tab .btn-primary').addEventListener('click', async () => {
        openModal('Создать запись', saveBooking);
        await Promise.all([fetchClients(), fetchMasters(), fetchServices()]);
        setModalBody(getBookingFormHtml());
    });
    document.querySelector('#admins-tab .btn-primary').addEventListener('click', () => {
        openAddAdminModal();
    });
}

function getClientFormHtml(client = {}) {
    return `
        <form id="client-form">
            <input type="hidden" name="id" value="${client.id || ''}">
            <div class="form-group">
                <label for="client-name">Имя</label>
                <input type="text" id="client-name" name="name" class="form-input" value="${client.name || ''}" required>
            </div>
            <div class="form-group">
                <label for="client-email">Email</label>
                <input type="email" id="client-email" name="email" class="form-input" value="${client.email || ''}" required>
            </div>
            <div class="form-group">
                <label for="client-phone">Телефон</label>
                <input type="tel" id="client-phone" name="phone" class="form-input" value="${client.phone || ''}" required>
            </div>
        </form>
    `;
}

function getMasterFormHtml(master = {}) {
    return `
        <form id="master-form">
            <input type="hidden" name="id" value="${master.id || ''}">
            <div class="form-group">
                <label for="master-name">Имя</label>
                <input type="text" id="master-name" name="name" class="form-input" value="${master.name || ''}" required>
            </div>
            <div class="form-group">
                <label for="master-specialization">Специализация</label>
                <input type="text" id="master-specialization" name="specialization" class="form-input" value="${master.specialization || ''}" required>
            </div>
            <div class="form-group">
                <label for="master-email">Email</label>
                <input type="email" id="master-email" name="email" class="form-input" value="${master.email || ''}" required>
            </div>
            <div class="form-group">
                <label for="master-phone">Телефон</label>
                <input type="tel" id="master-phone" name="phone" class="form-input" value="${master.phone || ''}" required>
            </div>
        </form>
    `;
}

function getServiceFormHtml(service = {}) {
    return `
        <form id="service-form">
            <input type="hidden" name="id" value="${service.id || ''}">
            <div class="form-group">
                <label for="service-name">Название</label>
                <input type="text" id="service-name" name="name" class="form-input" value="${service.name || ''}" required>
            </div>
            <div class="form-group">
                <label for="service-description">Описание</label>
                <input type="text" id="service-description" name="description" class="form-input" value="${service.description || ''}" required>
            </div>
            <div class="form-group">
                <label for="service-duration">Длительность (мин)</label>
                <input type="number" id="service-duration" name="duration_minutes" class="form-input" value="${service.duration_minutes || ''}" required>
            </div>
            <div class="form-group">
                <label for="service-price">Цена</label>
                <input type="number" id="service-price" name="price" class="form-input" value="${service.price || ''}" required>
            </div>
            <div class="form-group">
                <label for="service-category">Категория</label>
                <input type="text" id="service-category" name="category" class="form-input" value="${service.category || ''}" required>
            </div>
        </form>
    `;
}

function getBookingFormHtml(booking = {}) {
    return `
        <form id="booking-form">
            <input type="hidden" name="id" value="${booking.id || ''}">
            <div class="form-group">
                <label for="booking-client">Клиент</label>
                <select id="booking-client" name="client_id" class="form-input" required>
                    ${allClients.map(client => `<option value="${client.id}" ${booking.client_id == client.id ? 'selected' : ''}>${client.name}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="booking-master">Мастер</label>
                <select id="booking-master" name="master_id" class="form-input" required>
                    ${allMasters.map(master => `<option value="${master.id}" ${booking.master_id == master.id ? 'selected' : ''}>${master.name}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="booking-service">Услуга</label>
                <select id="booking-service" name="service_id" class="form-input" required>
                    ${allServices.map(service => `<option value="${service.id}" ${booking.service_id == service.id ? 'selected' : ''}>${service.name}</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label for="booking-date">Дата</label>
                <input type="date" id="booking-date" name="booking_date" class="form-input" value="${booking.booking_date || ''}" required>
            </div>
            <div class="form-group">
                <label for="booking-start-time">Время начала</label>
                <input type="time" id="booking-start-time" name="start_time" class="form-input" value="${booking.start_time || ''}" required>
            </div>
            <div class="form-group">
                <label for="booking-end-time">Время окончания</label>
                <input type="time" id="booking-end-time" name="end_time" class="form-input" value="${booking.end_time || ''}" required>
            </div>
            <div class="form-group">
                <label for="booking-status">Статус</label>
                <select id="booking-status" name="status" class="form-input" required>
                    <option value="pending" ${booking.status == 'pending' ? 'selected' : ''}>Ожидание</option>
                    <option value="confirmed" ${booking.status == 'confirmed' ? 'selected' : ''}>Подтверждена</option>
                    <option value="completed" ${booking.status == 'completed' ? 'selected' : ''}>Завершена</option>
                    <option value="cancelled" ${booking.status == 'cancelled' ? 'selected' : ''}>Отменена</option>
                </select>
            </div>
        </form>
    `;
}

async function saveClient() {
    const form = document.getElementById('client-form');
    const formData = new FormData(form);
    const clientData = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/api/clients', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(clientData),
        });

        if (response.ok) {
            closeModal();
            loadClients();
            // TODO: Show success message
        } else {
            // TODO: Show error message
        }
    } catch (error) {
        console.error('Error saving client:', error);
        // TODO: Show error message
    }
}

async function saveMaster() {
    const form = document.getElementById('master-form');
    const formData = new FormData(form);
    const masterData = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/api/masters', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(masterData),
        });

        if (response.ok) {
            closeModal();
            loadMasters();
        }
    } catch (error) {
        console.error('Error saving master:', error);
    }
}

async function saveService() {
    const form = document.getElementById('service-form');
    const formData = new FormData(form);
    const serviceData = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/api/services', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(serviceData),
        });

        if (response.ok) {
            closeModal();
            loadServices();
        }
    } catch (error) {
        console.error('Error saving service:', error);
    }
}

async function saveBooking() {
    const form = document.getElementById('booking-form');
    const formData = new FormData(form);
    const bookingData = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/api/bookings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bookingData),
        });

        if (response.ok) {
            closeModal();
            loadBookings();
        }
    } catch (error) {
        console.error('Error saving booking:', error);
    }
}
