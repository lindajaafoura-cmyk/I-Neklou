
import random
from datetime import date
from django.utils import timezone
from django.db.models import Q, Avg, Count
from .models import (
    Restaurant, RestaurantGallery, Promotion,
    Review, Reservation, Favorite, MenuItem
)

# ============================================================
# Service Restaurants
# ============================================================

class RestaurantService:
    """Gestion des restaurants et de leurs données."""
    
    RESTAURANTS_DATA_FALLBACK = {
        1001: {"name": "El Mida", "image": "https://images.unsplash.com/photo-1544148103-0773bf10d330?w=800&q=80"},
        1002: {"name": "Le Golfe", "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2a/5b/3c/7a/caption.jpg?w=1400&h=800&s=1"},
        1003: {"name": "Dar El Jeld", "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/12/24/4a/36/au-coeur-de-la-medina.jpg?w=1800&h=1000&s=1"},
        1004: {"name": "Bella Napoli", "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1c/19/fe/9d/bella-napoli.jpg?w=1400&h=-1&s=1"},
        1005: {"name": "The Creek", "image": "https://lh3.googleusercontent.com/p/AF1QipPOpWVJf5Ss7S2R1_g0bv3-5NGtzNuTl3JZJ6JP=s1360-w1360-h1020-rw"},
        1006: {"name": "Fondouk El Attarine", "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/11/fb/75/c9/photo8jpg.jpg?w=2000&h=-1&s=1"},
        1007: {"name": "La Salle à Manger", "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2f/ad/8e/9b/la-terasse-espace-fumeur.jpg?w=1400&h=-1&s=1"},
        1008: {"name": "Boragó", "image": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=800&q=80"},
        1009: {"name": "Bab Tounès", "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2e/e0/a5/85/caption.jpg?w=1100&h=-1&s=1"},
    }
    
    @staticmethod
    def get_restaurant_id(restaurant):
        """Retourne l'ID primaire du restaurant."""
        return restaurant.static_id or restaurant.user_id or restaurant.id
    
    @staticmethod
    def get_restaurant_image(restaurant):
        """Récupère l'image du restaurant (galerie > image stockée > fallback)."""
        # D'abord chercher dans la galerie
        gallery = RestaurantGallery.objects.using('mongodb').filter(
            restaurant_id=str(RestaurantService.get_restaurant_id(restaurant))
        )
        
        if gallery.exists():
            images = [g.image_url for g in gallery]
            return random.choice(images)
        
        # Sinon retourner l'image stockée
        if restaurant.image:
            return restaurant.image
        
        # Fallback depuis le dictionnaire statique
        rid = RestaurantService.get_restaurant_id(restaurant)
        if rid in RestaurantService.RESTAURANTS_DATA_FALLBACK:
            return RestaurantService.RESTAURANTS_DATA_FALLBACK[rid]['image']
        
        # Image par défaut
        return "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80"
    
    @staticmethod
    def get_active_promotion(restaurant):
        """Retourne la promotion la plus importante du restaurant (s'il y en a une)."""
        restaurant_id = str(RestaurantService.get_restaurant_id(restaurant))
        today = timezone.now().date()
        
        # Chercher les promotions actives
        promotions = Promotion.objects.using('mongodb').filter(
            restaurant_id=restaurant_id,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).order_by('-discount_percentage')
        
        if not promotions.exists():
            return None
        
        promo = promotions.first()
        return {
            'title': promo.title,
            'discount': promo.discount_percentage,
            'description': (promo.description[:50] + '...' 
                          if len(promo.description) > 50 
                          else promo.description)
        }
    
    @staticmethod
    def format_restaurant_card(restaurant):
        """Formate un restaurant pour l'affichage sur une carte."""
        return {
            'id': RestaurantService.get_restaurant_id(restaurant),
            'name': restaurant.name,
            'cuisine': restaurant.cuisine_type or 'Autres',
            'location': restaurant.city or '',
            'rating': restaurant.rating or 4.0,
            'price': restaurant.price_range or '$$',
            'image': RestaurantService.get_restaurant_image(restaurant),
            'description': (
                (restaurant.description[:100] + '...')
                if restaurant.description and len(restaurant.description) > 100
                else (restaurant.description or 'Un magnifique restaurant à découvrir.')
            ),
            'promotion': RestaurantService.get_active_promotion(restaurant)
        }
    
    @staticmethod
    def get_all_restaurants():
        """Récupère tous les restaurants approuvés formatés."""
        restaurants = Restaurant.objects.using('mongodb').filter(status='approved')
        return [RestaurantService.format_restaurant_card(r) for r in restaurants]
    
    @staticmethod
    def get_restaurant_by_id(restaurant_id):
        """Récupère un restaurant par son ID."""
        try:
            # Essayer plusieurs formats d'ID
            restaurant = (Restaurant.objects.using('mongodb').filter(id=restaurant_id).first() or
                        Restaurant.objects.using('mongodb').filter(static_id=restaurant_id).first() or
                        Restaurant.objects.using('mongodb').filter(user_id=int(restaurant_id)).first())
            return restaurant
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def get_restaurant_menu(restaurant_id):
        """Récupère le menu d'un restaurant."""
        menu = MenuItem.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id)
        ).values('category').annotate(items=Count('id')).order_by('category')
        
        items_by_category = {}
        for cat in menu:
            items = MenuItem.objects.using('mongodb').filter(
                restaurant_id=str(restaurant_id),
                category=cat['category']
            ).order_by('name')
            items_by_category[cat['category']] = items
        
        return items_by_category
    
    @staticmethod
    def get_restaurant_reviews(restaurant_id):
        """Récupère les avis d'un restaurant."""
        reviews = Review.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id),
            status='approved'
        ).order_by('-created_at')
        
        return {
            'reviews': reviews,
            'count': reviews.count(),
            'average_rating': reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        }


