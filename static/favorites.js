

document.addEventListener('DOMContentLoaded', function () {

    // Filtres par catégorie
    document.querySelectorAll('.filter-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const categorie = btn.dataset.categorie;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filtrerFavoris(categorie);
        });
    });

    // Boutons "Retirer des favoris"
    document.querySelectorAll('.heart-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const id = btn.dataset.restaurantId;
            retirerFavori(id, btn);
        });
    });

    // Boutons "Voir les détails"
    document.querySelectorAll('.favorite-card-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const id = btn.dataset.restaurantId;
            window.location.href = `/restaurant/${id}/`;
        });
    });
});

// Filtrer les cartes par catégorie
function filtrerFavoris(categorie) {
    document.querySelectorAll('.favorite-card').forEach(function (carte) {
        if (categorie === 'all' || carte.dataset.category === categorie) {
            carte.style.display = 'block';
        } else {
            carte.style.display = 'none';
        }
    });
}

// Retirer un restaurant des favoris
function retirerFavori(restaurantId, btn) {
    const carte = btn.closest('.favorite-card');
    carte.style.opacity = '0';
    carte.style.transform = 'scale(0.9)';
    carte.style.transition = 'all 0.3s ease';

    setTimeout(function () {
        fetch('/toggle-favorite/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'restaurant_id=' + restaurantId
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.status === 'removed') {
                carte.remove();
                afficherToast('Restaurant retiré des favoris');
                const grille = document.getElementById('favoritesGrid');
                if (grille && grille.querySelectorAll('.favorite-card').length === 0) {
                    location.reload();
                }
            }
        })
        .catch(function () { afficherToast('Erreur lors de la suppression'); });
    }, 300);
}

// Afficher un message temporaire
function afficherToast(message) {
    let toast = document.querySelector('.toast-notification');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast-notification';
        document.body.appendChild(toast);
    }
    toast.innerText = message;
    toast.classList.add('show');
    setTimeout(function () { toast.classList.remove('show'); }, 2500);
}

// Récupérer le cookie CSRF
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
