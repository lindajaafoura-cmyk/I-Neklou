# 🍽️ DineTunis - Guide Complet d'Utilisation et Maintenance

## 📚 Table des matières
1. [Architecture](#architecture)
2. [Installation](#installation)
3. [Services Backend](#services-backend)
4. [Filtrage Frontend](#filtrage-frontend)
5. [Dépannage](#dépannage)
6. [Bonnes pratiques](#bonnes-pratiques)

---

## 🏗️ Architecture

Le projet est organisé en **3 couches**:

```
┌─────────────────────────────────┐
│  Templates HTML (Django)        │
├─────────────────────────────────┤
│  Views (views_*.py)             │
├─────────────────────────────────┤
│  Services (services.py)         │
├─────────────────────────────────┤
│  Modèles (models.py)            │
├─────────────────────────────────┤
│  Base de données (MongoDB/PG)   │
└─────────────────────────────────┘
```

### Fichiers clés:
- **`services.py`** - Logique métier centralisée ⭐
- **`views_user.py`** - Pages utilisateur
- **`views_restaurant.py`** - Dashboard restaurants
- **`views_admin.py`** - Panel administrateur
- **`static/filters.js`** - Filtrage sidebar ⭐
- **`static/filters.css`** - Styles filtres ⭐

---

## 💾 Installation & Setup

### 1. Cloner & installer dépendances
```bash
cd DineTunis
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Migrations
```bash
python manage.py migrate
```

### 3. Créer compte admin
```bash
python manage.py createsuperuser
```

### 4. Lancer serveur
```bash
python manage.py runserver
# Accès: http://localhost:8000
```

---

## 🔧 Services Backend (NEW)

### RestaurantService
Centre de gestion des restaurants:

#### Récupérer tous les restaurants
```python
from pages.services import RestaurantService

# Tous les restaurants approuvés formatés
restaurants = RestaurantService.get_all_restaurants()
# Retour: [{'id': 1, 'name': 'El Mida', 'rating': 4.5, ...}]
```

#### Récupérer un restaurant
```python
restaurant = RestaurantService.get_restaurant_by_id(1)
# Handles: id, static_id, user_id
```

#### Obtenir l'image du restaurant
```python
image = RestaurantService.get_restaurant_image(restaurant)
# Stratégie: Galerie → Stockée → Fallback
```

#### Obtenir la promotion active
```python
promo = RestaurantService.get_active_promotion(restaurant)
# Retour: {'title': '...', 'discount': 20, ...} ou None
```

#### Formater une carte restaurant
```python
card_data = RestaurantService.format_restaurant_card(restaurant)
# Retour: Objet JSON prêt pour le frontend
```

---

### FavoriteService
Gestion simple des favoris:

```python
from pages.services import FavoriteService

# Vérifier si favori
is_fav = FavoriteService.is_favorite(user, restaurant_id)

# Ajouter/supprimer favori
is_added = FavoriteService.toggle_favorite(user, restaurant)

# Récupérer tous les favoris
favs = FavoriteService.get_user_favorites(user)
```

---

### ReservationService
Gestion des réservations:

```python
from pages.services import ReservationService

# Créer réservation
data = {
    'date': '2026-05-15',
    'time': '20:00',
    'guests': 4,
    'special_requests': 'Sans oignons'
}
reservation = ReservationService.create_reservation(user, restaurant, data)

# Récupérer réservations utilisateur
user_reservations = ReservationService.get_user_reservations(user)

# Récupérer réservations restaurant
rest_reservations = ReservationService.get_restaurant_reservations(restaurant_id)

# Changer statut
ReservationService.update_reservation_status(res_id, 'confirmed')
```

---

### FilterService
Filtrage avancé côté serveur:

```python
from pages.services import FilterService

restaurants_data = RestaurantService.get_all_restaurants()

filters = {
    'search': 'pizza',
    'cities': ['tunis', 'sfax'],
    'cuisines': ['italienne'],
    'rating': 4,
    'budget_max': 100
}

filtered = FilterService.filter_restaurants(restaurants_data, filters)
```

---

### RestaurantDashboardService
Dashboard du propriétaire:

```python
from pages.services import RestaurantDashboardService

restaurant_id = 1

# Réservations récentes
reservations = RestaurantDashboardService.get_recent_reservations(restaurant_id)

# Avis récents
reviews = RestaurantDashboardService.get_recent_reviews(restaurant_id)

# Menu
menu = RestaurantDashboardService.get_menu_items(restaurant_id)

# Galerie
gallery = RestaurantDashboardService.get_gallery(restaurant_id)

# Promotions
promos = RestaurantDashboardService.get_promotions(restaurant_id)

# Statistiques
stats = RestaurantDashboardService.get_dashboard_stats(restaurant_id)
# Retour: {total_reservations, avg_rating, reviews_count, ...}
```

---

## 🎨 Filtrage Frontend (JavaScript)

### Classe SidebarFilters
Gestion complète des filtres côté client:

#### Initialisation
```html
<!-- HTML: Charger data dans data-restaurants -->
<div id="restaurantsGrid" data-restaurants='{{ db_restaurants|escapejs }}'>
    <!-- Cards vont ici -->
</div>

<script src="{% static 'filters.js' %}"></script>
```

```javascript
// JavaScript s'initialise automatiquement
// OU initialiser manuellement:
const filters = new SidebarFilters(restaurantsData);
```

#### API
```javascript
// Appliquer filtres
filters.applyFilters();

// Réinitialiser
filters.resetFilters();

// Récupérer restaurants filtrés
const filtered = filters.getFilteredRestaurants();

// Obtenir état filters
const current = filters.getCurrentFilters();
// Retour: {search: '...', cities: [...], rating: 0, budget: 200}

// Mettre à jour données
filters.updateRestaurantsData(newData);
```

#### Événements
```javascript
// Les checkboxes se lient automatiquement:
// - .filter-ville
// - .filter-cuisine
// - input[name="rating"]
// - #priceSlider
// - #searchInput
// - #resetFiltersBtn
```

#### Sauvegarde automatique
```javascript
// Les filtres se sauvegardent dans localStorage
// Récupérés automatiquement au rechargement
localStorage.getItem('dinetunis_filters')
```

---

## 🎯 Exemples d'utilisation

### Backend: Afficher restaurants avec recherche
```python
# views_user.py
from pages.services import RestaurantService, FilterService

def index(request):
    # Obtenir tous les restaurants
    restaurants = RestaurantService.get_all_restaurants()
    
    # Appliquer filtres si demandé (côté serveur)
    search = request.GET.get('q', '')
    if search:
        filters = {'search': search}
        restaurants = FilterService.filter_restaurants(restaurants, filters)
    
    return render(request, 'index.html', {
        'restaurants': restaurants,
        'db_restaurants': json.dumps(restaurants)
    })
```

### Frontend: Initialiser filtres
```html
<!-- templates/index.html -->
<div class="container">
    <aside class="sidebar">
        <!-- Checkboxes, sliders, etc. -->
        <input type="text" id="searchInput" placeholder="Rechercher...">
        <label>
            <input type="checkbox" class="filter-ville" value="tunis">
            Tunis
        </label>
        <input type="range" id="priceSlider" min="0" max="200" value="200">
        <button id="resetFiltersBtn">Réinitialiser</button>
    </aside>

    <div id="restaurantsGrid" data-restaurants='{{ db_restaurants|escapejs }}'>
        {% for rest in restaurants %}
        <div class="restaurant-card" data-id="{{ rest.id }}" 
             data-cuisine="{{ rest.cuisine }}" data-ville="{{ rest.location }}">
            <!-- Card content -->
        </div>
        {% endfor %}
    </div>
</div>

<link rel="stylesheet" href="{% static 'filters.css' %}">
<script src="{% static 'filters.js' %}"></script>
```

---

## 🐛 Dépannage

### Problème: Restaurants ne s'affichent pas
```python
# Vérifier
>>> from pages.services import RestaurantService
>>> restaurants = RestaurantService.get_all_restaurants()
>>> len(restaurants)  # Doit être > 0

# Vérifier la base de données
>>> from pages.models import Restaurant
>>> Restaurant.objects.using('mongodb').filter(status='approved').count()
```

### Problème: Filtres ne fonctionnent pas
```javascript
// Console browser (F12)
console.log(sidebarFilters)  // Doit exister
console.log(sidebarFilters.getFilteredRestaurants())  // Vérifier résultats
```

### Problème: Images ne chargent pas
```python
# Vérifier la galerie
>>> from pages.models import RestaurantGallery
>>> RestaurantGallery.objects.using('mongodb').filter(restaurant_id='1').count()

# Vérifier les URLs
>>> from pages.services import RestaurantService
>>> r = Restaurant.objects.using('mongodb').get(id='1')
>>> img = RestaurantService.get_restaurant_image(r)
>>> print(img)  # Doit retourner une URL valide
```

---

## ✅ Bonnes pratiques

### ❌ À éviter
```python
# Code dupliqué dans views
def index(request):
    restaurants = Restaurant.objects.using('mongodb').filter(status='approved')
    # ... 30 lignes de logique ...
    return render(request, 'index.html', {'restaurants': formatted})

def dashboard(request):
    restaurants = Restaurant.objects.using('mongodb').filter(status='approved')
    # ... Mêmes 30 lignes ...
    return render(request, 'dashboard.html', {'restaurants': formatted})
```

### ✅ À faire
```python
# Utiliser services
from pages.services import RestaurantService

def index(request):
    restaurants = RestaurantService.get_all_restaurants()
    return render(request, 'index.html', {'restaurants': restaurants})

def dashboard(request):
    restaurants = RestaurantService.get_all_restaurants()
    return render(request, 'dashboard.html', {'restaurants': restaurants})
```

### Ajouter une nouvelle fonctionnalité

**Étape 1:** Créer la logique dans `services.py`
```python
class RestaurantService:
    @staticmethod
    def get_restaurants_by_rating(min_rating=4.0):
        restaurants = Restaurant.objects.using('mongodb').filter(
            status='approved',
            rating__gte=min_rating
        )
        return [RestaurantService.format_restaurant_card(r) for r in restaurants]
```

**Étape 2:** L'utiliser dans `views_user.py`
```python
def top_rated(request):
    restaurants = RestaurantService.get_restaurants_by_rating(4.5)
    return render(request, 'top_rated.html', {'restaurants': restaurants})
```

**Étape 3:** Créer le template
```html
<!-- templates/top_rated.html -->
{% for rest in restaurants %}
<div class="restaurant-card">{{ rest.name }}</div>
{% endfor %}
```

---

## 📊 Structure de la base de données

### Collections MongoDB
```
restaurant          - Infos restaurants
profile            - Profils utilisateurs
review             - Avis
reservation        - Réservations
favorite           - Favoris
menuitem           - Items menu
gallery            - Photos galerie
promotion          - Promotions
user               - Utilisateurs MongoDB
loyalty_*          - Points fidélité
support_messages   - Messages support
```

### Table PostgreSQL
```
auth_user          - Utilisateurs Django
```

---

## 🚀 Déploiement

### Checklist avant production
- [ ] `DEBUG = False` dans `settings.py`
- [ ] Vérifier `ALLOWED_HOSTS`
- [ ] Vérifier `DATABASES` config
- [ ] `python manage.py collectstatic`
- [ ] Tester services backend
- [ ] Tester filtres frontend

### Lancer en production
```bash
# Avec Gunicorn
gunicorn DineTunis.wsgi --bind 0.0.0.0:8000

# Avec Nginx
# Voir config Nginx séparée
```

---

## 📞 Support

En cas de problème:
1. Consulter `ARCHITECTURE.md` pour la structure
2. Vérifier les logs: `python manage.py` output
3. Vérifier la console du navigateur (F12)
4. Tester les services en Django shell

---

**Dernière mise à jour:** Mai 2026  
**Version:** 2.0 - Refactored  
**Maintenance:** Bien organisée ✅
