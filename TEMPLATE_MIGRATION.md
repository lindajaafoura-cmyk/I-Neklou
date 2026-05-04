# 📝 Guide de Migration des Templates

## 📋 Checklist de mise à jour

### ✅ Fichiers créés/modifiés
- [x] `services.py` - Logique métier centralisée
- [x] `static/filters.js` - Système de filtrage avancé
- [x] `static/filters.css` - Styles modernes
- [x] `views_user.py` - Optimisé pour utiliser services
- [x] `ARCHITECTURE.md` - Documentation architecture
- [x] `README_GUIDE.md` - Guide complet
- [ ] Templates HTML - À mettre à jour
- [ ] `settings.py` - À vérifier configuration

---

## 🔄 Migration des templates

### 1. **index.html** - Page d'accueil

#### Avant
```html
<!-- Pas d'organisation du JS -->
<script src="{% static 'script.js' %}"></script>
```

#### Après
```html
<!-- Ajouter les nouveaux fichiers -->
<head>
    <link rel="stylesheet" href="{% static 'filters.css' %}">
</head>

<body>
    <!-- Sidebar amélioré -->
    <aside class="sidebar">
        <div class="sidebar-filters">
            <h3>🔍 Filtrer</h3>
            
            <!-- Recherche -->
            <div class="filter-section">
                <div class="search-box">
                    <input type="text" id="searchInput" 
                           placeholder="Rechercher restaurant..." 
                           class="form-control">
                </div>
            </div>
            
            <!-- Villes -->
            <div class="filter-section">
                <div class="filter-section-title">📍 Villes</div>
                <div class="checkbox-group">
                    {% for city in cities %}
                    <div class="checkbox-item">
                        <input type="checkbox" id="city_{{ city }}" 
                               class="filter-ville" value="{{ city }}">
                        <label for="city_{{ city }}">{{ city }}</label>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Cuisines -->
            <div class="filter-section">
                <div class="filter-section-title">🍴 Cuisines</div>
                <div class="checkbox-group">
                    {% for cuisine in cuisines %}
                    <div class="checkbox-item">
                        <input type="checkbox" id="cuisine_{{ cuisine }}" 
                               class="filter-cuisine" value="{{ cuisine }}">
                        <label for="cuisine_{{ cuisine }}">{{ cuisine }}</label>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Notes -->
            <div class="filter-section">
                <div class="filter-section-title">⭐ Note minimale</div>
                <div class="rating-group">
                    <div class="rating-item">
                        <input type="radio" id="rating_0" name="rating" value="0" checked>
                        <label for="rating_0">Toutes les notes</label>
                    </div>
                    {% for rating in ratings %}
                    <div class="rating-item">
                        <input type="radio" id="rating_{{ rating }}" 
                               name="rating" value="{{ rating }}">
                        <label for="rating_{{ rating }}">
                            {{ rating }} <span class="rating-stars">{{'★'|repeat:rating }}</span>
                        </label>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Budget -->
            <div class="filter-section">
                <div class="filter-section-title">💰 Budget maximum</div>
                <div class="budget-slider-group">
                    <label id="budgetLabel">Budget: 200 TND</label>
                    <input type="range" id="priceSlider" 
                           min="0" max="200" value="200">
                    <div class="budget-info">
                        Mise à jour en temps réel
                    </div>
                </div>
            </div>
            
            <!-- Actions -->
            <div class="filter-actions">
                <button id="resetFiltersBtn">↻ Réinitialiser</button>
            </div>
            
            <!-- Compteur résultats -->
            <div class="results-counter">
                <div id="restaurantCount">0 restaurant trouvé</div>
            </div>
        </div>
    </aside>
    
    <!-- Grille des restaurants -->
    <main class="content">
        <div id="restaurantsGrid" 
             class="restaurant-grid"
             data-restaurants='{{ db_restaurants|escapejs }}'>
            {% for rest in restaurants %}
            <div class="restaurant-card" 
                 data-id="{{ rest.id }}"
                 data-cuisine="{{ rest.cuisine|lower }}"
                 data-ville="{{ rest.location|lower }}"
                 data-rating="{{ rest.rating }}"
                 data-budget="{{ rest.price }}">
                <img src="{{ rest.image }}" alt="{{ rest.name }}">
                <h3 class="card-title">{{ rest.name }}</h3>
                <p class="cuisine">{{ rest.cuisine }}</p>
                <p class="location">📍 {{ rest.location }}</p>
                <div class="rating">⭐ {{ rest.rating }}/5</div>
                {% if rest.promotion %}
                <div class="promotion">
                    -{{ rest.promotion.discount }}%
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </main>
    
    <!-- Scripts -->
    <script src="{% static 'filters.js' %}"></script>
    <script src="{% static 'script.js' %}"></script>
</body>
```

---

### 2. **restaurant_detail.html** - Détails du restaurant

