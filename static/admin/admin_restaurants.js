// ============================================================
// ADMIN — Liste des restaurants
// adminRestaurants est injecté par Django dans le template
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    afficherRestaurants();
});

function afficherRestaurants() {
    const tbody = document.getElementById('restaurants-table-body');
    const params = new URLSearchParams(window.location.search);
    const filtreStatut  = params.get('status') || '';
    const filtreRecherche = (params.get('search') || '').toLowerCase();

    // Filtrer la liste
    let liste = adminRestaurants.filter(function (r) {
        const correspondStatut = !filtreStatut || r.status === filtreStatut;
        const correspondRecherche = !filtreRecherche ||
            r.name.toLowerCase().includes(filtreRecherche) ||
            r.email.toLowerCase().includes(filtreRecherche) ||
            r.location.toLowerCase().includes(filtreRecherche);
        return correspondStatut && correspondRecherche;
    });

    // Mettre à jour les compteurs
    document.getElementById('stat-pending').textContent   = liste.filter(r => r.status === 'pending').length;
    document.getElementById('stat-approved').textContent  = liste.filter(r => r.status === 'approved').length;
    document.getElementById('stat-rejected').textContent  = liste.filter(r => r.status === 'rejected').length;
    document.getElementById('stat-suspended').textContent = liste.filter(r => r.status === 'suspended').length;

    if (liste.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><i class="fas fa-search"></i><p>Aucun restaurant trouvé</p></td></tr>';
        return;
    }

    // Textes des statuts
    const texteStatut = {
        pending:   'En attente',
        approved:  'Approuvé',
        rejected:  'Rejeté',
        suspended: 'Suspendu'
    };

    tbody.innerHTML = '';
    liste.forEach(function (resto) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div style="display:flex;align-items:center;gap:10px;">
                    <img src="${resto.image}" alt="${resto.name}"
                         style="width:40px;height:40px;border-radius:8px;object-fit:cover;"
                         onerror="this.src='https://via.placeholder.com/40x40?text=R'">
                    <strong>${resto.name}</strong>
                </div>
            </td>
            <td>${resto.email || ''}</td>
            <td>${resto.location || ''}</td>
            <td><span class="badge badge-${resto.status}">${texteStatut[resto.status] || resto.status}</span></td>
            <td>
                <span class="badge ${resto.payment_status === 'paid' ? 'badge-approved' : 'badge-pending'}">
                    ${resto.payment_status === 'paid' ? 'Payé' : 'Non payé'}
                </span>
            </td>
            <td>★ ${resto.rating}</td>
            <td>
                <a href="/admin-panel/restaurants/${resto.id}/" class="btn-icon view" title="Voir">
                    <i class="fas fa-eye"></i>
                </a>
            </td>`;
        tbody.appendChild(tr);
    });
}