# ============================================================
# Service Favoris
# ============================================================

class FavoriteService:
    """Gestion des restaurants favoris de l'utilisateur."""
    
    @staticmethod
    def is_favorite(user, restaurant_id):
        """Vérifie si un restaurant est en favori."""
        return Favorite.objects.using('mongodb').filter(
            user=user,
            restaurant_id=str(restaurant_id)
        ).exists()
    
    @staticmethod
    def toggle_favorite(user, restaurant):
        """Ajoute ou supprime un restaurant des favoris."""
        restaurant_id = str(RestaurantService.get_restaurant_id(restaurant))
        
        favorite = Favorite.objects.using('mongodb').filter(
            user=user,
            restaurant_id=restaurant_id
        ).first()
        
        if favorite:
            favorite.delete()
            return False
        else:
            Favorite.objects.using('mongodb').create(
                user=user,
                restaurant_id=restaurant_id,
                restaurant_name=restaurant.name,
                restaurant_image=RestaurantService.get_restaurant_image(restaurant),
                cuisine=restaurant.cuisine_type,
                rating=str(restaurant.rating),
                location=restaurant.city
            )
            return True
    
    @staticmethod
    def get_user_favorites(user):
        """Récupère tous les favoris de l'utilisateur."""
        return Favorite.objects.using('mongodb').filter(user=user).order_by('-created_at')


# ============================================================
# Service Réservations
# ============================================================

class ReservationService:
    """Gestion des réservations."""
    
    @staticmethod
    def create_reservation(user, restaurant, reservation_data):
        """Crée une nouvelle réservation."""
        return Reservation.objects.using('mongodb').create(
            user_id=user.id,
            user_email=user.email,
            user_name=f"{user.first_name} {user.last_name}".strip(),
            restaurant_id=str(RestaurantService.get_restaurant_id(restaurant)),
            restaurant_name=restaurant.name,
            date=reservation_data['date'],
            time=reservation_data['time'],
            guests=reservation_data['guests'],
            special_requests=reservation_data.get('special_requests', ''),
            status='pending'
        )
    
    @staticmethod
    def get_user_reservations(user):
        """Récupère les réservations d'un utilisateur."""
        return Reservation.objects.using('mongodb').filter(
            user_id=user.id
        ).order_by('-created_at')
    
    @staticmethod
    def get_restaurant_reservations(restaurant_id):
        """Récupère les réservations d'un restaurant."""
        return Reservation.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id)
        ).order_by('-created_at')
    
    @staticmethod
    def update_reservation_status(reservation_id, new_status):
        """Met à jour le statut d'une réservation."""
        reservation = Reservation.objects.using('mongodb').get(id=reservation_id)
        reservation.status = new_status
        reservation.save(using='mongodb')
        return reservation


# ============================================================
# Service Filtrage
# ============================================================

class FilterService:
    """Logique de filtrage avancée des restaurants."""
    
    BUDGET_MAPPING = {'$': 30, '$$': 80, '$$$': 150, '$$$$': 200}
    
    @staticmethod
    def filter_restaurants(restaurants_data, filters):
        """
        Filtre une liste de restaurants selon les critères donnés.
        
        filters: {
            'search': str (optionnel),
            'cities': list (optionnel),
            'cuisines': list (optionnel),
            'rating': int (optionnel, 0-5),
            'budget_max': int (optionnel)
        }
        """
        if not filters:
            return restaurants_data
        
        search = (filters.get('search') or '').lower().strip()
        cities = [c.lower() for c in (filters.get('cities') or [])]
        cuisines = [c.lower() for c in (filters.get('cuisines') or [])]
        rating = filters.get('rating', 0)
        budget_max = filters.get('budget_max', 200)
        
        filtered = []
        
        for restaurant in restaurants_data:
            # Filtre recherche texte
            if search:
                match_name = search in restaurant['name'].lower()
                match_cuisine = search in restaurant['cuisine'].lower()
                match_location = search in restaurant['location'].lower()
                if not (match_name or match_cuisine or match_location):
                    continue
            
            # Filtre ville
            if cities and restaurant['location'].lower() not in cities:
                continue
            
            # Filtre cuisine
            if cuisines and restaurant['cuisine'].lower() not in cuisines:
                if 'autres' not in cuisines or restaurant['cuisine'].lower() != 'autres':
                    if not any(c in restaurant['cuisine'].lower() for c in cuisines):
                        continue
            
            # Filtre note
            if rating > 0 and int(restaurant['rating']) != rating:
                continue
            
            # Filtre budget
            restaurant_budget = FilterService.BUDGET_MAPPING.get(
                restaurant['price'], 0
            )
            if restaurant_budget > budget_max:
                continue
            
            filtered.append(restaurant)
        
        return filtered


