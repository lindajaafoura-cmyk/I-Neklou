// ============================================================
// ADMIN — Programme de fidélité
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    // Afficher la section transactions si paramètre user_id présent
    const params = new URLSearchParams(window.location.search);
    if (params.has('user_id') || window.location.hash === '#transactions') {
        const btnTransactions = document.getElementById('tab-transactions');
        if (btnTransactions) btnTransactions.click();
    }
});

// Basculer entre les sections Utilisateurs et Transactions
function afficherSectionFidelite(section, bouton) {
    document.querySelectorAll('.admin-tab').forEach(function (tab) {
        tab.classList.remove('active');
    });
    bouton.classList.add('active');

    if (section === 'users') {
        document.getElementById('users-section').style.display = 'block';
        document.getElementById('transactions-section').style.display = 'none';
        // Nettoyer l'URL
        const url = new URL(window.location);
        url.searchParams.delete('user_id');
        url.searchParams.delete('type');
        window.history.replaceState({}, '', url);
    } else {
        document.getElementById('users-section').style.display = 'none';
        document.getElementById('transactions-section').style.display = 'block';
    }
}
