// ============================================================
// PAGE MON COMPTE — Navigation entre les sections
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

    // Navigation entre les sections
    document.querySelectorAll('.section-tab').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const section = btn.dataset.section;

            document.querySelectorAll('.compte-section').forEach(function (el) {
                el.style.display = 'none';
            });

            const cible = document.getElementById('section-' + section);
            if (cible) cible.style.display = 'block';

            document.querySelectorAll('.section-tab').forEach(function (tab) {
                tab.classList.remove('active');
            });
            btn.classList.add('active');
        });
    });

    // Validation du formulaire profil côté client
    const profilForm = document.querySelector('.profil-form');
    if (profilForm) {
        profilForm.addEventListener('submit', function (e) {
            const prenom = profilForm.querySelector('[name="prenom"]').value.trim();
            const nom    = profilForm.querySelector('[name="nom"]').value.trim();
            const email  = profilForm.querySelector('[name="email"]').value.trim();
            const lettres = /^[A-Za-zÀ-ÿ\s\-]{2,50}$/;

            if (!prenom || !nom || !email) {
                e.preventDefault();
                afficherErreurProfil('Tous les champs sont obligatoires.');
                return;
            }
            if (!lettres.test(prenom)) {
                e.preventDefault();
                afficherErreurProfil('Le prénom doit contenir uniquement des lettres (2 à 50 caractères).');
                return;
            }
            if (!lettres.test(nom)) {
                e.preventDefault();
                afficherErreurProfil('Le nom doit contenir uniquement des lettres (2 à 50 caractères).');
                return;
            }
            // L'email est validé côté serveur — en cas d'erreur la page recharge avec le mail original
        });
    }

    // Suppression du compte
    const btnSupprimer = document.getElementById('btnSupprimerCompte');
    if (btnSupprimer) {
        btnSupprimer.addEventListener('click', supprimerCompte);
    }
});

// Afficher un message d'erreur sous le formulaire profil
function afficherErreurProfil(msg) {
    let existing = document.getElementById('profil-error');
    if (existing) existing.remove();
    const div = document.createElement('div');
    div.id = 'profil-error';
    div.style.cssText = 'color:#c0392b;background:#fdecea;border:1px solid #f5c6cb;padding:10px 14px;border-radius:6px;margin-top:10px;font-size:13px;';
    div.textContent = msg;
    document.querySelector('.profil-form').appendChild(div);
    setTimeout(() => div.remove(), 4000);
}

// Demander la suppression du compte
function supprimerCompte() {
    if (!confirm('Êtes-vous sûr de vouloir supprimer votre compte ? Cette action est irréversible.')) return;

    fetch('/supprimer-compte/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.status === 'ok') {
            window.location.href = '/presentation/';
        } else {
            alert('Une erreur est survenue. Veuillez réessayer.');
        }
    })
    .catch(function () {
        alert('Erreur de connexion au serveur.');
    });
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
