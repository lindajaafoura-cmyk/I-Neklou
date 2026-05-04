
function filtrerRestaurants() {
    const cartes = document.querySelectorAll('#restaurantsGrid .restaurant-card');
    if (!cartes.length) return;

    const recherche = (document.getElementById('searchInput')?.value || '').toLowerCase().trim();

    const villesChoisies = Array.from(
        document.querySelectorAll('.filter-ville:checked')
    ).map(cb => cb.value.toLowerCase());

    const cuisinesChoisies = Array.from(
        document.querySelectorAll('.filter-cuisine:checked')
    ).map(cb => cb.value.toLowerCase());

    const noteRadio = document.querySelector('input[name="rating"]:checked');
    const noteMin = noteRadio ? parseFloat(noteRadio.value) : 0;

    let nbVisible = 0;

    cartes.forEach(carte => {
        const nom     = (carte.querySelector('.card-title')?.textContent || '').toLowerCase();
        const cuisine = (carte.dataset.cuisine || '').toLowerCase();
        const ville   = (carte.dataset.ville || '').toLowerCase();
        const note    = parseFloat(carte.dataset.rating || '0');
        const budget  = (carte.dataset.budget || '').trim();

        let afficher = true;

        // Filtre par mot-clé
        if (recherche && !nom.includes(recherche) && !cuisine.includes(recherche) && !ville.includes(recherche)) {
            afficher = false;
        }

        // Filtre par ville
        if (afficher && villesChoisies.length > 0) {
            if (!ville) {
                afficher = false;
            } else {
                afficher = villesChoisies.some(v => ville.includes(v) || v.includes(ville));
            }
        }

        // Filtre par cuisine
        if (afficher && cuisinesChoisies.length > 0) {
            if (!cuisine || cuisine === 'autres') {
                afficher = cuisinesChoisies.includes('autres');
            } else {
                afficher = cuisinesChoisies.some(c => cuisine.includes(c) || c.includes(cuisine));
            }
        }

        const slider = document.getElementById('priceSlider');
        if (slider && parseInt(slider.value) < 150) {
            const prixMax = parseInt(slider.value);
            const budgetMap = { '$': 30, '$$': 80, '$$$': 150, '$$$$': 200 };
            const prixCarte = budgetMap[budget] || 0;
            if (prixCarte > prixMax) afficher = false;
        }

        if (afficher && noteMin > 0) {
            afficher = Math.round(note) === noteMin;
        }

        carte.style.display = afficher ? '' : 'none';
        if (afficher) nbVisible++;
    });

    const compteur = document.getElementById('restaurantCount');
    if (compteur) {
        compteur.textContent = `${nbVisible} restaurant${nbVisible > 1 ? 's' : ''} trouvé${nbVisible > 1 ? 's' : ''}`;
    }

    let msgVide = document.getElementById('noResultMsg');
    if (nbVisible === 0) {
        if (!msgVide) {
            msgVide = document.createElement('div');
            msgVide.id = 'noResultMsg';
            msgVide.style.cssText = 'grid-column:1/-1;text-align:center;padding:40px;color:#999;font-size:15px;';
            msgVide.textContent = 'Aucun restaurant trouvé pour ces critères.';
            document.getElementById('restaurantsGrid').appendChild(msgVide);
        }
    } else if (msgVide) {
        msgVide.remove();
    }
}

function reinitialiserFiltres() {
    document.querySelectorAll('.filter-ville, .filter-cuisine, .filter-budget').forEach(cb => cb.checked = false);

    const noteDefaut = document.querySelector('input[name="rating"][value="0"]');
    if (noteDefaut) noteDefaut.checked = true;

    const champRecherche = document.getElementById('searchInput');
    if (champRecherche) champRecherche.value = '';

    document.querySelectorAll('#restaurantsGrid .restaurant-card').forEach(c => c.style.display = '');

    const msgVide = document.getElementById('noResultMsg');
    if (msgVide) msgVide.remove();

    const total = document.querySelectorAll('#restaurantsGrid .restaurant-card').length;
    const compteur = document.getElementById('restaurantCount');
    if (compteur) {
        compteur.textContent = `${total} restaurant${total > 1 ? 's' : ''} trouvé${total > 1 ? 's' : ''}`;
    }
}

function basculerFiltre(header) {
    header.parentElement.classList.toggle('collapsed');
}


async function basculerFavori(event, restaurantId, nomRestaurant, imageRestaurant, cuisine, note, ville, categorie) {
    event.stopPropagation();
    const btn = event.currentTarget;
    const icone = btn.querySelector('i');

    try {
        const reponse = await fetch('/toggle-favorite/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `restaurant_id=${restaurantId}&restaurant_name=${encodeURIComponent(nomRestaurant)}&restaurant_image=${encodeURIComponent(imageRestaurant || '')}&cuisine=${encodeURIComponent(cuisine || '')}&rating=${encodeURIComponent(note || '')}&location=${encodeURIComponent(ville || '')}&category=${encodeURIComponent(categorie || '')}`
        });

        const data = await reponse.json();

        if (data.status === 'added') {
            icone?.classList.replace('far', 'fas');
            afficherNotification('Ajouté aux favoris ♥');
        } else if (data.status === 'removed') {
            icone?.classList.replace('fas', 'far');
            afficherNotification('Retiré des favoris');
        }
    } catch (e) {
        afficherNotification('Erreur, veuillez réessayer.');
    }
}

async function verifierFavoris() {
    const cartes = document.querySelectorAll('.restaurant-card[data-id]');
    for (const carte of cartes) {
        const id = carte.dataset.id;
        if (!id) continue;
        try {
            const reponse = await fetch(`/api/is-favorite/${id}/`);
            const data = await reponse.json();
            if (data.is_favorite) {
                const icone = carte.querySelector('.fav-btn i');
                icone?.classList.replace('far', 'fas');
            }
        } catch (e) {

        }
    }
}

function afficherNotification(message) {
    const notif = document.createElement('div');
    notif.textContent = message;
    notif.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#2D5A3B;color:white;padding:12px 20px;border-radius:8px;z-index:1000;font-size:14px;';
    document.body.appendChild(notif);
    setTimeout(() => {
        notif.style.opacity = '0';
        notif.style.transition = 'opacity 0.5s';
        setTimeout(() => notif.remove(), 500);
    }, 2000);
}

function getCookie(name) {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return null;
}

document.addEventListener('DOMContentLoaded', () => {
    verifierFavoris();

    document.getElementById('searchBtn')?.addEventListener('click', filtrerRestaurants);
    document.getElementById('searchInput')?.addEventListener('input', filtrerRestaurants);
    document.getElementById('searchInput')?.addEventListener('keyup', e => {
        if (e.key === 'Enter') filtrerRestaurants();
    });

    document.getElementById('resetFilters')?.addEventListener('click', reinitialiserFiltres);

    document.querySelectorAll('.filter-ville, .filter-cuisine, .filter-budget, input[name="rating"]').forEach(el => {
        el.addEventListener('change', filtrerRestaurants);
    });

    const slider = document.getElementById('priceSlider');
    if (slider) {
        slider.addEventListener('input', function () {
            const val = parseInt(this.value);
            const label = document.getElementById('priceLabel');
            if (label) label.textContent = val >= 150 ? 'Tous les budgets' : `Max: ${val} DT`;
            const pct = (val / 150) * 100;
            this.style.background = `linear-gradient(to right, #2D5A3B 0%, #2D5A3B ${pct}%, #ddd ${pct}%, #ddd 100%)`;
            filtrerRestaurants();
        });
    }
});
