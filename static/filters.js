// ============================================================
// Sidebar Filters Manager - Système de filtrage avancé
// ============================================================
// Gère tous les aspects du filtrage par la sidebar :
// - Filtres par ville, cuisine, note, budget
// - Recherche en temps réel
// - Persistance des filtres
// - Affichage des résultats

class SidebarFilters {
    constructor(restaurantsData = []) {
        this.allRestaurants = restaurantsData;
        this.filteredRestaurants = restaurantsData;
        this.currentFilters = {
            search: '',
            cities: [],
            cuisines: [],
            rating: 0,
            budget: 200
        };
        this.init();
    }

    // ─────────────────────────────────────────────────────
    // Initialisation
    // ─────────────────────────────────────────────────────

    init() {
        this.attachEventListeners();
        this.loadSavedFilters();
    }

    attachEventListeners() {
        // Recherche texte
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e));
        }

        // Filtres checkbox (ville, cuisine)
        document.querySelectorAll('.filter-ville, .filter-cuisine').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.applyFilters());
        });

        // Filtre note (radio buttons)
        document.querySelectorAll('input[name="rating"]').forEach(radio => {
            radio.addEventListener('change', () => this.applyFilters());
        });

        // Curseur de budget
        const priceSlider = document.getElementById('priceSlider');
        if (priceSlider) {
            priceSlider.addEventListener('input', (e) => this.handleBudgetChange(e));
        }

        // Bouton réinitialiser
        const resetBtn = document.getElementById('resetFiltersBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetFilters());
        }
    }

    // ─────────────────────────────────────────────────────
    // Gestion des filtres
    // ─────────────────────────────────────────────────────

    handleSearch(event) {
        this.currentFilters.search = event.target.value.toLowerCase().trim();
        this.applyFilters();
    }

    handleBudgetChange(event) {
        const value = parseInt(event.target.value);
        this.currentFilters.budget = value;
        
        // Mise à jour du label
        const label = document.getElementById('budgetLabel');
        if (label) {
            label.textContent = `Budget: ${value} TND`;
        }
        
        this.applyFilters();
    }

    collectSelectedFilters() {
        // Villes sélectionnées
        const cities = Array.from(document.querySelectorAll('.filter-ville:checked'))
            .map(cb => cb.value.toLowerCase());
        this.currentFilters.cities = cities;

        // Cuisines sélectionnées
        const cuisines = Array.from(document.querySelectorAll('.filter-cuisine:checked'))
            .map(cb => cb.value.toLowerCase());
        this.currentFilters.cuisines = cuisines;

        // Note sélectionnée
        const ratingRadio = document.querySelector('input[name="rating"]:checked');
        this.currentFilters.rating = ratingRadio ? parseInt(ratingRadio.value) : 0;
    }

    applyFilters() {
        this.collectSelectedFilters();
        this.filteredRestaurants = this.filterRestaurants();
        this.displayResults();
        this.saveSavedFilters();
    }

    filterRestaurants() {
        return this.allRestaurants.filter(restaurant => {
            // Filtre recherche texte
            if (this.currentFilters.search) {
                const search = this.currentFilters.search;
                const matchName = restaurant.name.toLowerCase().includes(search);
                const matchCuisine = restaurant.cuisine.toLowerCase().includes(search);
                const matchLocation = restaurant.location.toLowerCase().includes(search);
                
                if (!matchName && !matchCuisine && !matchLocation) {
                    return false;
                }
            }

            // Filtre ville
            if (this.currentFilters.cities.length > 0) {
                const city = restaurant.location.toLowerCase();
                if (!this.currentFilters.cities.includes(city)) {
                    return false;
                }
            }

            // Filtre cuisine
            if (this.currentFilters.cuisines.length > 0) {
                const cuisine = restaurant.cuisine.toLowerCase();
                const isOthers = this.currentFilters.cuisines.includes('autres');
                
                if (cuisine === 'autres') {
                    if (!isOthers) return false;
                } else {
                    const match = this.currentFilters.cuisines.some(c => 
                        cuisine.includes(c) || c.includes(cuisine)
                    );
                    if (!match) return false;
                }
            }

            // Filtre note
            if (this.currentFilters.rating > 0) {
                if (Math.round(restaurant.rating) !== this.currentFilters.rating) {
                    return false;
                }
            }

            // Filtre budget (prix estimé basé sur le symbole $)
            const budgetMap = { '$': 30, '$$': 80, '$$$': 150, '$$$$': 200 };
            const restaurantBudget = budgetMap[restaurant.price] || 0;
            if (restaurantBudget > this.currentFilters.budget) {
                return false;
            }

            return true;
        });
    }

    // ─────────────────────────────────────────────────────
    // Affichage des résultats
    // ─────────────────────────────────────────────────────

    displayResults() {
        const grid = document.getElementById('restaurantsGrid');
        if (!grid) return;

        const cards = grid.querySelectorAll('.restaurant-card');
        let visibleCount = 0;

        cards.forEach(card => {
            const restaurantId = card.dataset.id;
            const isVisible = this.filteredRestaurants.some(r => r.id == restaurantId);
            
            card.style.display = isVisible ? '' : 'none';
            if (isVisible) visibleCount++;
        });

        this.updateResultsCount(visibleCount);
        this.showEmptyMessage(visibleCount === 0);
    }

    updateResultsCount(count) {
        const counter = document.getElementById('restaurantCount');
        if (counter) {
            const pluriel = count > 1 ? 's' : '';
            counter.textContent = `${count} restaurant${pluriel} trouvé${pluriel}`;
        }
    }

    showEmptyMessage(isEmpty) {
        let msgVide = document.getElementById('noResultMsg');
        
        if (isEmpty) {
            if (!msgVide) {
                msgVide = document.createElement('div');
                msgVide.id = 'noResultMsg';
                msgVide.className = 'empty-results-message';
                msgVide.innerHTML = `
                    <div class="empty-icon">🍽️</div>
                    <p>Aucun restaurant ne correspond à vos critères</p>
                    <small>Essayez de modifier vos filtres</small>
                `;
                document.getElementById('restaurantsGrid')?.appendChild(msgVide);
            }
        } else if (msgVide) {
            msgVide.remove();
        }
    }

    // ─────────────────────────────────────────────────────
    // Réinitialisation
    // ─────────────────────────────────────────────────────

    resetFilters() {
        // Réinitialiser les checkboxes
        document.querySelectorAll('.filter-ville, .filter-cuisine').forEach(cb => {
            cb.checked = false;
        });

        // Réinitialiser les radio buttons
        const defaultRating = document.querySelector('input[name="rating"][value="0"]');
        if (defaultRating) defaultRating.checked = true;

        // Réinitialiser la recherche
        const searchInput = document.getElementById('searchInput');
        if (searchInput) searchInput.value = '';

        // Réinitialiser le budget
        const priceSlider = document.getElementById('priceSlider');
        if (priceSlider) {
            priceSlider.value = 200;
            const label = document.getElementById('budgetLabel');
            if (label) label.textContent = 'Budget: 200 TND';
        }

        // Appliquer les filtres (qui vont afficher tous les restaurants)
        this.applyFilters();
    }

    // ─────────────────────────────────────────────────────
    // Persistance des filtres (localStorage)
    // ─────────────────────────────────────────────────────

    saveSavedFilters() {
        localStorage.setItem('dinetunis_filters', JSON.stringify(this.currentFilters));
    }

    loadSavedFilters() {
        const saved = localStorage.getItem('dinetunis_filters');
        if (saved) {
            try {
                const filters = JSON.parse(saved);
                this.restoreFiltersUI(filters);
                this.applyFilters();
            } catch (e) {
                console.warn('Erreur chargement des filtres sauvegardés', e);
            }
        }
    }

    restoreFiltersUI(filters) {
        // Restaurer recherche
        const searchInput = document.getElementById('searchInput');
        if (searchInput && filters.search) {
            searchInput.value = filters.search;
        }

        // Restaurer villes
        if (filters.cities && filters.cities.length > 0) {
            document.querySelectorAll('.filter-ville').forEach(cb => {
                cb.checked = filters.cities.includes(cb.value.toLowerCase());
            });
        }

        // Restaurer cuisines
        if (filters.cuisines && filters.cuisines.length > 0) {
            document.querySelectorAll('.filter-cuisine').forEach(cb => {
                cb.checked = filters.cuisines.includes(cb.value.toLowerCase());
            });
        }

        // Restaurer note
        if (filters.rating > 0) {
            const ratingRadio = document.querySelector(`input[name="rating"][value="${filters.rating}"]`);
            if (ratingRadio) ratingRadio.checked = true;
        }

        // Restaurer budget
        const priceSlider = document.getElementById('priceSlider');
        if (priceSlider && filters.budget) {
            priceSlider.value = filters.budget;
            const label = document.getElementById('budgetLabel');
            if (label) label.textContent = `Budget: ${filters.budget} TND`;
        }
    }

    // ─────────────────────────────────────────────────────
    // API publique
    // ─────────────────────────────────────────────────────

    getFilteredRestaurants() {
        return this.filteredRestaurants;
    }

    updateRestaurantsData(data) {
        this.allRestaurants = data;
        this.applyFilters();
    }

    getCurrentFilters() {
        return { ...this.currentFilters };
    }
}

// ============================================================
// Initialisation automatique au chargement du DOM
// ============================================================

let sidebarFilters = null;

document.addEventListener('DOMContentLoaded', function () {
    // Récupérer les données depuis l'attribut data du DOM
    const gridElement = document.getElementById('restaurantsGrid');
    let restaurantsData = [];

    if (gridElement && gridElement.dataset.restaurants) {
        try {
            restaurantsData = JSON.parse(gridElement.dataset.restaurants);
        } catch (e) {
            console.error('Erreur parsing données restaurants:', e);
        }
    }

    // Initialiser le gestionnaire de filtres
    sidebarFilters = new SidebarFilters(restaurantsData);
});

// ============================================================
// Anciennes fonctions (compatibilité)
// ============================================================

function filtrerRestaurants() {
    if (sidebarFilters) {
        sidebarFilters.applyFilters();
    }
}

function reinitialiserFiltres() {
    if (sidebarFilters) {
        sidebarFilters.resetFilters();
    }
}
