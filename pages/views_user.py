# -*- coding: utf-8 -*-
# ============================================================
# Vues Utilisateur - Espace client DineTunis
# ============================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from datetime import date, datetime
import bcrypt
from .models import (
    Restaurant, UserProfile, Review, LoyaltyPoints,
    LoyaltyTransaction, Reservation, Favorite,
    MenuItem, RestaurantGallery, Promotion, MongoUser, SupportMessage
)
from .services import RestaurantService, FavoriteService, ReservationService
from .utils import get_user_restaurant, RESTAURANTS_DATA
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
def presentation(request):
    return render(request, 'pages/presentation.html')


@login_required(login_url='presentation')
def index(request):
    """Page d'accueil avec liste des restaurants approuvés."""
    try:
        # Récupérer tous les restaurants approuvés
        restaurants_data = RestaurantService.get_all_restaurants()
        restaurants_json = json.dumps(restaurants_data)
    except Exception as e:
        print(f"Erreur récupération restaurants: {e}")
        restaurants_data = []
        restaurants_json = "[]"
        
    return render(request, 'pages/index.html', {
        'restaurants': restaurants_data,
        'db_restaurants': restaurants_json
    })


def auth(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        user_type = request.POST.get('user_type', 'user')

        if 'full_name' in request.POST or 'restaurant_name' in request.POST:
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, "Cet email est déjà utilisé.")
                return render(request, 'pages/auth.html')

            if user_type == 'restaurant':
                restaurant_name = request.POST.get('restaurant_name')
                cin = request.POST.get('cin')
                phone = request.POST.get('phone')
                address = request.POST.get('address')

                user = User.objects.create_user(
                    username=email.split('@')[0] + "_" + str(timezone.now().timestamp())[:5],
                    email=email,
                    password=password,
                    first_name=restaurant_name
                )

                UserProfile.objects.using('mongodb').get_or_create(
                    user_id=user.id,
                    defaults={
                        'user_type': 'restaurant',
                        'phone': phone,
                        'address': address
                    }
                )

                Restaurant.objects.using('mongodb').create(
                    user_id=user.id,
                    name=restaurant_name,
                    email=email,
                    phone=phone,
                    cin=cin,
                    address=address,
                    status='pending',
                    is_active=True
                )

                # Hash password with bcrypt
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                MongoUser.objects.using('mongodb').create(
                    email=email,
                    username=user.username,
                    password=hashed.decode('utf-8'),
                    user_type='restaurant',
                    first_name=restaurant_name
                )

                messages.success(request, "✅ Inscription réussie ! Votre compte est en attente d'approbation par l'administrateur.")
                return render(request, 'pages/auth.html')

            else:
                full_name = request.POST.get('full_name')
                names = full_name.split(' ', 1)
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else ""
                
                user = User.objects.create_user(
                    username=email.split('@')[0] + "_" + str(timezone.now().timestamp())[:5],
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                UserProfile.objects.using('mongodb').get_or_create(
                    user_id=user.id,
                    defaults={'user_id': user.id, 'user_type': 'user'}
                )
                
                # Hash password with bcrypt
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                MongoUser.objects.using('mongodb').create(
                    email=email,
                    username=user.username,
                    password=hashed.decode('utf-8'),
                    user_type='user',
                    first_name=first_name,
                    last_name=last_name
                )
                
                login(request, user)
                messages.success(request, "Inscription réussie ! Bienvenue sur DineTunis.")
                return redirect('index')
        else:
            try:
                mongo_user = MongoUser.objects.using('mongodb').filter(email__iexact=email).first()
                
                if mongo_user:
                    # Check password with bcrypt
                    if bcrypt.checkpw(password.encode('utf-8'), mongo_user.password.encode('utf-8')):
                        user, created = User.objects.get_or_create(
                            email=email,
                            defaults={
                                'username': mongo_user.username or email.split('@')[0],
                                'first_name': mongo_user.first_name,
                                'last_name': mongo_user.last_name
                            }
                        )
                        if created:
                            user.set_password(password)
                            user.save()
                        
                        if mongo_user.user_type == 'admin' or user.is_superuser:
                            login(request, user)
                            messages.success(request, "Connexion réussie (Admin) !")
                            return redirect('admin_dashboard_stats')
                        
                        elif mongo_user.user_type == 'restaurant':
                            restaurant = Restaurant.objects.using('mongodb').filter(
                                Q(user_id=user.id) | Q(static_id=user.id)
                            ).first()
                            
                            if restaurant:
                                # Sécurité : vérifier le statut ici
                                if restaurant.status == 'approved':
                                    login(request, user)
                                    messages.success(request, "Connexion réussie !")
                                    return redirect('dashboard')
                                elif restaurant.status == 'rejected':
                                    messages.error(request, "❌ Votre compte restaurant a été rejeté. Veuillez contacter l'administration.")
                                    return render(request, 'pages/auth.html')
                                else:
                                    messages.warning(request, "⏳ Votre compte restaurant est toujours en attente d'approbation par l'administrateur.")
                                    return render(request, 'pages/auth.html')
                            else:
                                messages.error(request, "Erreur: Votre compte restaurant n'est pas configuré.")
                                return render(request, 'pages/auth.html')
                        else:
                            login(request, user)
                            messages.success(request, "Connexion réussie !")
                            return redirect('index')
                    else:
                        messages.error(request, "Mot de passe incorrect")
                else:
                    users = User.objects.filter(email__iexact=email)
                    if users.exists():
                        user = users.first()
                        authenticated_user = authenticate(request, username=user.username, password=password)
                        if authenticated_user:
                            # Vérification des rôles après login SQLite
                            profile = UserProfile.objects.using('mongodb').filter(user_id=authenticated_user.id).first()
                            
                            if authenticated_user.is_superuser or (profile and profile.user_type == 'admin'):
                                login(request, authenticated_user)
                                messages.success(request, "Connexion réussie (Admin) !")
                                return redirect('admin_dashboard_stats')
                                
                            if profile and profile.user_type == 'restaurant':
                                restaurant = Restaurant.objects.using('mongodb').filter(
                                    Q(user_id=authenticated_user.id) | Q(static_id=authenticated_user.id)
                                ).first()
                                if restaurant and restaurant.status == 'approved':
                                    login(request, authenticated_user)
                                    messages.success(request, "Connexion réussie !")
                                    return redirect('dashboard')
                                elif restaurant:
                                    messages.warning(request, "⏳ Votre compte restaurant est en attente d'approbation.")
                                    return render(request, 'pages/auth.html')
                            
                            login(request, authenticated_user)
                            messages.success(request, "Connexion réussie !")
                            return redirect('index')
                        else:
                            messages.error(request, "Mot de passe incorrect")
                    else:
                        messages.error(request, "Aucun compte trouvé avec cet email")

            except Exception as e:
                messages.error(request, f"Erreur: {str(e)}")

            return render(request, 'pages/auth.html')

    return render(request, 'pages/auth.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté")
    return redirect('presentation')


@login_required(login_url='auth')
def mon_compte(request):
    user = request.user

    try:
        reservations_queryset = Reservation.objects.using('mongodb').filter(
            user_id=user.id
        ).order_by('-created_at')
    except:
        reservations_queryset = []

    reservations = []
    for res in reservations_queryset:
        if hasattr(res, 'date'):
            if isinstance(res.date, datetime):
                res.formatted_date = res.date.date().strftime('%d/%m/%Y')
            elif hasattr(res.date, 'strftime'):
                res.formatted_date = res.date.strftime('%d/%m/%Y')
            else:
                res.formatted_date = str(res.date)

        if hasattr(res, 'time'):
            if isinstance(res.time, datetime):
                res.formatted_time = res.time.time().strftime('%H:%M')
            elif hasattr(res.time, 'strftime'):
                res.formatted_time = res.time.strftime('%H:%M')
            else:
                res.formatted_time = str(res.time)

        reservations.append(res)

    favoris_queryset = Favorite.objects.filter(user=user)
    favoris = []
    for fav in favoris_queryset:
        if hasattr(fav, 'created_at') and fav.created_at:
            fav.formatted_date = fav.created_at.strftime('%d/%m/%Y')
        else:
            fav.formatted_date = "Date inconnue"
        favoris.append(fav)

    context = {
        'user': user,
        'reservations': reservations,
        'favoris': favoris,
        'recherches': [],
        'profil_prenom': user.first_name,
        'profil_nom':    user.last_name,
        'profil_email':  user.email,
        'open_section':  'profil',
    }

    return render(request, 'pages/mon_compte.html', context)


@login_required(login_url='auth')
def modifier_profil(request):
    if request.method == 'POST':
        user = request.user
        prenom = request.POST.get('prenom', '').strip()
        nom    = request.POST.get('nom', '').strip()
        email  = request.POST.get('email', '').strip().lower()

        # --- Contrôles de saisie ---
        import re

        def erreur(msg):
            messages.error(request, msg)
            return redirect('mon_compte')

        if not prenom or not nom or not email:
            return erreur("Tous les champs sont obligatoires.")

        if not re.match(r'^[A-Za-zÀ-ÿ\s\-]{2,50}$', prenom):
            return erreur("Le prénom doit contenir uniquement des lettres (2 à 50 caractères).")

        if not re.match(r'^[A-Za-zÀ-ÿ\s\-]{2,50}$', nom):
            return erreur("Le nom doit contenir uniquement des lettres (2 à 50 caractères).")

        if not re.match(r'^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$', email):
            return erreur("L'adresse e-mail n'est pas valide.")

        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            return erreur("Cette adresse e-mail est déjà utilisée par un autre compte.")

        # --- Mise à jour ---
        user.first_name = prenom
        user.last_name  = nom
        user.email      = email
        user.save()
        messages.success(request, "Profil mis à jour avec succès !")
        return redirect('mon_compte')
    return redirect('mon_compte')


@login_required(login_url='auth')
def dashboard(request):
    restaurant = get_user_restaurant(request.user)
    
    if not restaurant:
        messages.error(request, "Vous n'êtes pas associé à un restaurant. Veuillez contacter l'administrateur.")
        return redirect('index')
    
    # Vérification du statut du restaurant
    status = getattr(restaurant, 'status', 'pending')
    if status != 'approved':
        if status == 'rejected':
            messages.error(request, "❌ Votre compte restaurant a été rejeté. Veuillez contacter l'administration.")
        else:
            messages.warning(request, "⏳ Votre compte restaurant est en cours de validation. Vous aurez accès à votre tableau de bord dès son approbation.")
        return redirect('index')
    
    rest_id_value = str(restaurant.pk)

    # GESTION DES MESSAGES DE SUPPORT (RETOUR VERS ADMIN)
    if request.method == 'POST' and 'support_message' in request.POST:
        msg_text = request.POST.get('support_message', '').strip()
        if msg_text:
            SupportMessage.objects.using('mongodb').create(
                sender=request.user,
                restaurant_id=rest_id_value,
                message=msg_text,
                is_from_admin=False
            )
            messages.success(request, "Votre message a été envoyé à l'administrateur.")
            return redirect('dashboard')

    # Récupérer les messages
    support_messages = SupportMessage.objects.using('mongodb').filter(
        restaurant_id=rest_id_value
    ).order_by('created_at')

    context = {
        'restaurant': restaurant,
        'support_messages': support_messages,
    }
    return render(request, 'pages/dashboard.html', context)

@login_required(login_url='auth')
def reserver(request, restaurant_id=None):
    restaurant_name = "Restaurant inconnu"
    if restaurant_id:
        rid = int(restaurant_id)
        if rid in RESTAURANTS_DATA:
            restaurant_name = RESTAURANTS_DATA[rid].get('name', restaurant_name)
        else:
            try:
                r = Restaurant.objects.using('mongodb').filter(Q(static_id=rid) | Q(user_id=rid)).first()
                if r:
                    restaurant_name = r.name
            except:
                pass

    rest_json = "null"
    if restaurant_id:
        try:
            rid = int(restaurant_id)
            r = Restaurant.objects.using('mongodb').filter(Q(static_id=rid) | Q(user_id=rid)).first()
            if r:
                # Récupérer les photos de galerie et choisir une au hasard
                rid = r.static_id or r.user_id or 999
                gallery_images = RestaurantGallery.objects.using('mongodb').filter(restaurant_id=str(rid))
                image = r.image
                if gallery_images.exists():
                    import random
                    img_list = [g.image_url for g in gallery_images]
                    image = random.choice(img_list)
                    
                rest_data = {
                    'id': rid,
                    'name': r.name,
                    'cuisine': r.cuisine_type or 'Autres',
                    'address': r.address or r.city or '',
                    'phone': r.phone or '',
                    'rating': r.rating or 4.0,
                    'hours': f"{r.hours_weekday or '12:00-23:00'}",
                    'image': image or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80"
                }
                rest_json = json.dumps(rest_data)
        except:
            pass

    context = {
        'restaurant_name': restaurant_name,
        'today': date.today(),
        'restaurant_id': restaurant_id,
        'db_restaurant': rest_json,
    }

    if request.method == 'POST':
        reservation_date = request.POST.get('date')
        reservation_time = request.POST.get('time', '19:00')
        guests = request.POST.get('guests', 2)
        special_requests = request.POST.get('special_requests', '')

        try:
            reservation = Reservation(
                user_id=request.user.id,
                user_email=request.user.email,
                user_name=request.user.get_full_name() or request.user.username,
                restaurant_id=restaurant_id or 0,
                restaurant_name=restaurant_name,
                date=datetime.strptime(reservation_date, '%Y-%m-%d').date() if reservation_date else date.today(),
                time=datetime.strptime(reservation_time, '%H:%M').time() if reservation_time else None,
                guests=int(guests),
                special_requests=special_requests,
                status='pending',
            )
            reservation.save(using='mongodb')
            messages.success(
                request,
                f'Réservation pour {guests} personne(s) le {reservation_date} à {reservation_time} confirmée !'
            )
            return redirect('mon_compte')

        except Exception as e:
            messages.error(request, f'Erreur lors de la réservation : {str(e)}')

    return render(request, 'pages/reservation.html', context)


@login_required(login_url='auth')
def loyalty(request):
    # Dictionnaire de codes valides (exemple simple pour les étudiants)
    # Dans la vraie vie, ces codes seraient uniques et stockés en base de données
    VALID_CODES = {
        'DINETUNIS100': 100,
        'BIENVENUE50': 50,
        'REPAS2024': 30,
        'FIDELITE20': 20,
    }

    # 1. Récupérer ou créer les points de l'utilisateur
    try:
        loyalty_points = LoyaltyPoints.objects.using('mongodb').get(user=request.user)
        created = False
    except LoyaltyPoints.DoesNotExist:
        loyalty_points = LoyaltyPoints.objects.using('mongodb').create(
            user=request.user,
            points=0,
            tier='ekoul'
        )
        created = True

    # 2. Gestion si l'utilisateur soumet un code
    if request.method == 'POST':
        code = request.POST.get('loyalty_code', '').strip().upper()
        
        if code in VALID_CODES:
            points_to_add = VALID_CODES[code]
            
            # Vérifier si l'utilisateur a déjà utilisé ce code (pour la démo, on utilise la description de transaction)
            already_used = LoyaltyTransaction.objects.using('mongodb').filter(
                user=request.user, 
                description=f"Code utilisé: {code}"
            ).exists()
            
            if not already_used:
                # Ajouter les points
                loyalty_points.points += points_to_add
                loyalty_points.total_points_earned += points_to_add
                loyalty_points.update_tier()
                loyalty_points.save(using='mongodb')
                
                # Enregistrer la transaction
                LoyaltyTransaction.objects.using('mongodb').create(
                    user=request.user,
                    points=points_to_add,
                    transaction_type='earned',
                    description=f"Code utilisé: {code}"
                )
                
                messages.success(request, f"Félicitations ! Vous avez gagné {points_to_add} points avec le code {code}.")
            else:
                messages.warning(request, "Vous avez déjà utilisé ce code !")
        else:
            messages.error(request, "Code invalide. Veuillez réessayer.")
            
        return redirect('loyalty')

    # 3. Récupérer l'historique des transactions
    transactions = LoyaltyTransaction.objects.using('mongodb').filter(user=request.user).order_by('-created_at')

    # 4. Calculer la progression vers le prochain niveau
    next_tier = "Maximum"
    points_needed = 0
    progress_percent = 100
    
    if loyalty_points.tier == 'ekoul':
        next_tier = "Ekoul Kbir"
        points_needed = 200 - loyalty_points.total_points_earned
        progress_percent = min(100, (loyalty_points.total_points_earned / 200) * 100)
    elif loyalty_points.tier == 'ekoul_kbir':
        next_tier = "Makhmekh"
        points_needed = 500 - loyalty_points.total_points_earned
        progress_percent = min(100, (loyalty_points.total_points_earned / 500) * 100)
    elif loyalty_points.tier == 'makhmekh':
        next_tier = "Makhmekh Kbir"
        points_needed = 1000 - loyalty_points.total_points_earned
        progress_percent = min(100, (loyalty_points.total_points_earned / 1000) * 100)

    # 5. Générer les coupons disponibles selon les points actuels
    available_coupons = []
    pts = loyalty_points.points

    if pts >= 100:
        available_coupons.append({
            'value': '-10 DT',
            'desc': 'Réduction sur votre prochaine addition',
            'code': 'REDUC10DT',
            'cost': 100,
            'icon': 'fas fa-tag',
        })
    if pts >= 250:
        available_coupons.append({
            'value': 'Entrée offerte',
            'desc': 'Une entrée offerte lors de votre visite',
            'code': 'ENTREE250',
            'cost': 250,
            'icon': 'fas fa-utensils',
        })
    if pts >= 500:
        available_coupons.append({
            'value': 'Plat offert',
            'desc': 'Un plat principal offert au choix',
            'code': 'PLAT500',
            'cost': 500,
            'icon': 'fas fa-wine-glass',
        })
    if pts >= 1000:
        available_coupons.append({
            'value': 'Menu dégustation',
            'desc': 'Menu dégustation complet pour 2 personnes',
            'code': 'MENU1000',
            'cost': 1000,
            'icon': 'fas fa-crown',
        })

    # Noms d'affichage des niveaux
    tier_display = {
        'ekoul': 'Ekoul',
        'ekoul_kbir': 'Ekoul Kbir',
        'makhmekh': 'Makhmekh',
        'makhmekh_kbir': 'Makhmekh Kbir',
    }

    context = {
        'loyalty': loyalty_points,
        'transactions': transactions,
        'next_tier': next_tier,
        'points_needed': points_needed if points_needed > 0 else 0,
        'progress_percent': progress_percent,
        'valid_codes_demo': VALID_CODES.keys(),
        'available_coupons': available_coupons,
        'tier_display': tier_display,
        'tier_name': tier_display.get(loyalty_points.tier, loyalty_points.tier),
    }

    return render(request, 'pages/loyalty.html', context)


@login_required(login_url='auth')
def favorites(request):
    favoris = Favorite.objects.filter(user=request.user)
    return render(request, 'pages/favorites.html', {'favoris': favoris})


@login_required(login_url='auth')
def toggle_favorite(request):
    """Ajoute ou supprime un restaurant des favoris."""
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')
        
        if not restaurant_id:
            return JsonResponse({'status': 'error', 'message': 'Missing restaurant_id'}, status=400)
        
        try:
            restaurant = RestaurantService.get_restaurant_by_id(restaurant_id)
            if not restaurant:
                return JsonResponse({'status': 'error', 'message': 'Restaurant not found'}, status=404)
            
            is_added = FavoriteService.toggle_favorite(request.user, restaurant)
            status = 'added' if is_added else 'removed'
            
            return JsonResponse({'status': status})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def is_favorite_api(request, restaurant_id):
    """Vérifie si un restaurant est en favori."""
    if not request.user.is_authenticated:
        return JsonResponse({'is_favorite': False})

    is_favorite = FavoriteService.is_favorite(request.user, restaurant_id)
    return JsonResponse({'is_favorite': is_favorite})


@login_required(login_url='auth')
def restaurant_detail(request, restaurant_id):
    """Affiche les détails d'un restaurant avec son menu et ses avis."""
    rest_json = "null"
    
    try:
        # Récupérer le restaurant
        restaurant = RestaurantService.get_restaurant_by_id(restaurant_id)
        
        if not restaurant:
            messages.error(request, "Restaurant non trouvé.")
            return redirect('index')
        
        restaurant_id = RestaurantService.get_restaurant_id(restaurant)
        
        # Récupérer le menu organisé par catégories
        menu_by_category = RestaurantService.get_restaurant_menu(restaurant_id)
        
        # Formater le menu
        menu = []
        for category, items in menu_by_category.items():
            for item in items:
                menu.append({
                    'name': item.name,
                    'price': f"{item.price} TND",
                    'category': category,
                    'image': item.image_url or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&fit=crop"
                })
        
        # Récupérer les avis
        reviews_data = RestaurantService.get_restaurant_reviews(restaurant_id)
        reviews = []
        for review in reviews_data['reviews']:
            reviews.append({
                'user': review.user.first_name or review.user.username,
                'rating': review.rating,
                'comment': review.comment,
                'date': review.created_at.strftime('%d/%m/%Y')
            })
        
        # Récupérer les promotions actives
        promotions = []
        promotion = RestaurantService.get_active_promotion(restaurant)
        if promotion:
            promotions.append(promotion)
        
        # Formater les données du restaurant
        rest_data = {
            'id': restaurant_id,
            'name': restaurant.name,
            'cuisine': restaurant.cuisine_type or 'Autres',
            'location': restaurant.city or restaurant.address or '',
            'rating': restaurant.rating or 4.0,
            'price': restaurant.price_range or '$$',
            'image': RestaurantService.get_restaurant_image(restaurant),
            'description': restaurant.description or 'Un magnifique restaurant à découvrir.',
            'address': restaurant.address or '',
            'phone': restaurant.phone or '',
            'email': restaurant.email or '',
            'horaires_semaine': restaurant.hours_weekday or '',
            'horaires_samedi': restaurant.hours_saturday or '',
            'horaires_dimanche': restaurant.hours_sunday or '',
            'menu': menu,
            'reviews': reviews,
            'promotions': promotions,
            'average_rating': reviews_data['average_rating']
        }
        rest_json = json.dumps(rest_data)
        
    except Exception as e:
        print(f"Erreur restaurant_detail: {e}")
        messages.error(request, "Erreur lors du chargement du restaurant.")

    return render(request, 'pages/restaurant_detail.html', {
        'restaurant_id': restaurant_id,
        'db_restaurant': rest_json
    })
