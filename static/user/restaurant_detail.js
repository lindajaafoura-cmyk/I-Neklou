// ============================================================
// PAGE DÉTAIL RESTAURANT
// Le HTML est dans le template Django.
// Ce fichier remplit les éléments avec les données de MongoDB.
// ============================================================

const imageDefaut = 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&q=80';
const imageMenuDefaut = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&fit=crop';

document.addEventListener('DOMContentLoaded', function () {
    if (typeof dbRestaurant === 'undefined' || !dbRestaurant) {
        document.getElementById('restaurantNom').textContent = 'Restaurant introuvable';
        return;
    }
    remplirPage(dbRestaurant);
    initialiserFormulaire(dbRestaurant.id);
});

// ── Remplir toute la page avec les données du restaurant ──────

function remplirPage(resto) {
    const image = resto.image || imageDefaut;

    // Showcase
    document.getElementById('showcaseArea').style.backgroundImage = `url('${image}')`;
    document.getElementById('cuisineBadge').textContent = resto.cuisine || 'Restaurant';
    document.getElementById('restaurantNom').textContent = resto.name;
    document.getElementById('restaurantMeta').textContent = [resto.location, convertirPrix(resto.price)].filter(Boolean).join(' · ');
    document.getElementById('restaurantNote').innerHTML = etoiles(Math.floor(resto.rating || 0)) + ` <span class="rating-val">${resto.rating || ''}</span>`;
    document.getElementById('btnReserver').addEventListener('click', function () {
        window.location.href = `/reserver/${resto.id}/`;
    });

    // À propos
    document.getElementById('aboutNom').textContent = resto.name;
    document.getElementById('aboutDescription').textContent = resto.description || 'Aucune description disponible.';
    document.getElementById('aboutImage').src = image;
    document.getElementById('aboutImage').alt = resto.name;
    remplirInfos(resto);
    remplirPromotions(resto.promotions || []);

    // Menu
    remplirMenu(resto.menu || []);

    // Avis
    remplirAvis(resto.reviews || []);

    // Image du formulaire
    document.getElementById('formImage').src = image;
    document.getElementById('formImage').alt = resto.name;
}

// ── Infos (adresse, téléphone, email, budget) ─────────────────

function remplirInfos(resto) {
    const grille = document.getElementById('infoGrille');
    grille.innerHTML = '';

    const infos = [
        { label: 'Adresse',      valeur: resto.address },
        { label: 'Téléphone',    valeur: resto.phone },
        { label: 'Email',        valeur: resto.email },
        { label: 'Budget moyen', valeur: convertirPrix(resto.price) },
    ];

    infos.forEach(function (info) {
        if (!info.valeur) return;
        const div = document.createElement('div');
        div.className = 'info-item';
        div.innerHTML = `<span class="info-label">${info.label}</span><span class="info-value">${info.valeur}</span>`;
        grille.appendChild(div);
    });
}

// ── Promotions ────────────────────────────────────────────────

function remplirPromotions(promotions) {
    const banner = document.getElementById('promotionsBanner');
    if (promotions.length === 0) {
        banner.innerHTML = '';
        return;
    }
    let html = '<div class="promotions-banner">';
    promotions.forEach(function (promo) {
        html += `
            <div class="promotion-card">
                <div class="promo-icon"><i class="fas fa-tags"></i></div>
                <div class="promo-content">
                    <div class="promo-title">${promo.title}</div>
                    <div class="promo-desc">${promo.description}</div>
                    <div class="promo-badge">${promo.discount}</div>
                </div>
            </div>`;
    });
    html += '</div>';
    banner.innerHTML = html;
}

// ── Menu ──────────────────────────────────────────────────────

