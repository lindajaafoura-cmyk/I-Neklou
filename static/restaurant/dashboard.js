let currentRestaurant = null;
let dashboardData = {};

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function apiCall(url, method, body) {
    let options = {
        method: method || 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
    };
    if (body) options.body = JSON.stringify(body);
    return fetch(url, options).then(r => r.json());
}

async function loadDashboardData() {
    try {
        let data = await apiCall('/api/dashboard-data/');
        if (data.error) {
            document.getElementById('restaurantName').textContent = 'Aucun restaurant';
            return;
        }
        dashboardData = data;
        currentRestaurant = data.restaurant;
        currentRestaurant.menu = data.menu || [];

        document.getElementById('restaurantName').textContent = currentRestaurant.name;
        document.getElementById('restaurantLocation').innerHTML = `<i class="fas fa-map-pin"></i> ${currentRestaurant.location || 'Non défini'}`;
        document.getElementById('restaurantPhone').innerHTML = `<i class="fas fa-phone"></i> ${currentRestaurant.phone || 'Non défini'}`;

        document.getElementById('avgRating').textContent = data.stats.avg_rating || '0';
        document.getElementById('occupancyRate').textContent = (data.stats.occupancy_rate || '0') + '%';
        document.getElementById('loyaltyCount').textContent = data.stats.loyalty_count || '0';

        displayAllReviews(data.reviews || []);
        displayReservations(data.reservations || []);
        displayMenu();
        displayGallery(data.gallery || []);
        displayHours();
        displayPromotions(data.promotions || []);

        let settingsName = document.getElementById('settingsName');
        if (settingsName) settingsName.value = currentRestaurant.name || '';
        let settingsDesc = document.getElementById('settingsDescription');
        if (settingsDesc) settingsDesc.value = currentRestaurant.description || '';
        let settingsPhone = document.getElementById('settingsPhone');
        if (settingsPhone) settingsPhone.value = currentRestaurant.phone || '';
        let settingsEmail = document.getElementById('settingsEmail');
        if (settingsEmail) settingsEmail.value = currentRestaurant.email || '';
        let settingsAddress = document.getElementById('settingsAddress');
        if (settingsAddress) settingsAddress.value = currentRestaurant.address || '';

        notifications = data.notifications || [];
        afficherNotifications();

        setTimeout(() => initCharts(), 100);
    } catch (e) {
        console.error('Erreur chargement:', e);
        document.getElementById('restaurantName').textContent = 'Erreur de chargement';
    }
}

function toggleNotifications() {
    let panel = document.getElementById('notificationsPanel');
    panel.classList.toggle('show');
    if (panel.classList.contains('show')) {
        afficherNotifications();
    }
}

let notifications = [];

function afficherNotifications() {
    let container = document.getElementById('notificationsList');
    let nonLues = notifications.filter(n => !n.lue).length;
    document.getElementById('notificationCount').textContent = nonLues;

    if (notifications.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:30px;">Aucune notification</div>';
        return;
    }

    notifications.sort((a, b) => new Date(b.time) - new Date(a.time));

    container.innerHTML = notifications.map(notif => {
        let icone = 'fa-bell';
        let couleur = 'system';

        if (notif.type === 'reservation') { icone = 'fa-calendar-check'; couleur = 'reservation'; }
        if (notif.type === 'review') { icone = 'fa-star'; couleur = 'review'; }
        if (notif.type === 'promo') { icone = 'fa-tags'; couleur = 'promo'; }
        if (notif.type === 'favorite') { icone = 'fa-heart'; couleur = 'review'; }

        let d = new Date(notif.time);
        let maintenant = new Date();
        let diffMinutes = Math.floor((maintenant - d) / 60000);
        let temps;

        if (diffMinutes < 1) temps = "À l'instant";
        else if (diffMinutes < 60) temps = `Il y a ${diffMinutes} min`;
        else if (diffMinutes < 1440) temps = `Il y a ${Math.floor(diffMinutes / 60)} h`;
        else temps = `Il y a ${Math.floor(diffMinutes / 1440)} j`;

        return `
            <div class="notification-item ${!notif.lue ? 'unread' : ''}" onclick="marquerCommeLu('${notif.id}')">
                <div class="notification-icon ${couleur}">
                    <i class="fas ${icone}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notif.titre}</div>
                    <div class="notification-message">${notif.message}</div>
                    <div class="notification-time">${temps}</div>
                </div>
            </div>
        `;
    }).join('');
}

