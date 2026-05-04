// ============================================================
// PAGE RÉSERVATION
// dbRestaurant est injecté par Django depuis MongoDB
// ============================================================

let currentRestaurant = null;

document.addEventListener('DOMContentLoaded', function () {
    if (typeof dbRestaurant !== 'undefined' && dbRestaurant) {
        currentRestaurant = dbRestaurant;
    }

    afficherInfoRestaurant();

    const champDate = document.getElementById('date');
    const today = new Date().toISOString().split('T')[0];
    champDate.min = today;
    champDate.value = today;
    champDate.addEventListener('change', genererCreneaux);
    genererCreneaux();

    document.getElementById('reservationForm').addEventListener('submit', soumettreReservation);
    document.getElementById('btnFermerModal').addEventListener('click', fermerModal);
});

// ── Afficher les infos du restaurant ──────────────────────────

function afficherInfoRestaurant() {
    if (!currentRestaurant) return;

    const image = document.getElementById('restaurantFullImage');
    if (image && currentRestaurant.image) image.src = currentRestaurant.image;

    const titre = document.getElementById('restaurantTitleHeader');
    if (titre) titre.innerHTML = `Réservation chez <strong>${currentRestaurant.name}</strong>`;

    const nom  = document.getElementById('sideRestaurantName');
    const desc = document.getElementById('sideRestaurantDesc');
    if (nom) nom.textContent = currentRestaurant.name;
    if (desc) {
        desc.textContent = currentRestaurant.cuisine
            ? currentRestaurant.cuisine + ' • ' + (currentRestaurant.address || '')
            : (currentRestaurant.address || '');
    }
}

// ── Générer les créneaux horaires ─────────────────────────────

function genererCreneaux() {
    const selectHeure  = document.getElementById('time');
    const dateChoisie  = document.getElementById('date').value;
    const maintenant   = new Date();
    const estAujourdhui = dateChoisie === maintenant.toISOString().split('T')[0];
    const heureActuelle = maintenant.getHours();
    const minActuelle   = maintenant.getMinutes();

    const tousLesCreneaux = [
        '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
        '19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00', '22:30'
    ];

    let creneauxDisponibles = tousLesCreneaux;

    if (estAujourdhui) {
        creneauxDisponibles = tousLesCreneaux.filter(function (creneau) {
            const parties = creneau.split(':');
            const h = parseInt(parties[0]);
            const m = parseInt(parties[1]);
            return h > heureActuelle || (h === heureActuelle && m > minActuelle);
        });
    }

    if (creneauxDisponibles.length === 0) {
        selectHeure.innerHTML = "<option value=''>Fermé (ou complet) aujourd'hui</option>";
        return;
    }

    selectHeure.innerHTML = '<option value="">Choisir une heure</option>';
    creneauxDisponibles.forEach(function (creneau) {
        const graine = dateChoisie + creneau + (currentRestaurant ? currentRestaurant.id : '1');
        let seed = 0;
        for (let i = 0; i < graine.length; i++) seed += graine.charCodeAt(i);
        const estComplet = (seed % 100) < 25;

        const option = document.createElement('option');
        option.value = creneau;
        option.textContent = estComplet ? creneau + ' (Complet)' : creneau;
        if (estComplet) {
            option.disabled = true;
            option.style.color = '#ccc';
            option.style.fontStyle = 'italic';
        }
        selectHeure.appendChild(option);
    });
}

// ── Validation ────────────────────────────────────────────────

function validerNom(nom) {
    if (nom.length < 2 || nom.length > 50) {
        return 'Le nom doit contenir entre 2 et 50 caractères.';
    }
    const lettresAutorisees = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ-';
    for (let i = 0; i < nom.length; i++) {
        if (!lettresAutorisees.includes(nom[i])) {
            return 'Le nom ne doit contenir que des lettres.';
        }
    }
    return null;
}

function validerTelephone(tel) {
    const chiffres = tel.replace(/\s/g, '');
    if (chiffres.length !== 8) {
        return 'Le numéro doit contenir exactement 8 chiffres.';
    }
    for (let i = 0; i < chiffres.length; i++) {
        if (chiffres[i] < '0' || chiffres[i] > '9') {
            return 'Le numéro ne doit contenir que des chiffres.';
        }
    }
    if ('24579'.indexOf(chiffres[0]) === -1) {
        return 'Le numéro doit commencer par 2, 4, 5, 7 ou 9.';
    }
    return null;
}

