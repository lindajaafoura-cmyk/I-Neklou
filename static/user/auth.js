// ============================================================
// PAGE AUTHENTIFICATION — Connexion et Inscription avec slide
// ============================================================

const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('authContainer');
const userTypeBtn = document.getElementById('userType');
const restaurantTypeBtn = document.getElementById('restaurantType');
const userSignupForm = document.getElementById('userSignupForm');
const restaurantSignupForm = document.getElementById('restaurantSignupForm');
const loginUserType = document.getElementById('login_user_type');

// Basculer vers le panneau d'inscription
if (signUpButton) {
    signUpButton.addEventListener('click', () => {
        container.classList.add('right-panel-active');
    });
}

// Basculer vers le panneau de connexion
if (signInButton) {
    signInButton.addEventListener('click', () => {
        container.classList.remove('right-panel-active');
    });
}

// Auto-open register panel if action=register is in the URL
if (window.location.search.includes('action=register')) {
    if (container) {
        container.classList.add('right-panel-active');
    }
}

// Basculer sur mobile
const mobileSignUp = document.getElementById('mobileSignUp');
const mobileSignIns = document.querySelectorAll('.mobileSignIn');

if (mobileSignUp) {
    mobileSignUp.addEventListener('click', (e) => {
        e.preventDefault();
        container.classList.add('right-panel-active');
    });
}

mobileSignIns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        container.classList.remove('right-panel-active');
    });
});

// Basculer entre utilisateur et restaurant
if (userTypeBtn) {
    userTypeBtn.addEventListener('click', () => {
        userTypeBtn.classList.add('active');
        restaurantTypeBtn.classList.remove('active');
        
        // Mettre à jour le type de connexion
        if (loginUserType) loginUserType.value = 'user';
        
        // Afficher le bon formulaire d'inscription
        if (userSignupForm) userSignupForm.style.display = 'block';
        if (restaurantSignupForm) restaurantSignupForm.style.display = 'none';
    });
}

if (restaurantTypeBtn) {
    restaurantTypeBtn.addEventListener('click', () => {
        restaurantTypeBtn.classList.add('active');
        userTypeBtn.classList.remove('active');
        
        // Mettre à jour le type de connexion
        if (loginUserType) loginUserType.value = 'restaurant';
        
        // Afficher le bon formulaire d'inscription
        if (userSignupForm) userSignupForm.style.display = 'none';
        if (restaurantSignupForm) restaurantSignupForm.style.display = 'block';
    });
}

// ── Cascade Gouvernorat → Ville ────────────────────────────────
const selectGouvernorat = document.getElementById('gouvernorat');
const selectVille = document.getElementById('ville');

const villesParGouvernorat = {
    tunis: ['Tunis', 'La Marsa', 'Carthage', 'Le Bardo', 'Sidi Bou Said'],
    ariana: ['Ariana', 'La Soukra', 'Raoued', 'Sidi Thabet', 'Ettadhamen'],
    benarous: ['Ben Arous', 'Hammam Lif', 'Hammam Chott', 'Bou Mhel', 'El Mourouj'],
    manouba: ['Manouba', 'Den Den', 'Douar Hicher', 'Oued Ellil', 'Tebourba'],
    nabeul: ['Nabeul', 'Hammamet', 'Kélibia', 'Menzel Temime', 'Korba'],
    zaghouan: ['Zaghouan', 'Zriba', 'Bir Mcherga'],
    bizerte: ['Bizerte', 'Menzel Bourguiba', 'Mateur', 'Ras Jebel', 'Sejnane'],
    beja: ['Béja', 'Medjez el-Bab', 'Téboursouk'],
    jendouba: ['Jendouba', 'Tabarka', 'Aïn Draham', 'Ghardimaou'],
    kef: ['Le Kef', 'Tajerouine', 'Sakiet Sidi Youssef'],
    siliana: ['Siliana', 'Bou Arada', 'Gaâfour'],
    sousse: ['Sousse', 'Hammam Sousse', 'Msaken', 'Kalaa Kebira'],
    monastir: ['Monastir', 'Moknine', 'Jemmal', 'Ksar Hellal'],
    mahdia: ['Mahdia', 'Ksour Essef', 'Chebba', 'El Jem'],
    sfax: ['Sfax', 'Sakiet Ezzit', 'Gremda', 'Thyna'],
    kairouan: ['Kairouan', 'Sbikha', 'Haffouz'],
    kasserine: ['Kasserine', 'Sbeitla', 'Feriana'],
    sidibouzid: ['Sidi Bouzid', 'Jilma', 'Meknassy'],
    gabes: ['Gabès', 'El Hamma', 'Mareth'],
    medenine: ['Médenine', 'Djerba', 'Ben Gardane', 'Zarzis'],
    tataouine: ['Tataouine', 'Ghomrassen'],
    gafsa: ['Gafsa', 'Métlaoui', 'Redeyef'],
    tozeur: ['Tozeur', 'Nefta'],
    kebili: ['Kébili', 'Douz']
};

if (selectGouvernorat && selectVille) {
    selectGouvernorat.addEventListener('change', function () {
        const gouvernorat = this.value;
        selectVille.innerHTML = '<option value="">Ville</option>';
        if (gouvernorat && villesParGouvernorat[gouvernorat]) {
            villesParGouvernorat[gouvernorat].forEach(ville => {
                const option = document.createElement('option');
                option.value = ville.toLowerCase().replace(/\s+/g, '');
                option.textContent = ville;
                selectVille.appendChild(option);
            });
        }
    });
}