function marquerCommeLu(id) {
    let notif = notifications.find(n => n.id === id);
    if (notif) {
        notif.lue = true;
        afficherNotifications();
        showNotification('Notification marquée comme lue', 'success');
    }
}

function toutMarquerLu() {
    notifications.forEach(n => n.lue = true);
    afficherNotifications();
    showNotification('Toutes les notifications sont lues', 'success');
}

function deconnexion() {
    const logoutUrl = document.body.dataset.logoutUrl || '/deconnexion/';
    window.location.href = logoutUrl;
}

function displayAllReviews(reviews) {
    let container = document.getElementById('allReviews');
    if (!container) return;

    if (!reviews || reviews.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#999; padding:30px;">Aucun avis pour le moment</p>';
        return;
    }

    container.innerHTML = reviews.map(review => `
        <div class="review-card">
            <div class="review-header">
                <div class="review-user">
                    <h4>${review.user}</h4>
                </div>
                <span class="review-rating">${'★'.repeat(review.rating)}${'☆'.repeat(5 - review.rating)}</span>
            </div>
            <p class="review-text">"${review.comment}"</p>
            ${review.reply ? `
                <div class="review-reply-admin">
                    <div class="reply-header">
                        <i class="fas fa-reply"></i> Votre réponse
                    </div>
                    <p>${review.reply}</p>
                </div>
            ` : ''}
            <div class="review-footer">
                <span>${formatDate(review.date)}</span>
                <div class="review-actions">
                    <button class="btn-reply" onclick="showReplyModal('${review.id}')">${review.reply ? 'Modifier' : 'Répondre'}</button>
                    <button class="btn-report" onclick="reportReview('${review.id}')">Signaler</button>
                </div>
            </div>
        </div>
    `).join('');
}