# ============================================================
# Service Dashboard Restaurant
# ============================================================

class RestaurantDashboardService:
    """Gestion du dashboard du restaurant propriétaire."""
    
    @staticmethod
    def get_recent_reservations(restaurant_id, limit=20):
        """Récupère les réservations récentes."""
        reservations = Reservation.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id)
        ).order_by('-created_at')[:limit]
        
        formatted = []
        for res in reservations:
            formatted.append({
                'id': str(res.id),
                'name': res.user_name,
                'persons': res.guests,
                'time': res.time.strftime('%H:%M') if hasattr(res.time, 'strftime') else str(res.time),
                'date': res.date.strftime('%Y-%m-%d') if hasattr(res.date, 'strftime') else str(res.date),
                'status': res.status,
                'status_display': res.get_status_display_fr() if hasattr(res, 'get_status_display_fr') else res.status
            })
        
        return formatted
    
    @staticmethod
    def get_recent_reviews(restaurant_id, limit=10):
        """Récupère les avis récents."""
        reviews = Review.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id)
        ).order_by('-created_at')[:limit]
        
        formatted = []
        for review in reviews:
            formatted.append({
                'id': str(review.id),
                'user': review.user.get_full_name() or review.user.username,
                'rating': review.rating,
                'comment': review.comment,
                'reply': review.restaurant_reply,
                'date': review.created_at.strftime('%Y-%m-%d'),
                'avatar': f'https://i.pravatar.cc/150?u={review.user.id}',
                'status': review.status,
                'verified': review.is_verified
            })
        
        return formatted
    
    @staticmethod
    def get_menu_items(restaurant_id):
        """Récupère les items du menu."""
        items = MenuItem.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id)
        ).order_by('category', 'name')
        
        formatted = []
        for item in items:
            formatted.append({
                'id': str(item.id),
                'name': item.name,
                'price': f"{item.price} TND",
                'category': item.category,
                'description': item.description,
                'image': item.image_url or '',
                'available': item.is_available
            })
        
        return formatted
    
    @staticmethod
    def get_gallery(restaurant_id):
        """Récupère la galerie photos."""
        gallery = RestaurantGallery.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id)
        ).order_by('-created_at')
        
        formatted = []
        for photo in gallery:
            formatted.append({
                'id': str(photo.id),
                'url': photo.image_url,
                'caption': photo.caption or '',
                'date': photo.created_at.strftime('%Y-%m-%d')
            })
        
        return formatted
    
    @staticmethod
    def get_promotions(restaurant_id):
        """Récupère les promotions actives."""
        promotions = Promotion.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id),
            is_active=True
        ).order_by('-discount_percentage')
        
        formatted = []
        today = timezone.now().date()
        
        for promo in promotions:
            days_left = (promo.end_date - today).days if promo.end_date else 0
            status = 'active'
            if days_left <= 3:
                status = 'ending'
            elif days_left < 0:
                status = 'expired'
            
            formatted.append({
                'id': str(promo.id),
                'title': promo.title,
                'description': promo.description,
                'discount': f"-{promo.discount_percentage}%",
                'status': status,
                'end_date': promo.end_date.strftime('%Y-%m-%d') if promo.end_date else None,
                'days_left': days_left
            })
        
        return formatted
    
    @staticmethod
    def get_dashboard_stats(restaurant_id):
        """Récupère les statistiques du dashboard."""
        today = timezone.now().date()
        this_month = timezone.now().replace(day=1).date()
        
        # Réservations
        total_reservations = Reservation.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id)
        ).count()
        
        today_reservations = Reservation.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id),
            date=today
        ).count()
        
        confirmed_reservations = Reservation.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id),
            status='confirmed'
        ).count()
        
        # Avis
        reviews = Review.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id)
        )
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Menu
        menu_count = MenuItem.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id)
        ).count()
        
        # Promotions actives
        promotions_count = Promotion.objects.using('mongodb').filter(
            restaurant_id=str(restaurant_id),
            is_active=True
        ).count()
        
        return {
            'total_reservations': total_reservations,
            'today_reservations': today_reservations,
            'confirmed_reservations': confirmed_reservations,
            'average_rating': round(avg_rating, 1),
            'reviews_count': reviews.count(),
            'menu_items_count': menu_count,
            'active_promotions': promotions_count
        }