function remplirMenu(plats) {
    const conteneurCategories = document.getElementById('menuCategories');
    const conteneurPlats = document.getElementById('menuItems');

    if (plats.length === 0) {
        conteneurCategories.innerHTML = '';
        conteneurPlats.innerHTML = '<p style="text-align:center;color:#999;padding:30px;">Menu non disponible.</p>';
        return;
    }

    // Catégories uniques
    const categories = ['Tous'];
    plats.forEach(function (plat) {
        if (!categories.includes(plat.category)) categories.push(plat.category);
    });

    conteneurCategories.innerHTML = '';
    categories.forEach(function (cat, i) {
        const btn = document.createElement('button');
        btn.className = 'menu-category-btn' + (i === 0 ? ' active' : '');
        btn.textContent = cat;
        btn.addEventListener('click', function () {
            document.querySelectorAll('.menu-category-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filtrerMenu(cat);
        });
        conteneurCategories.appendChild(btn);
    });

    conteneurPlats.innerHTML = '';
    plats.forEach(function (plat) {
        const div = document.createElement('div');
        div.className = 'food-menu-item';
        div.dataset.category = plat.category;
        div.innerHTML = `
            <div class="food-img">
                <img src="${plat.image || imageMenuDefaut}" alt="${plat.name}" loading="lazy"
                     onerror="this.src='${imageMenuDefaut}'">
            </div>
            <div class="food-description">
                <span class="food-category-tag">${plat.category}</span>
                <h3 class="food-title">${plat.name}</h3>
                <p class="food-price">${plat.price}</p>
            </div>`;
        conteneurPlats.appendChild(div);
    });
}

function filtrerMenu(categorie) {
    document.querySelectorAll('.food-menu-item').forEach(function (item) {
        item.style.display = (categorie === 'Tous' || item.dataset.category === categorie) ? 'flex' : 'none';
    });
}

// ── Avis ──────────────────────────────────────────────────────

const couleursAvatar = [
    { bg: '#FFF0E0', text: '#E8A030' },
    { bg: '#E8F0E8', text: '#4A6B4D' },
    { bg: '#FAE8E0', text: '#C96E4B' },
    { bg: '#E8E8FA', text: '#6060B0' },
];

function remplirAvis(avis) {
    const conteneur = document.getElementById('listeAvis');
    if (avis.length === 0) {
        conteneur.innerHTML = '<p class="no-reviews">Aucun avis pour le moment. Soyez le premier !</p>';
        return;
    }
    conteneur.innerHTML = '';
    avis.forEach(function (avis, i) {
        const couleur = couleursAvatar[i % couleursAvatar.length];
        const div = document.createElement('div');
        div.className = 'testimonial-box';
        div.innerHTML = `
            <div class="customer-photo">
                <div class="avatar-circle" style="background:${couleur.bg};color:${couleur.text};">
                    ${avis.user.charAt(0).toUpperCase()}
                </div>
                <p class="customer-name">${avis.user}</p>
            </div>
            <div class="star-rating">${etoiles(avis.rating)}</div>
            <p class="testimonial-text">"${avis.comment}"</p>`;
        conteneur.appendChild(div);
    });
}

// ── Formulaire avis ───────────────────────────────────────────

function initialiserFormulaire(restaurantId) {
    // Étoiles cliquables
    document.querySelectorAll('#etoilesNote .star').forEach(function (etoile) {
        etoile.addEventListener('click', function () {
            const note = parseInt(etoile.dataset.value);
            document.getElementById('noteChoisie').value = note;
            document.querySelectorAll('#etoilesNote .star').forEach(function (s, i) {
                s.textContent = i < note ? '★' : '☆';
                s.classList.toggle('active', i < note);
            });
        });
    });

    // Soumission
    document.getElementById('formulaireAvis').addEventListener('submit', function (e) {
        e.preventDefault();
        envoyerAvis(restaurantId);
    });
}

async function envoyerAvis(restaurantId) {
    const nom      = document.getElementById('avisNom').value;
    const note     = parseInt(document.getElementById('noteChoisie').value);
    const commentaire = document.getElementById('avisCommentaire').value;

    if (!note) {
        alert('Veuillez sélectionner une note.');
        return;
    }

    // Validation côté client selon les nouvelles spécifications
    if (!commentaire.trim() || commentaire.trim().length < 5) {
        alert('Le commentaire doit contenir au moins 5 caractères.');
        return;
    }

    try {
        const reponse = await fetch('/api/submit-review/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ restaurant_id: restaurantId, name: nom, rating: note, comment: commentaire })
        });

        const data = await reponse.json();
        if (data.status === 'success') {
            alert('Merci ! Votre avis a été enregistré.');
            document.getElementById('formulaireAvis').reset();
            document.getElementById('noteChoisie').value = 0;
            document.querySelectorAll('#etoilesNote .star').forEach(s => s.textContent = '☆');
            // Ajouter l'avis en tête de liste sans recharger
            const conteneur = document.getElementById('listeAvis');
            const div = document.createElement('div');
            div.className = 'testimonial-box';
            div.innerHTML = `
                <div class="customer-photo">
                    <div class="avatar-circle" style="background:#E8F0E8;color:#4A6B4D;">${nom.charAt(0).toUpperCase()}</div>
                    <p class="customer-name">${nom}</p>
                </div>
                <div class="star-rating">${etoiles(note)}</div>
                <p class="testimonial-text">"${commentaire}"</p>`;
            conteneur.prepend(div);
        } else {
            alert('Erreur : ' + data.error);
        }
    } catch (e) {
        alert('Erreur lors de l\'envoi de l\'avis.');
    }
}

// ── Utilitaires ───────────────────────────────────────────────

function etoiles(n) {
    return '★'.repeat(Math.max(0, n)) + '☆'.repeat(Math.max(0, 5 - n));
}

function convertirPrix(symbole) {
    const map = { '$': 'Moins de 30 DT', '$$': '30–80 DT', '$$$': '80–150 DT', '$$$$': '150+ DT' };
    return map[symbole] || symbole || '';
}

function getCookie(name) {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) return decodeURIComponent(cookie.substring(name.length + 1));
    }
    return null;
}