function displayReservations(reservations) {
    let container = document.getElementById('reservationsList');
    if (!container) return;

    let data = reservations || dashboardData.reservations || [];

    if (data.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#999; padding:30px;">Aucune réservation</p>';
        return;
    }

    container.innerHTML = data.map(res => `
        <div class="reservation-item ${res.status === 'pending' ? 'pending' : ''} ${res.status === 'cancelled' ? 'cancelled' : ''}" data-id="${res.id}">
            <div class="reservation-info">
                <h4>${res.name}</h4>
                <div class="reservation-details">
                    <span><i class="fas fa-users"></i> ${res.persons} pers.</span>
                    <span><i class="fas fa-clock"></i> ${res.time}</span>
                    <span><i class="fas fa-calendar"></i> ${formatDisplayDate(res.date)}</span>
                </div>
            </div>
            <div class="reservation-actions">
                <span class="reservation-status ${res.status}">${getStatusText(res.status)}</span>
                ${res.status === 'pending' ? `
                    <button class="btn-confirm" onclick="confirmReservation('${res.id}')"><i class="fas fa-check"></i></button>
                    <button class="btn-reject" onclick="rejectReservation('${res.id}')"><i class="fas fa-times"></i></button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function displayMenu() {
    if (!currentRestaurant || !currentRestaurant.menu) return;
    let categories = ['Tous', ...new Set(currentRestaurant.menu.map(item => item.category))];
    let categoriesContainer = document.getElementById('menuCategories');
    if (!categoriesContainer) return;

    categoriesContainer.innerHTML = categories.map((cat, index) => `
        <button class="category-tab ${index === 0 ? 'active' : ''}" onclick="filterMenu('${cat}')">${cat}</button>
    `).join('');

    displayMenuItems('Tous');
}

function displayMenuItems(category) {
    let container = document.getElementById('menuItems');
    if (!container || !currentRestaurant || !currentRestaurant.menu) return;

    let filtered = category === 'Tous'
        ? currentRestaurant.menu
        : currentRestaurant.menu.filter(item => item.category === category);

    if (filtered.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#999; padding:30px;">Aucun plat dans cette catégorie</p>';
        return;
    }

    container.innerHTML = filtered.map(item => `
        <div class="menu-item-card" data-id="${item.id}">
            <div class="menu-item-image">
                <img src="${item.image}" alt="${item.name}">
            </div>
            <div class="menu-item-info">
                <h4>${item.name}</h4>
                <p>${item.category}</p>
                <div class="menu-item-footer">
                    <span class="menu-item-price">${item.price} DT</span>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <span class="stock-badge ${!item.stock ? 'out' : ''}">${item.stock ? '✓' : '✗'}</span>
                        <div class="menu-item-actions">
                            <button class="edit-btn" onclick="editMenuItem('${item.id}')"><i class="fas fa-edit"></i></button>
                            <button class="delete-btn" onclick="deleteMenuItem('${item.id}')"><i class="fas fa-trash"></i></button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function displayGallery(gallery) {
    let container = document.getElementById('gallery');
    if (!container) return;

    let data = gallery || dashboardData.gallery || [];

    if (data.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#999; padding:30px;">Aucune photo</p>';
        return;
    }

    container.innerHTML = data.map(photo => `
        <div class="gallery-item" data-id="${photo.id}">
            <img src="${photo.url}" alt="${photo.name || 'Photo'}">
            <div class="gallery-overlay">
                <button onclick="viewPhoto('${photo.id}', '${photo.url}', '${photo.name || ''}')"><i class="fas fa-eye"></i></button>
                <button onclick="deletePhoto('${photo.id}')"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    `).join('');
}

function displayHours() {
    let container = document.getElementById('hoursGrid');
    if (!container || !currentRestaurant) return;

    let hours = currentRestaurant.hours || {};

    container.innerHTML = `
        <div class="hour-row">
            <span class="day">Lundi - Vendredi</span>
            <span class="hours">${hours.monday_friday || 'Non défini'}</span>
        </div>
        <div class="hour-row">
            <span class="day">Samedi</span>
            <span class="hours">${hours.saturday || 'Non défini'}</span>
            <span class="special-badge">Nocturne</span>
        </div>
        <div class="hour-row">
            <span class="day">Dimanche</span>
            <span class="hours">${hours.sunday || 'Non défini'}</span>
            <span class="special-badge">Fermé soir</span>
        </div>
    `;
}

function displayPromotions(promotions) {
    let container = document.getElementById('promotionsList');
    if (!container) return;

    let data = promotions || dashboardData.promotions || [];

    if (data.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#999; padding:30px;">Aucune promotion active</p>';
        return;
    }

    container.innerHTML = data.map(promo => `
        <div class="promo-card" data-id="${promo.id}">
            <div class="promo-info">
                <h4>${promo.title}</h4>
                <p>${promo.description}</p>
                <span class="promo-discount">${promo.discount}</span>
            </div>
            <div>
                <span class="promo-status ${promo.status === 'ending' ? 'ending' : ''}">
                    ${promo.status === 'active' ? 'Actif' : 'Se termine bientôt'}
                </span>
                <div class="promo-actions">
                    <button class="btn-delete-promo" onclick="deletePromotion('${promo.id}')"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        </div>
    `).join('');
}

function displayLoyaltyData() {
    let loyaltyMembers = document.getElementById('loyaltyMembers');
    let activeCoupons = document.getElementById('activeCoupons');
    let totalPoints = document.getElementById('totalPoints');

    if (loyaltyMembers) loyaltyMembers.textContent = '0';
    if (activeCoupons) activeCoupons.textContent = '0';
    if (totalPoints) totalPoints.textContent = '0';
}

function initCharts() {
    const charts = dashboardData.stats?.charts;
    if (!charts) return;

    // 1. PERFORMANCE & GROWTH (Main Chart) - REAL DATA
    const perfCtx = document.getElementById('performanceChart')?.getContext('2d');
    if (perfCtx) {
        const gradient = perfCtx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(45, 90, 59, 0.3)');
        gradient.addColorStop(1, 'rgba(45, 90, 59, 0)');

        new Chart(perfCtx, {
            type: 'line',
            data: {
                labels: charts.performance?.labels || [],
                datasets: [
                    {
                        label: 'Réservations',
                        data: charts.performance?.data || [],
                        borderColor: '#2D5A3B',
                        backgroundColor: gradient,
                        borderWidth: 4,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 6,
                        pointBackgroundColor: '#fff',
                        pointBorderColor: '#2D5A3B',
                        pointBorderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#F5F0E6' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 2. PEAK HOURS (Bar Chart) - REAL DATA
    const peakCtx = document.getElementById('peakHoursChart')?.getContext('2d');
    if (peakCtx) {
        new Chart(peakCtx, {
            type: 'bar',
            data: {
                labels: charts.hours?.labels || [],
                datasets: [{
                    label: 'Affluence',
                    data: charts.hours?.data || [],
                    backgroundColor: '#2D5A3B',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { display: false },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 3. MIX CLIENTS
    const mixCtx = document.getElementById('customerMixChart')?.getContext('2d');
    if (mixCtx) {
        new Chart(mixCtx, {
            type: 'doughnut',
            data: {
                labels: ['Réguliers', 'Nouveaux'],
                datasets: [{
                    data: [dashboardData.stats.loyalty_count, dashboardData.stats.monthly_reservations - dashboardData.stats.loyalty_count],
                    backgroundColor: ['#2D5A3B', '#E8E0D0'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
}

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });

    let targetSection = document.getElementById(sectionId + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
    }

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    let activeNav = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
    if (activeNav) {
        activeNav.classList.add('active');
    }

    let titres = {
        'dashboard': 'Dashboard',
        'avis': 'Avis clients',
        'reservations': 'Réservations',
        'menu': 'Menu & Horaires',
        'parametres': 'Paramètres'
    };

    let icones = {
        'dashboard': 'home',
        'avis': 'star',
        'reservations': 'calendar-check',
        'menu': 'utensils',
        'parametres': 'cog'
    };

    document.getElementById('pageTitle').innerHTML =
        `<i class="fas fa-${icones[sectionId]}"></i> ${titres[sectionId]}`;
}

function showAddReservationModal() {
    let modal = document.getElementById('modal');
    let modalContent = document.getElementById('modalContent');

    modalContent.innerHTML = `
        <h3>Nouvelle réservation</h3>
        <div style="display: grid; gap: 15px;">
            <input type="text" id="resName" placeholder="Nom du client" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <input type="date" id="resDate" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;" value="${new Date().toISOString().split('T')[0]}">
            <input type="time" id="resTime" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;" value="20:00">
            <input type="number" id="resPersons" placeholder="Nombre de personnes" min="1" max="20" value="2" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
        </div>
        <div class="modal-actions">
            <button class="btn-add" onclick="addReservation()">Créer</button>
            <button class="btn-edit" onclick="closeModal()">Annuler</button>
        </div>
    `;

    modal.classList.add('active');
}

async function addReservation() {
    let name = document.getElementById('resName')?.value;
    let date = document.getElementById('resDate')?.value;
    let time = document.getElementById('resTime')?.value;
    let persons = parseInt(document.getElementById('resPersons')?.value) || 2;

    if (!name || !date || !time) {
        showNotification('Veuillez remplir tous les champs', 'error');
        return;
    }

    try {
        await apiCall('/api/reservation-action/', 'POST', {
            action: 'create',
            name: name,
            date: date,
            time: time,
            persons: persons
        });
        showNotification('Réservation créée avec succès', 'success');
        closeModal();
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur lors de la création', 'error');
    }
}

async function confirmReservation(id) {
    try {
        await apiCall('/api/reservation-action/', 'POST', { id: id, action: 'confirm' });
        showNotification('Réservation confirmée', 'success');
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

async function rejectReservation(id) {
    try {
        await apiCall('/api/reservation-action/', 'POST', { id: id, action: 'cancel' });
        showNotification('Réservation annulée', 'info');
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

function filterMenu(category) {
    document.querySelectorAll('.category-tab').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent === category) {
            btn.classList.add('active');
        }
    });
    displayMenuItems(category);
}

function showAddMenuItemModal() {
    let modal = document.getElementById('modal');
    let modalContent = document.getElementById('modalContent');

    modalContent.innerHTML = `
        <h3>Ajouter un plat</h3>
        <div style="display: grid; gap: 15px;">
            <input type="text" id="menuName" placeholder="Nom du plat" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <input type="number" id="menuPrice" placeholder="Prix (ex: 25)" step="0.5" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <input type="text" id="menuImage" placeholder="URL de l'image" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <select id="menuCategory" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
                <option value="Entrées">Entrées</option>
                <option value="Plats">Plats</option>
                <option value="Desserts">Desserts</option>
                <option value="Boissons">Boissons</option>
                <option value="Spécialités">Spécialités</option>
            </select>
            <label style="display: flex; align-items: center; gap: 10px;">
                <input type="checkbox" id="menuStock" checked> En stock
            </label>
        </div>
        <div class="modal-actions">
            <button class="btn-add" onclick="addMenuItem()">Ajouter</button>
            <button class="btn-edit" onclick="closeModal()">Annuler</button>
        </div>
    `;

    modal.classList.add('active');
}

async function addMenuItem() {
    let name = document.getElementById('menuName')?.value;
    let price = parseFloat(document.getElementById('menuPrice')?.value);
    let category = document.getElementById('menuCategory')?.value;
    let image = document.getElementById('menuImage')?.value || '';
    let stock = document.getElementById('menuStock')?.checked;

    if (!name || !price) {
        showNotification('Veuillez remplir le nom et le prix', 'error');
        return;
    }

    try {
        await apiCall('/api/menu-item/', 'POST', { name, price, category, image, stock });
        showNotification('Plat ajouté avec succès', 'success');
        closeModal();
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur lors de l\'ajout', 'error');
    }
}

function editMenuItem(itemId) {
    let item = currentRestaurant.menu.find(i => i.id === itemId);
    if (!item) return;

    let modal = document.getElementById('modal');
    let modalContent = document.getElementById('modalContent');

    let priceNum = parseFloat(item.price) || 0;

    modalContent.innerHTML = `
        <h3>Modifier le plat</h3>
        <div style="display: grid; gap: 15px;">
            <input type="text" id="editMenuName" value="${item.name}" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <input type="number" id="editMenuPrice" value="${priceNum}" step="0.5" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <input type="text" id="editMenuImage" value="${item.image}" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <select id="editMenuCategory" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
                <option value="Entrées" ${item.category === 'Entrées' ? 'selected' : ''}>Entrées</option>
                <option value="Plats" ${item.category === 'Plats' ? 'selected' : ''}>Plats</option>
                <option value="Desserts" ${item.category === 'Desserts' ? 'selected' : ''}>Desserts</option>
                <option value="Boissons" ${item.category === 'Boissons' ? 'selected' : ''}>Boissons</option>
                <option value="Spécialités" ${item.category === 'Spécialités' ? 'selected' : ''}>Spécialités</option>
            </select>
            <label style="display: flex; align-items: center; gap: 10px;">
                <input type="checkbox" id="editMenuStock" ${item.stock ? 'checked' : ''}> En stock
            </label>
        </div>
        <div class="modal-actions">
            <button class="btn-add" onclick="updateMenuItem('${itemId}')">Mettre à jour</button>
            <button class="btn-edit" onclick="closeModal()">Annuler</button>
        </div>
    `;

    modal.classList.add('active');
}

async function updateMenuItem(itemId) {
    let name = document.getElementById('editMenuName')?.value;
    let price = parseFloat(document.getElementById('editMenuPrice')?.value);
    let category = document.getElementById('editMenuCategory')?.value;
    let image = document.getElementById('editMenuImage')?.value;
    let stock = document.getElementById('editMenuStock')?.checked;

    try {
        await apiCall('/api/menu-item/', 'PUT', { id: itemId, name, price, category, image, stock });
        showNotification('Plat mis à jour', 'success');
        closeModal();
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

async function deleteMenuItem(itemId) {
    if (!confirm('Voulez-vous vraiment supprimer ce plat ?')) return;

    try {
        await apiCall('/api/menu-item/', 'DELETE', { id: itemId });
        showNotification('Plat supprimé', 'success');
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

function uploadPhotos() {
    let modal = document.getElementById('modal');
    let modalContent = document.getElementById('modalContent');

    modalContent.innerHTML = `
        <h3>Ajouter une photo</h3>
        <div style="display: grid; gap: 15px;">
            <input type="text" id="photoName" placeholder="Légende" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <input type="text" id="photoUrl" placeholder="URL de l'image" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
        </div>
        <div class="modal-actions">
            <button class="btn-add" onclick="addPhoto()">Ajouter</button>
            <button class="btn-edit" onclick="closeModal()">Annuler</button>
        </div>
    `;

    modal.classList.add('active');
}

async function addPhoto() {
    let name = document.getElementById('photoName')?.value;
    let url = document.getElementById('photoUrl')?.value;

    if (!url) {
        showNotification('Veuillez entrer une URL', 'error');
        return;
    }

    try {
        await apiCall('/api/gallery/', 'POST', { name, url });
        showNotification('Photo ajoutée', 'success');
        closeModal();
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

function viewPhoto(photoId, url, name) {
    let modal = document.getElementById('modal');
    let modalContent = document.getElementById('modalContent');

    modalContent.innerHTML = `
        <h3>${name || 'Photo'}</h3>
        <img src="${url}" style="width: 100%; max-height: 400px; object-fit: contain; border-radius: 10px;">
        <div class="modal-actions">
            <button class="btn-edit" onclick="closeModal()">Fermer</button>
        </div>
    `;

    modal.classList.add('active');
}

async function deletePhoto(photoId) {
    if (!confirm('Voulez-vous vraiment supprimer cette photo ?')) return;

    try {
        await apiCall('/api/gallery/', 'DELETE', { id: photoId });
        showNotification('Photo supprimée', 'success');
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

function editHours() {
    let hours = currentRestaurant?.hours || {};

    let modal = document.getElementById('modal');
    let modalContent = document.getElementById('modalContent');

    modalContent.innerHTML = `
        <h3>Modifier les horaires</h3>
        <div style="display: grid; gap: 15px;">
            <div>
                <label>Lundi - Vendredi</label>
                <input type="text" id="hoursWeek" value="${hours.monday_friday || ''}" style="width: 100%; padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            </div>
            <div>
                <label>Samedi</label>
                <input type="text" id="hoursSat" value="${hours.saturday || ''}" style="width: 100%; padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            </div>
            <div>
                <label>Dimanche</label>
                <input type="text" id="hoursSun" value="${hours.sunday || ''}" style="width: 100%; padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            </div>
        </div>
        <div class="modal-actions">
            <button class="btn-add" onclick="saveHours()">Enregistrer</button>
            <button class="btn-edit" onclick="closeModal()">Annuler</button>
        </div>
    `;

    modal.classList.add('active');
}

async function saveHours() {
    let weekday = document.getElementById('hoursWeek')?.value;
    let saturday = document.getElementById('hoursSat')?.value;
    let sunday = document.getElementById('hoursSun')?.value;

    try {
        await apiCall('/api/restaurant-settings/', 'POST', {
            hours_weekday: weekday,
            hours_saturday: saturday,
            hours_sunday: sunday,
        });
        currentRestaurant.hours = {
            monday_friday: weekday,
            saturday: saturday,
            sunday: sunday,
        };
        displayHours();
        showNotification('Horaires mis à jour', 'success');
        closeModal();
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

function showAddPromoModal() {
    let modal = document.getElementById('modal');
    let modalContent = document.getElementById('modalContent');

    modalContent.innerHTML = `
        <h3>Nouvelle promotion</h3>
        <div style="display: grid; gap: 15px;">
            <input type="text" id="promoTitle" placeholder="Titre" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <input type="text" id="promoDesc" placeholder="Description" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <input type="text" id="promoDiscount" placeholder="Réduction (ex: -20%)" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;">
            <input type="date" id="promoStart" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;" value="${new Date().toISOString().split('T')[0]}">
            <input type="date" id="promoEnd" style="padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px;" value="${new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0]}">
        </div>
        <div class="modal-actions">
            <button class="btn-add" onclick="addPromo()">Créer</button>
            <button class="btn-edit" onclick="closeModal()">Annuler</button>
        </div>
    `;

    modal.classList.add('active');
}

async function addPromo() {
    let title = document.getElementById('promoTitle')?.value;
    let description = document.getElementById('promoDesc')?.value;
    let discount = document.getElementById('promoDiscount')?.value;
    let startDate = document.getElementById('promoStart')?.value;
    let endDate = document.getElementById('promoEnd')?.value;

    if (!title || !description || !discount) {
        showNotification('Veuillez remplir tous les champs', 'error');
        return;
    }

    try {
        await apiCall('/api/promotion/', 'POST', {
            title, description, discount,
            start_date: startDate,
            end_date: endDate,
        });
        showNotification('Promotion créée', 'success');
        closeModal();
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

async function deletePromotion(id) {
    if (!confirm('Voulez-vous vraiment supprimer cette promotion ?')) return;

    try {
        await apiCall('/api/promotion/', 'DELETE', { id: id });
        showNotification('Promotion supprimée', 'success');
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

function showAddMemberModal() {
    showNotification('Fonctionnalité en cours de développement', 'info');
}

function viewMemberHistory(memberId) {
    showNotification('Fonctionnalité en cours de développement', 'info');
}

function deleteMember(memberId) {
    showNotification('Fonctionnalité en cours de développement', 'info');
}

function showReplyModal(reviewId) {
    let modal = document.getElementById('modal');
    let modalContent = document.getElementById('modalContent');

    let review = (dashboardData.reviews || []).find(r => r.id === reviewId);
    let existingReply = review ? (review.reply || '') : '';

    modalContent.innerHTML = `
        <h3>${existingReply ? 'Modifier la réponse' : 'Répondre à l\'avis'}</h3>
        <textarea id="replyText" rows="4" placeholder="Votre réponse..." style="width: 100%; padding: 12px; border: 2px solid #F0E5D8; border-radius: 12px; margin-bottom: 15px;">${existingReply}</textarea>
        <div class="modal-actions">
            <button class="btn-add" onclick="submitReply('${reviewId}')">${existingReply ? 'Modifier' : 'Envoyer'}</button>
            <button class="btn-edit" onclick="closeModal()">Annuler</button>
        </div>
    `;

    modal.classList.add('active');
}

async function submitReply(reviewId) {
    let reply = document.getElementById('replyText')?.value;
    if (!reply || !reply.trim()) {
        showNotification('Veuillez entrer une réponse', 'error');
        return;
    }

    try {
        await apiCall('/api/review-reply/', 'POST', { id: reviewId, reply: reply });
        showNotification('Réponse envoyée avec succès', 'success');
        closeModal();
        loadDashboardData();
    } catch (e) {
        showNotification('Erreur lors de l\'envoi', 'error');
    }
}

function reportReview(reviewId) {
    if (confirm('Voulez-vous signaler cet avis ?')) {
        showNotification('Avis signalé', 'success');
    }
}

// Fonction pour switcher entre les onglets du menu
function switchMenuTab(tabId, tabElement) {
    // Masquer tous les contenus des onglets
    const allTabContents = document.querySelectorAll('.menu-tab-content');
    allTabContents.forEach(content => {
        content.classList.remove('active');
    });

    // Désactiver tous les boutons onglet
    const allTabButtons = document.querySelectorAll('.menu-tab');
    allTabButtons.forEach(btn => {
        btn.classList.remove('active');
    });

    // Afficher le contenu de l'onglet sélectionné
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Activer le bouton de l'onglet sélectionné
    if (tabElement) {
        tabElement.classList.add('active');
    }
}

function exportReviews() {
    let reviews = dashboardData.reviews || [];
    let dataStr = JSON.stringify(reviews, null, 2);
    let dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    let linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', 'avis.json');
    linkElement.click();
    showNotification('Export terminé', 'success');
}

async function saveSettings(event) {
    event.preventDefault();

    let data = {
        name: document.getElementById('settingsName')?.value,
        description: document.getElementById('settingsDescription')?.value,
        phone: document.getElementById('settingsPhone')?.value,
        email: document.getElementById('settingsEmail')?.value,
        address: document.getElementById('settingsAddress')?.value,
        cuisine: document.getElementById('settingsCuisine')?.value,
        price: document.getElementById('settingsPrice')?.value,
    };

    try {
        await apiCall('/api/restaurant-settings/', 'POST', data);
        document.getElementById('restaurantName').textContent = data.name;
        document.getElementById('restaurantPhone').innerHTML = `<i class="fas fa-phone"></i> ${data.phone}`;
        showNotification('Paramètres enregistrés', 'success');
    } catch (e) {
        showNotification('Erreur', 'error');
    }
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

function showNotification(message, type) {
    type = type || 'info';
    let notification = document.createElement('div');
    notification.className = `toast ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function formatDate(dateString) {
    let d = new Date(dateString);
    let maintenant = new Date();
    let diffTime = Math.abs(maintenant - d);
    let diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return 'Hier';
    if (diffDays < 7) return `Il y a ${diffDays} jours`;
    return d.toLocaleDateString('fr-FR');
}

function formatDisplayDate(dateString) {
    let d = new Date(dateString);
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
}

function getStatusText(status) {
    switch (status) {
        case 'confirmed': return 'Confirmée';
        case 'pending': return 'En attente';
        case 'cancelled': return 'Annulée';
        case 'completed': return 'Terminée';
        default: return status;
    }
}

document.addEventListener('click', function (event) {
    let panel = document.getElementById('notificationsPanel');
    let badge = document.querySelector('.notification-badge');

    if (panel && badge && !panel.contains(event.target) && !badge.contains(event.target)) {
        panel.classList.remove('show');
    }
});

document.addEventListener('DOMContentLoaded', function () {
    loadDashboardData();

    afficherNotifications();

    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function () {
            let section = this.getAttribute('data-section');
            showSection(section);
        });
    });
});

// ===== CHAT : Auto-scroll vers le bas =====
(function () {
    var messagesContainer = document.getElementById('chatMessages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
})();
window.showSection = showSection;
window.filterMenu = filterMenu;
window.showReplyModal = showReplyModal;
window.submitReply = submitReply;
window.reportReview = reportReview;
window.showAddReservationModal = showAddReservationModal;
window.addReservation = addReservation;
window.confirmReservation = confirmReservation;
window.rejectReservation = rejectReservation;
window.showAddMenuItemModal = showAddMenuItemModal;
window.addMenuItem = addMenuItem;
window.editMenuItem = editMenuItem;
window.updateMenuItem = updateMenuItem;
window.deleteMenuItem = deleteMenuItem;
window.uploadPhotos = uploadPhotos;
window.addPhoto = addPhoto;
window.viewPhoto = viewPhoto;
window.deletePhoto = deletePhoto;
window.editHours = editHours;
window.saveHours = saveHours;
window.showAddPromoModal = showAddPromoModal;
window.addPromo = addPromo;
window.deletePromotion = deletePromotion;
window.showAddMemberModal = showAddMemberModal;
window.addMember = addReservation;
window.viewMemberHistory = viewMemberHistory;
window.deleteMember = deleteMember;
window.saveSettings = saveSettings;
window.exportReviews = exportReviews;
window.toggleNotifications = toggleNotifications;
window.marquerCommeLu = marquerCommeLu;
window.toutMarquerLu = toutMarquerLu;
window.deconnexion = deconnexion;
window.closeModal = closeModal;