function afficherErreur(champId, message) {
    const champ = document.getElementById(champId);
    if (!champ) return;
    champ.style.borderColor = '#e53935';
    const ancienne = document.getElementById('erreur-' + champId);
    if (ancienne) ancienne.remove();
    const erreur = document.createElement('span');
    erreur.id = 'erreur-' + champId;
    erreur.style.cssText = 'color:#e53935;font-size:12px;margin-top:4px;display:block;';
    erreur.textContent = message;
    champ.parentNode.appendChild(erreur);
}

function effacerErreur(champId) {
    const champ = document.getElementById(champId);
    if (champ) champ.style.borderColor = '';
    const erreur = document.getElementById('erreur-' + champId);
    if (erreur) erreur.remove();
}

// ── Soumission du formulaire ──────────────────────────────────

async function soumettreReservation(event) {
    event.preventDefault();

    const date    = document.getElementById('date').value;
    const heure   = document.getElementById('time').value;
    const nom     = document.getElementById('name').value.trim();
    const tel     = document.getElementById('phone').value.trim();
    const nbPers  = parseInt(document.getElementById('guests').value) || 2;
    const demandes = document.getElementById('special_requests')
        ? document.getElementById('special_requests').value
        : '';
    const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;

    effacerErreur('name');
    effacerErreur('phone');
    effacerErreur('time');

    let erreur = false;

    if (!heure) {
        afficherErreur('time', 'Veuillez sélectionner un créneau horaire.');
        erreur = true;
    }
    if (!nom) {
        afficherErreur('name', 'Le nom est obligatoire.');
        erreur = true;
    } else {
        const msgNom = validerNom(nom);
        if (msgNom) { afficherErreur('name', msgNom); erreur = true; }
    }
    if (!tel) {
        afficherErreur('phone', 'Le numéro de téléphone est obligatoire.');
        erreur = true;
    } else {
        const msgTel = validerTelephone(tel);
        if (msgTel) { afficherErreur('phone', msgTel); erreur = true; }
    }

    if (erreur) return;

    const donnees = new FormData();
    donnees.append('date', date);
    donnees.append('time', heure);
    donnees.append('guests', nbPers);
    donnees.append('special_requests', demandes);
    donnees.append('csrfmiddlewaretoken', csrf);

    try {
        const reponse = await fetch(window.location.pathname, {
            method: 'POST',
            body: donnees,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });

        if (reponse.ok) {
            remplirModal(nom, tel, date, heure, nbPers, demandes);
            document.getElementById('confirmationModal').classList.add('active');
            setTimeout(function () { window.location.href = '/mon-compte/'; }, 4000);
        } else {
            alert('Une erreur est survenue. Veuillez réessayer.');
        }
    } catch (e) {
        alert('Erreur de connexion au serveur.');
    }
}


function remplirModal(nom, tel, date, heure, nbPers, demandes) {
    const nomResto = currentRestaurant ? currentRestaurant.name : '';
    const dateFormatee = new Date(date).toLocaleDateString('fr-FR', {
        day: 'numeric', month: 'long', year: 'numeric'
    });

    remplirLigneModal('modal-restaurant', nomResto);
    remplirLigneModal('modal-nom', nom);
    remplirLigneModal('modal-telephone', tel);
    remplirLigneModal('modal-date', dateFormatee);
    remplirLigneModal('modal-heure', heure);
    remplirLigneModal('modal-personnes', nbPers + ' personne(s)');

    const ligneDemandes = document.getElementById('modal-demandes-row');
    if (ligneDemandes) {
        ligneDemandes.style.display = demandes ? '' : 'none';
        remplirLigneModal('modal-demandes', demandes);
    }
}

function remplirLigneModal(id, valeur) {
    const el = document.getElementById(id);
    if (el) el.textContent = valeur;
}

function fermerModal() {
    document.getElementById('confirmationModal').classList.remove('active');
    window.location.href = '/mon-compte/';
}