#### Avant
```html
<!-- Affichage basique -->
{% if db_restaurant %}
    {{ db_restaurant }}
{% endif %}
```

#### Après (utilise les services automatiquement)
```html
<script>
    // Les données sont déjà formatées par RestaurantService
    const restaurant = JSON.parse('{{ db_restaurant|escapejs }}');
</script>

<!-- Menu -->
{% if restaurant.menu %}
<section class="menu">
    <h2>Menu</h2>
    {% for item in restaurant.menu %}
    <div class="menu-item">
        <h4>{{ item.name }}</h4>
        <p>{{ item.category }} - {{ item.price }}</p>
    </div>
    {% endfor %}
</section>
{% endif %}

<!-- Avis -->
{% if restaurant.reviews %}
<section class="reviews">
    <h2>Avis ({{ restaurant.reviews|length }})</h2>
    <div class="reviews-list">
        {% for review in restaurant.reviews %}
        <div class="review">
            <div class="review-header">
                <strong>{{ review.user }}</strong>
                <span class="rating">⭐ {{ review.rating }}/5</span>
            </div>
            <p>{{ review.comment }}</p>
            <small>{{ review.date }}</small>
        </div>
        {% endfor %}
    </div>
</section>
{% endif %}
```

---

### 3. **mon_compte.html** - Espace utilisateur

Code existant OK, mais améliorer avec les services si besoin de refactor.

---

## 🛠️ Mise à jour des vues pour les templates

### Envoyer les données correctes au template

```python
# views_user.py
from django.db.models import Q

def index(request):
    """Page d'accueil optimisée."""
    from pages.services import RestaurantService
    
    # Obtenir tous les restaurants
    restaurants = RestaurantService.get_all_restaurants()
    
    # Extraire données uniques pour filtres
    cities = sorted(set(r['location'] for r in restaurants if r['location']))
    cuisines = sorted(set(r['cuisine'] for r in restaurants if r['cuisine']))
    ratings = [4, 4.5, 5]
    
    context = {
        'restaurants': restaurants,
        'db_restaurants': json.dumps(restaurants),
        'cities': cities,
        'cuisines': cuisines,
        'ratings': ratings,
    }
    
    return render(request, 'pages/index.html', context)
```

---

## 📱 Adapter le CSS existant

### Assurez-vous que les classes CSS existent

```css
/* Ajouter à votre CSS principal */
.restaurant-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    padding: 20px;
}

.restaurant-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.2s;
}

.restaurant-card:hover {
    transform: translateY(-4px);
}

.card-title {
    font-size: 18px;
    font-weight: 600;
    margin: 10px;
}
```

---

## ✅ Vérifier la configuration

### `settings.py`
```python
# S'assurer que MongoDB est configuré
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'mongodb': {
        'ENGINE': 'django_mongodb_backend',
        'NAME': 'dinetunis',
        'HOST': 'mongodb+srv://...',
        'CONNECT': True,
    }
}

# Router
DATABASE_ROUTERS = ['pages.db_router.MongoDBRouter']

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Template engines
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

---

## 🚀 Tester les changements

### Tester les services en Django shell
```bash
python manage.py shell
```

```python
from pages.services import RestaurantService, FilterService
import json

# Tester RestaurantService
restaurants = RestaurantService.get_all_restaurants()
print(f"Total: {len(restaurants)} restaurants")
print(json.dumps(restaurants[0], indent=2))

# Tester FilterService
filters = {'search': 'pizza', 'rating': 4}
filtered = FilterService.filter_restaurants(restaurants, filters)
print(f"Filtrés: {len(filtered)} restaurants")
```

### Tester le frontend
```javascript
// Console du navigateur (F12)
console.log(sidebarFilters)
console.log(sidebarFilters.getFilteredRestaurants())
console.log(localStorage.getItem('dinetunis_filters'))
```

---

## 🔧 Fichiers à mettre à jour

| Fichier | Action | Priorité |
|---------|--------|----------|
| templates/index.html | Ajouter sidebar améliorée | ⭐⭐⭐ |
| templates/restaurant_detail.html | Vérifier compatibilité | ⭐⭐ |
| views_user.py | Passer villes/cuisines | ⭐⭐⭐ |
| static/style.css | Ajouter styles grille | ⭐⭐ |
| settings.py | Vérifier config | ⭐ |

---

## ✨ Résultats après migration

✅ Sidebar 100% fonctionnelle avec filtres avancés
✅ Filtrage en temps réel sans rechargement
✅ Persistance des filtres (localStorage)
✅ Code backend organisé en services
✅ Code frontend modulaire et réutilisable
✅ CSS moderne et responsive
✅ Meilleure maintenabilité

---

**Durée estimée:** 2-3 heures
**Complexité:** Faible-Moyen
**Impact:** Très positif ✨
