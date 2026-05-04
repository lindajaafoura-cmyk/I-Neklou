// ============================================================
// ADMIN — Dashboard & Statistiques
// ============================================================

// Basculer entre les sections Dashboard et Statistiques
function afficherSection(section, bouton) {
    document.querySelectorAll('.admin-tab').forEach(function (tab) {
        tab.classList.remove('active');
    });
    bouton.classList.add('active');

    if (section === 'dashboard') {
        document.getElementById('dashboard-section').style.display = 'block';
        document.getElementById('statistics-section').style.display = 'none';
    } else {
        document.getElementById('dashboard-section').style.display = 'none';
        document.getElementById('statistics-section').style.display = 'block';
        chargerGraphiques();
    }
}

// Charger les graphiques Chart.js (appelé une seule fois)
function chargerGraphiques() {
    // Graphique types d'utilisateurs
    const ctxUsers = document.getElementById('userTypeChart');
    if (ctxUsers && !ctxUsers.dataset.loaded) {
        ctxUsers.dataset.loaded = 'true';
        new Chart(ctxUsers.getContext('2d'), {
            type: 'pie',
            data: {
                labels: ['Utilisateurs', 'Restaurants', 'Administrateurs'],
                datasets: [{
                    data: [
                        parseInt(document.getElementById('count-user').textContent) || 0,
                        parseInt(document.getElementById('count-restaurant').textContent) || 0,
                        parseInt(document.getElementById('count-admin').textContent) || 0
                    ],
                    backgroundColor: ['#1976D2', '#F57C00', '#6A1B9A'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    // Graphique statuts restaurants
    const ctxStatus = document.getElementById('restaurantStatusChart');
    if (ctxStatus && !ctxStatus.dataset.loaded) {
        ctxStatus.dataset.loaded = 'true';
        new Chart(ctxStatus.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['En attente', 'Approuvé', 'Rejeté', 'Suspendu'],
                datasets: [{
                    label: 'Restaurants',
                    data: [
                        parseInt(document.getElementById('count-pending').textContent) || 0,
                        parseInt(document.getElementById('count-approved').textContent) || 0,
                        parseInt(document.getElementById('count-rejected').textContent) || 0,
                        parseInt(document.getElementById('count-suspended').textContent) || 0
                    ],
                    backgroundColor: ['#F57C00', '#2E7D32', '#C62828', '#6A1B9A'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#F0E5D8' } }
                }
            }
        });
    }
}
