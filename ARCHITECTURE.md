# 📋 Documentation de l'Architecture DineTunis

## 🏗️ Structure organisée du Backend

### 1. **Services (services.py)**
Centre du code métier avec quatre services principaux:

#### `RestaurantService`
Gestion complète des restaurants:
- `get_restaurant_id()` - Récupère l'ID primaire
- `get_restaurant_image()` - Image avec fallback (galerie → stockée → défaut)
- `get_active_promotion()` - Promotion actuelle du resto
- `format_restaurant_card()` - Formate pour affichage
- `get_all_restaurants()` - Liste approuvés
- `get_restaurant_by_id()` - Récupère par ID flexible
- `get_restaurant_menu()` - Menu par catégories
- `get_restaurant_reviews()` - Avis + moyenne

#### `FavoriteService`
Gestion des favoris utilisateur:
- `is_favorite()` - Vérification
- `toggle_favorite()` - Ajoute/supprime
- `get_user_favorites()` - Liste des favoris

#### `ReservationService`
Gestion des réservations:
- `create_reservation()` - Crée une réservation
- `get_user_reservations()` - Historique utilisateur
- `get_restaurant_reservations()` - Historique resto
- `update_reservation_status()` - Change le statut

#### `FilterService`
Filtrage avancé avec:
- `filter_restaurants()` - Filtre multi-critères
- Gestion budget, ville, cuisine, note

### 2. **Modèles (models.py)**
Structure claire avec 13 modèles:
- **Restaurant** - Infos resto + statuts
- **UserProfile** - Profil utilisateur
- **LoyaltyPoints** - Points fidélité avec tiers
- **LoyaltyTransaction** - Historique points
- **Review** - Avis utilisateurs
- **LoyaltyReward** - Récompenses disponibles
- **UserRedemption** - Échanges utilisateur
- **Reservation** - Réservations avec statuts
- **Favorite** - Restaurants favoris
- **MenuItem** - Menu par catégories
- **RestaurantGallery** - Photos galerie
- **Promotion** - Promotions actives
- **MongoUser** - Collection MongoDB user
- **SupportMessage** - Messages support

### 3. **Vues (views_*.py)**
Organisées par rôle:

#### `views_user.py`
- `index()` - Accueil avec RestaurantService
- `auth()` - Inscription/connexion
- `restaurant_detail()` - Détails avec services
- `toggle_favorite()` - Favoris simple
- `is_favorite_api()` - API favoris
- `favorites()` - Page favoris
- `mon_compte()` - Espace utilisateur
- `modifier_profil()` - Editer profil
- `reserver()` - Créer réservation
- `dashboard()` - Tableau bord resto
- `loyalty()` - Page fidélité

#### `views_restaurant.py`
- APIs pour restaurants propriétaires
- Menu management
- Réservations
- Galerie
- Promotions

#### `views_admin.py`
- Gestion des restaurants
- Gestion des utilisateurs
- Modération des avis
- Fidélité
- Stats dashboard

#### `views.py`
- Autres routes générales

### 4. **Frontend (static/)**

#### `filters.js` ⭐ **NOUVEAU**
Classe `SidebarFilters`:
```javascript
// Initialisation
const filters = new SidebarFilters(restaurantsData);

// API
filters.applyFilters()          // Applique filtres
filters.resetFilters()          // Réinitialise
filters.getFilteredRestaurants() // Récupère résultats
filters.updateRestaurantsData()  // Maj données
filters.getCurrentFilters()      // État filters
```

**Fonctionnalités:**
- ✅ Recherche texte en temps réel
- ✅ Filtres par ville, cuisine
- ✅ Filtre note (radio buttons)
- ✅ Curseur budget interactif
- ✅ Sauvegarde filtres (localStorage)
- ✅ Compteur résultats
- ✅ Message quand aucun résultat

#### `filters.css` ⭐ **NOUVEAU**
Styles modernes:
- Checkboxes personnalisées
- Radio buttons stylisés
- Curseur budget coloré
- Messages vides animés
- Responsive design

#### `script.js`
- Fonctions utilisées par HTML
- Compatibilité avec ancien code

## 🔄 Flux Utilisateur

```
1. Accueil (index) 
   ↓ Charge RestaurantService.get_all_restaurants()
   ↓ Affiche cards + SidebarFilters JavaScript
   
2. Filtrage (sidebar)
   ↓ SidebarFilters.applyFilters()
   ↓ Filtre côté client
   ↓ Affiche/masque cartes
   
3. Détails resto (restaurant_detail)
   ↓ Charge RestaurantService + menu + avis
   ↓ Affiche infos complètes
   
4. Favoris (toggle_favorite)
   ↓ FavoriteService.toggle_favorite()
   ↓ Ajoute/supprime de favoris
   
5. Réservation (reserver)
   ↓ ReservationService.create_reservation()
   ↓ Sauvegarde en base
```

## 📊 Base de Données

**Hybride:** PostgreSQL + MongoDB

| Modèle | DB | Collection |
|--------|-----|-----------|
| Restaurant | MongoDB | restaurant |
| UserProfile | MongoDB | profile |
| Loyality* | MongoDB | loyalty* |
| Review | MongoDB | review |
| Reservation | MongoDB | reservation |
| Favorite | MongoDB | favorite |
| MenuItem | MongoDB | menuitem |
| RestaurantGallery | MongoDB | gallery |
| Promotion | MongoDB | promotion |
| MongoUser | MongoDB | user |
| SupportMessage | MongoDB | support_messages |
| User (Django) | PostgreSQL | auth_user |

## 🚀 Bonnes Pratiques

### Backend
```python
# ❌ AVANT: Code dupliqué
def index(request):
    # 50 lignes de logique
    
# ✅ APRÈS: Utilise services
def index(request):
    data = RestaurantService.get_all_restaurants()
    return render(request, 'index.html', {'restaurants': data})
```

### Frontend
```javascript
// ❌ AVANT: Fonctions globals
function filtrerRestaurants() { ... }

// ✅ APRÈS: Classe organisée
const filters = new SidebarFilters();
filters.applyFilters();
filters.resetFilters();
```

## 🔧 Maintenance

### Ajouter une fonctionnalité
1. Créer la logique dans `services.py`
2. L'utiliser dans `views_*.py`
3. Créer l'endpoint/template
4. Ajouter JS si nécessaire

### Exemple: Ajouter filtre budget
```python
# services.py
class FilterService:
    @staticmethod
    def filter_by_budget(restaurants, max_budget):
        return [r for r in restaurants if get_price(r) <= max_budget]

# views_user.py
filtered = FilterService.filter_by_budget(restaurants, request.GET.get('budget'))

# filters.js
applyFilters() {
    // Récupère budget du slider
    const budget = this.currentFilters.budget;
    // Filtre appliqué
}
```

## 📈 Performance

- **Services** réduisent requêtes dupliquées
- **Filtrage côté client** (JS) = 0 hit serveur
- **Sauvegarde localStorage** = pas de rechargement filters
- **Images lazy-loaded** = chargement + rapide

## 🐛 Debugging

### Logs
```python
print(f"Erreur: {e}")  # Backend
console.log(sidebarFilters.getCurrentFilters())  # Frontend
```

### Tests
```bash
# Vérifier services
python manage.py shell
>>> from pages.services import RestaurantService
>>> RestaurantService.get_all_restaurants()

# Vérifier JS
sidebarFilters.getFilteredRestaurants()
```

---

**Dernier update:** Mai 2026  
**Version:** 2.0 (Refactored)  
**Status:** ✅ Stable
