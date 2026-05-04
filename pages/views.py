# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum, Avg
from datetime import date, timedelta, datetime
from .models import (
    Restaurant, UserProfile, Review, LoyaltyPoints,
    LoyaltyTransaction, Reservation, Favorite,
    MenuItem, RestaurantGallery, Promotion, SupportMessage, MongoUser
)
from functools import wraps
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json

RESTAURANTS_DATA = {
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


def is_superadmin(user):
    if user.is_superuser:
        return True
    try:
        profile = UserProfile.objects.using('mongodb').filter(user=user).first()
        if profile and profile.user_type == 'admin':
            return True
    except:
        pass
    try:
        mongouser = MongoUser.objects.using('mongodb').filter(email__iexact=user.email).first()
        if mongouser and mongouser.user_type == 'admin':
            return True
    except:
        pass
    return False


def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth')
        if not is_superadmin(request.user):
            messages.error(request, "Accès refusé. Vous devez être administrateur.")
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_user_restaurant(user):
    try:
        return Restaurant.objects.using('mongodb').filter(user_id=user.id).first()
    except:
        return None

def presentation(request):
    return render(request, 'pages/presentation.html')


@login_required(login_url='presentation')
def index(request):
    try:
        qs = Restaurant.objects.using('mongodb').filter(status='approved') 
        rests_list = []
        for r in qs:
            # Récupérer les photos de galerie et choisir une au hasard
            rid = r.static_id or r.user_id or 999
            gallery_images = RestaurantGallery.objects.using('mongodb').filter(restaurant_id=str(rid))
            img = r.image
            
            if gallery_images.exists():
                import random
                img_list = [g.image_url for g in gallery_images]
                img = random.choice(img_list)
            # Fallback image depuis RESTAURANTS_DATA si pas de galerie
            elif not img and rid in RESTAURANTS_DATA:
                img = RESTAURANTS_DATA[rid]['image']
            
            # Récupérer les promotions actives pour ce restaurant
            from django.utils import timezone
            today = timezone.now().date()
            
            # Essayer avec différents formats d'ID
            possible_ids = [str(r.id), str(rid)]
            if r.static_id:
                possible_ids.append(str(r.static_id))
            if r.user_id:
                possible_ids.append(str(r.user_id))
            
            # Supprimer les doublons et les valeurs None
            possible_ids = list(set([pid for pid in possible_ids if pid and pid != 'None']))
            
            active_promotions = []
            for pid in possible_ids:
                promos = Promotion.objects.using('mongodb').filter(
                    restaurant_id=pid,
                    is_active=True,
                    start_date__lte=today,
                    end_date__gte=today
                ).order_by('-discount_percentage')
                if promos.exists():
                    active_promotions.extend(promos)
                    break
            
            promo_data = None
            if active_promotions:
                promo = active_promotions[0]
                promo_data = {
                    'title': promo.title,
                    'discount': promo.discount_percentage,
                    'description': promo.description[:50] + '...' if len(promo.description) > 50 else promo.description
                }
            
            rests_list.append({
                'id': rid,
                'name': r.name,
                'cuisine': r.cuisine_type or 'Autres',
                'location': r.city or '',
                'rating': r.rating or 4.0,
                'price': r.price_range or '$$',
                'image': img or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80",
                'description': (r.description[:100] + '...') if r.description and len(r.description) > 100 else (r.description or 'Un magnifique restaurant à découvrir.'),
                'promotion': promo_data
            })
        rests_json = json.dumps(rests_list)
    except Exception as e:
        rests_json = "[]"
        
    return render(request, 'pages/index.html', {
        'restaurants': rests_list,
        'db_restaurants': rests_json
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

                from django.contrib.auth.hashers import make_password
                MongoUser.objects.using('mongodb').create(
                    email=email,
                    username=user.username,
                    password=make_password(password),
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
                
                from django.contrib.auth.hashers import make_password
                MongoUser.objects.using('mongodb').create(
                    email=email,
                    username=user.username,
                    password=make_password(password),
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
                    from django.contrib.auth.hashers import check_password
                    if check_password(password, mongo_user.password):
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
    }
    return render(request, 'pages/mon_compte.html', context)


@login_required(login_url='auth')
def modifier_profil(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('prenom', '')
        user.last_name = request.POST.get('nom', '')
        user.email = request.POST.get('email', '')
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
    # Note : .using('mongodb') est utilisé car les points sont stockés dans MongoDB
    loyalty_points, created = LoyaltyPoints.objects.using('mongodb').get_or_create(
        user=request.user,
        defaults={'points': 0, 'tier': 'ekoul'}
    )

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
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')
        restaurant_name = request.POST.get('restaurant_name')
        restaurant_image = request.POST.get('restaurant_image')

        if not restaurant_id:
            return JsonResponse({'status': 'error', 'message': 'Missing restaurant_id'}, status=400)

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            restaurant_id=restaurant_id,
            defaults={
                'restaurant_name': restaurant_name or f"Restaurant {restaurant_id}",
                'restaurant_image': restaurant_image,
                'cuisine': request.POST.get('cuisine'),
                'rating': request.POST.get('rating'),
                'location': request.POST.get('location'),
                'category': request.POST.get('category')
            }
        )

        if not created:
            favorite.delete()
            return JsonResponse({'status': 'removed'})

        return JsonResponse({'status': 'added'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def is_favorite_api(request, restaurant_id):
    if not request.user.is_authenticated:
        return JsonResponse({'is_favorite': False})

    is_favorite = Favorite.objects.filter(user=request.user, restaurant_id=restaurant_id).exists()
    return JsonResponse({'is_favorite': is_favorite})


@login_required(login_url='auth')
def restaurant_detail(request, restaurant_id):
    rest_json = "null"
    try:
        rid = int(restaurant_id)
        r = Restaurant.objects.using('mongodb').filter(Q(static_id=rid) | Q(user_id=rid)).first()
            
        if r:
            menu_items = MenuItem.objects.using('mongodb').filter(restaurant_id=str(r.static_id or r.user_id))
            menu = []
            for m in menu_items:
                menu.append({
                    'name': m.name,
                    'price': f"{m.price} DT",
                    'category': m.category,
                    'image': m.image_url or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&fit=crop"
                })
                
            reviews_qs = Review.objects.filter(restaurant_id=rid, status='approved')
            reviews = []
            for rev in reviews_qs:
                reviews.append({
                    'user': rev.user.first_name or rev.user.username,
                    'rating': rev.rating,
                    'comment': rev.comment
                })
                
            # Récupérer les promotions actives
            from django.utils import timezone
            today = timezone.now().date()
            promotions = []
            try:
                active_promotions = Promotion.objects.using('mongodb').filter(
                    restaurant_id=str(r.static_id or r.user_id),
                    is_active=True,
                    start_date__lte=today,
                    end_date__gte=today
                )
                for p in active_promotions:
                    promotions.append({
                        'title': p.title,
                        'description': p.description,
                        'discount': f"-{p.discount_percentage}%",
                        'end_date': p.end_date.strftime('%d/%m') if p.end_date else None
                    })
            except:
                pass
                
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
                'location': r.city or r.address or '',
                'rating': r.rating or 4.0,
                'price': r.price_range or '$$',
                'image': image or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80",
                'description': r.description or 'Un magnifique restaurant à découvrir.',
                'address': r.address or '',
                'phone': r.phone or '',
                'email': r.email or '',
                'menu': menu,
                'reviews': reviews,
                'promotions': promotions
            }
            rest_json = json.dumps(rest_data)
        elif rid in RESTAURANTS_DATA:
            pass
    except Exception as e:
        pass

    return render(request, 'pages/restaurant_detail.html', {
        'restaurant_id': restaurant_id,
        'db_restaurant': rest_json
    })

@login_required(login_url='auth')
def api_dashboard_data(request):
    restaurant = get_user_restaurant(request.user)
    if not restaurant:
        return JsonResponse({'error': 'Aucun restaurant trouvé'}, status=404)

    rest_id = str(restaurant.static_id or restaurant.user_id)

    reservations = []
    try:
        qs = Reservation.objects.using('mongodb').filter(
            restaurant_id=rest_id
        ).order_by('-created_at')[:20]
        for r in qs:
            reservations.append({
                'id': str(r.id),
                'name': r.user_name,
                'persons': r.guests,
                'time': r.time.strftime('%H:%M') if r.time else '',
                'date': r.date.strftime('%Y-%m-%d') if r.date else '',
                'status': r.status,
            })
    except:
        pass

    reviews = []
    try:
        qs = Review.objects.using('mongodb').filter(restaurant_id=rest_id).order_by('-created_at')[:10]
        for r in qs:
            reviews.append({
                'id': str(r.id),
                'user': r.user.get_full_name() or r.user.username,
                'rating': r.rating,
                'comment': r.comment,
                'reply': r.restaurant_reply,
                'date': r.created_at.strftime('%Y-%m-%d'),
                'avatar': f'https://i.pravatar.cc/150?u={r.user.id}',
            })
    except:
        pass

    menu_items = []
    try:
        qs = MenuItem.objects.using('mongodb').filter(restaurant_id=rest_id)
        for m in qs:
            menu_items.append({
                'id': str(m.id),
                'name': m.name,
                'price': f"{m.price} DT",
                'category': m.category,
                'image': m.image_url or '',
                'stock': m.is_available,
            })
    except:
        pass

    gallery = []
    try:
        qs = RestaurantGallery.objects.using('mongodb').filter(restaurant_id=rest_id)
        for g in qs:
            gallery.append({
                'id': str(g.id),
                'url': g.image_url,
                'name': g.caption or '',
            })
    except:
        pass

    promotions = []
    try:
        qs = Promotion.objects.using('mongodb').filter(restaurant_id=rest_id, is_active=True)
        for p in qs:
            status = 'active'
            if p.end_date and (p.end_date - date.today()).days <= 3:
                status = 'ending'
            promotions.append({
                'id': str(p.id),
                'title': p.title,
                'description': p.description,
                'discount': f"-{p.discount_percentage}%",
                'status': status,
            })
    except:
        pass

    favorites_count = Favorite.objects.using('mongodb').filter(restaurant_id=rest_id).count()

    total_reviews = Review.objects.using('mongodb').filter(restaurant_id=rest_id).count()
    avg_rating = Review.objects.using('mongodb').filter(
        restaurant_id=rest_id, status='approved'
    ).aggregate(Avg('rating'))['rating__avg'] or 0

    monthly_reservations = 0
    try:
        thirty_days_ago = date.today() - timedelta(days=30)
        monthly_reservations = Reservation.objects.using('mongodb').filter(
            restaurant_id=rest_id,
            created_at__gte=thirty_days_ago
        ).count()
    except:
        pass

    notifications = []
    try:
        from django.utils import timezone
        from datetime import timedelta
        one_day_ago = timezone.now() - timedelta(days=1)
        
        recent_res = Reservation.objects.using('mongodb').filter(
            restaurant_id=rest_id,
            created_at__gte=one_day_ago
        ).order_by('-created_at')[:10]
        
        for r in recent_res:
            notifications.append({
                'id': f"res_{r.id}",
                'type': 'reservation',
                'titre': 'Nouvelle réservation',
                'message': f"{r.user_name} a réservé pour {r.guests} pers.",
                'time': r.created_at.isoformat(),
                'lue': False
            })

        recent_favs = Favorite.objects.using('mongodb').filter(
            restaurant_id=rest_id,
            created_at__gte=one_day_ago
        ).order_by('-created_at')[:10]

        for f in recent_favs:
            notifications.append({
                'id': f"fav_{f.id}",
                'type': 'favorite', 
                'titre': 'Nouveau favori',
                'message': f"Un utilisateur a ajouté votre restaurant à ses favoris !",
                'time': f.created_at.isoformat(),
                'lue': False
            })

        recent_reviews = Review.objects.using('mongodb').filter(
            restaurant_id=rest_id,
            created_at__gte=one_day_ago
        ).order_by('-created_at')[:10]

        for rev in recent_reviews:
            notifications.append({
                'id': f"rev_{rev.id}",
                'type': 'review',
                'titre': 'Nouvel avis',
                'message': f"{rev.user.first_name or rev.user.username} a laissé {rev.rating}★",
                'time': rev.created_at.isoformat(),
                'lue': False
            })
    except Exception as e:
        print(f"Notification error: {e}")

    # REAL STATS CALCULATIONS
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    
    confirmed_res_30d = list(Reservation.objects.using('mongodb').filter(
        restaurant_id=rest_id,
        created_at__gte=thirty_days_ago,
        status='confirmed'
    ))
    all_res_30d = list(Reservation.objects.using('mongodb').filter(
        restaurant_id=rest_id,
        created_at__gte=thirty_days_ago
    ))

    estimated_revenue = sum(r.guests for r in confirmed_res_30d) * 35
    monthly_reservations = len(all_res_30d)
    
    labels_7d = []
    data_7d = []
    for i in range(6, -1, -1):
        target_date = (now - timedelta(days=i)).date()
        labels_7d.append(target_date.strftime('%d/%m'))
        count = Reservation.objects.using('mongodb').filter(
            restaurant_id=rest_id,
            date=target_date
        ).count()
        data_7d.append(count)

    hours_labels = ['12h', '13h', '14h', '19h', '20h', '21h', '22h']
    hours_data = [0] * len(hours_labels)
    for r in all_res_30d:
        if r.time:
            h = r.time.hour
            if h == 12: hours_data[0] += 1
            elif h == 13: hours_data[1] += 1
            elif h == 14: hours_data[2] += 1
            elif h == 19: hours_data[3] += 1
            elif h == 20: hours_data[4] += 1
            elif h == 21: hours_data[5] += 1
            elif h == 22: hours_data[6] += 1

    # Photo aléatoire de la galerie si disponible
    rid = restaurant.static_id or restaurant.user_id or 999
    gallery_images = RestaurantGallery.objects.using('mongodb').filter(restaurant_id=str(rid))
    restaurant_image = restaurant.image or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80"
    if gallery_images.exists():
        import random
        img_list = [g.image_url for g in gallery_images]
        restaurant_image = random.choice(img_list)

    data = {
        'restaurant': {
            'name': restaurant.name,
            'location': restaurant.city or '',
            'phone': restaurant.phone or '',
            'email': restaurant.email or '',
            'description': restaurant.description or '',
            'address': restaurant.address or '',
            'cuisine': restaurant.cuisine_type or '',
            'price': restaurant.price_range or '$$$',
            'image': restaurant_image,
            'hours': {
                'monday_friday': restaurant.hours_weekday or '12:00 - 15:00 | 19:00 - 23:00',
                'saturday': restaurant.hours_saturday or '12:00 - 16:00 | 19:00 - 00:00',
                'sunday': restaurant.hours_sunday or '12:00 - 16:00'
            }
        },
        'stats': {
            'avg_rating': round(avg_rating, 1),
            'total_reviews': total_reviews,
            'monthly_reservations': monthly_reservations,
            'favorites': favorites_count,
            'estimated_revenue': estimated_revenue,
            'occupancy_rate': min(100, monthly_reservations * 3),
            'loyalty_count': int(monthly_reservations * 0.4),
            'charts': {
                'performance': {'labels': labels_7d, 'data': data_7d},
                'hours': {'labels': hours_labels, 'data': hours_data}
            }
        },
        'reservations': reservations,
        'reviews': reviews,
        'menu': menu_items,
        'gallery': gallery,
        'promotions': promotions,
        'notifications': notifications
    }

    return JsonResponse(data)


@login_required(login_url='auth')
@csrf_exempt
def api_menu_item(request):
    restaurant = get_user_restaurant(request.user)
    if not restaurant:
        return JsonResponse({'error': 'Aucun restaurant'}, status=404)

    rest_id = str(restaurant.static_id or 0)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            item = MenuItem.objects.using('mongodb').create(
                restaurant_id=rest_id,
                name=body.get('name', ''),
                price=body.get('price', 0),
                category=body.get('category', 'Plats'),
                image_url=body.get('image', ''),
                is_available=body.get('stock', True),
            )
            return JsonResponse({'status': 'ok', 'id': str(item.id)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    if request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            MenuItem.objects.using('mongodb').filter(
                id=body.get('id'),
                restaurant_id=str(rest_id)
            ).delete()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    if request.method == 'PUT':
        try:
            body = json.loads(request.body)
            MenuItem.objects.using('mongodb').filter(
                id=body.get('id'),
                restaurant_id=str(rest_id)
            ).update(
                name=body.get('name', ''),
                price=body.get('price', 0),
                category=body.get('category', 'Plats'),
                image_url=body.get('image', ''),
                is_available=body.get('stock', True),
            )
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required(login_url='auth')
@csrf_exempt
def api_reservation_action(request):
    restaurant = get_user_restaurant(request.user)
    if not restaurant:
        return JsonResponse({'error': 'Aucun restaurant'}, status=404)
        
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            action = body.get('action')

            if action == 'create':
                Reservation.objects.using('mongodb').create(
                    user_id=request.user.id,
                    user_email=request.user.email,
                    user_name=body.get('name', 'Client Restaurant'),
                    restaurant_id=restaurant.static_id or 0,
                    restaurant_name=restaurant.name,
                    date=datetime.strptime(body.get('date'), '%Y-%m-%d').date() if body.get('date') else date.today(),
                    time=datetime.strptime(body.get('time'), '%H:%M').time() if body.get('time') else None,
                    guests=int(body.get('persons', 2)),
                    status='confirmed'
                )
                return JsonResponse({'status': 'ok'})

            res_id = body.get('id')
            res = Reservation.objects.using('mongodb').get(id=res_id)

            if action == 'confirm':
                res.status = 'confirmed'
            elif action == 'cancel':
                res.status = 'cancelled'

            res.save(using='mongodb')
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required(login_url='auth')
@csrf_exempt
def api_gallery(request):
    restaurant = get_user_restaurant(request.user)
    if not restaurant:
        return JsonResponse({'error': 'Aucun restaurant'}, status=404)

    rest_id = restaurant.static_id or 0

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            photo_url = body.get('url', '')
            photo = RestaurantGallery.objects.using('mongodb').create(
                restaurant_id=rest_id,
                image_url=photo_url,
                caption=body.get('name', ''),
            )
            
            # Save as main image if it's the first one
            if not restaurant.image and photo_url:
                restaurant.image = photo_url
                restaurant.save(using='mongodb')
                
            return JsonResponse({'status': 'ok', 'id': str(photo.id)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    if request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            RestaurantGallery.objects.using('mongodb').filter(
                id=body.get('id'),
                restaurant_id=rest_id
            ).delete()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required(login_url='auth')
@csrf_exempt
def api_promotion(request):
    restaurant = get_user_restaurant(request.user)
    if not restaurant:
        return JsonResponse({'error': 'Aucun restaurant'}, status=404)

    rest_id = restaurant.static_id or 0

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            promo = Promotion.objects.using('mongodb').create(
                restaurant_id=rest_id,
                title=body.get('title', ''),
                description=body.get('description', ''),
                discount_percentage=int(body.get('discount', '0').replace('-', '').replace('%', '') or 0),
                start_date=body.get('start_date', date.today()),
                end_date=body.get('end_date', date.today() + timedelta(days=30)),
                is_active=True,
            )
            return JsonResponse({'status': 'ok', 'id': str(promo.id)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    if request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            Promotion.objects.using('mongodb').filter(
                id=body.get('id'),
                restaurant_id=rest_id
            ).delete()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required(login_url='auth')
@csrf_exempt
def api_restaurant_settings(request):
    restaurant = get_user_restaurant(request.user)
    if not restaurant:
        return JsonResponse({'error': 'Aucun restaurant'}, status=404)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            restaurant.name = body.get('name', restaurant.name)
            restaurant.description = body.get('description', restaurant.description)
            restaurant.phone = body.get('phone', restaurant.phone)
            restaurant.email = body.get('email', restaurant.email)
            restaurant.address = body.get('address', restaurant.address)
            restaurant.cuisine_type = body.get('cuisine', restaurant.cuisine_type)
            restaurant.price_range = body.get('price', restaurant.price_range)
            restaurant.hours_weekday = body.get('hours_weekday', restaurant.hours_weekday)
            restaurant.hours_saturday = body.get('hours_saturday', restaurant.hours_saturday)
            restaurant.hours_sunday = body.get('hours_sunday', restaurant.hours_sunday)
            restaurant.save(using='mongodb')
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@superadmin_required
def admin_dashboard_stats(request):
    total_users = User.objects.count()
    total_restaurants = Restaurant.objects.using('mongodb').count()
    pending_count = Restaurant.objects.using('mongodb').filter(status='pending').count()
    active_count = Restaurant.objects.using('mongodb').filter(status='approved').count()


    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()

    pending_rest = []
    try:
        pending_rest = list(Restaurant.objects.using('mongodb').filter(status='pending')[:5])
    except:
        pass

    recent_users = User.objects.order_by('-date_joined')[:5]

    user_stats = []
    user_type_counts = UserProfile.objects.using('mongodb').values('user_type').annotate(count=Count('id'))
    for item in user_type_counts:
        user_stats.append({
            'user_type': item['user_type'],
            'count': item['count']
        })

    type_present = [item['user_type'] for item in user_stats]
    if 'user' not in type_present:
        user_stats.append({'user_type': 'user', 'count': 0})
    if 'restaurant' not in type_present:
        user_stats.append({'user_type': 'restaurant', 'count': 0})
    if 'admin' not in type_present:
        user_stats.append({'user_type': 'admin', 'count': 0})

    total_users_count = total_users if total_users > 0 else 1
    user_type_dist = [
        {'user_type': 'user', 'count': next((item['count'] for item in user_stats if item['user_type'] == 'user'), 0),
         'percentage': round((next((item['count'] for item in user_stats if item['user_type'] == 'user'), 0) / total_users_count * 100), 1)},
        {'user_type': 'restaurant', 'count': next((item['count'] for item in user_stats if item['user_type'] == 'restaurant'), 0),
         'percentage': round((next((item['count'] for item in user_stats if item['user_type'] == 'restaurant'), 0) / total_users_count * 100), 1)},
        {'user_type': 'admin', 'count': next((item['count'] for item in user_stats if item['user_type'] == 'admin'), 0),
         'percentage': round((next((item['count'] for item in user_stats if item['user_type'] == 'admin'), 0) / total_users_count * 100), 1)},
    ]

    total_rest_count = total_restaurants if total_restaurants > 0 else 1
    restaurant_status_dist = [
        {'status': 'pending', 'count': pending_count,
         'percentage': round((pending_count / total_rest_count * 100), 1)},
        {'status': 'approved', 'count': active_count,
         'percentage': round((active_count / total_rest_count * 100), 1)},
        {'status': 'rejected', 'count': 0, 'percentage': 0},
        {'status': 'suspended', 'count': 0, 'percentage': 0},
    ]

    restaurants_by_city = []
    city_counts = Restaurant.objects.using('mongodb').values('city').annotate(count=Count('id')).order_by('-count')
    for item in city_counts:
        if item['city']:
            restaurants_by_city.append({
                'city': item['city'],
                'count': item['count'],
                'percentage': round((item['count'] / total_rest_count * 100), 1)
            })
    if not restaurants_by_city:
        restaurants_by_city = [{'city': 'Inconnu', 'count': 0, 'percentage': 0}]


    try:
        new_restaurants_30d = Restaurant.objects.using('mongodb').filter(created_at__gte=thirty_days_ago).count()
    except:
        new_restaurants_30d = 0

    context = {
        'total_users': total_users,
        'total_restaurants': total_restaurants,
        'pending_restaurants': pending_count,
        'active_restaurants': active_count,
        'new_users_30d': new_users_30d,
        'new_restaurants_30d': new_restaurants_30d,
        'pending_rest': pending_rest,
        'recent_users': recent_users,
        'user_stats': user_stats,
        'user_type_dist': user_type_dist,
        'restaurant_status_dist': restaurant_status_dist,
        'restaurants_by_city': restaurants_by_city,
    }
    return render(request, 'pages/admin-panel/dashboard_stats.html', context)


@superadmin_required
def admin_restaurants(request):
    restaurants = []
    try:
        qs = Restaurant.objects.using('mongodb').all()
        for r in qs:
            restaurants.append({
                'id': str(r.pk),
                'name': r.name or '',
                'cuisine': r.cuisine_type or 'Autres',
                'location': r.city or r.address or '',
                'rating': r.rating or 4.0,
                'price': r.price_range or '$$',
                'image': r.image or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&q=80",
                'description': r.description or '',
                'address': r.address or '',
                'phone': r.phone or '',
                'email': r.email or '',
                'status': getattr(r, 'status', 'approved'),
                'is_active': getattr(r, 'is_active', True),
                'payment_status': getattr(r, 'payment_status', 'unpaid'),
                'created_at': getattr(r, 'created_at').strftime('%Y-%m-%d') if hasattr(r, 'created_at') and r.created_at else ''
            })
    except:
        pass

    context = {
        'status_filter': request.GET.get('status', ''),
        'search': request.GET.get('search', ''),
        'admin_restaurants_json': json.dumps(restaurants)
    }
    return render(request, 'pages/admin-panel/restaurants.html', context)


from .models import (
    Restaurant, UserProfile, Review, LoyaltyPoints,
    LoyaltyTransaction, Reservation, Favorite,
    MenuItem, RestaurantGallery, Promotion, SupportMessage
)

def restaurant_payment(request, restaurant_id):
    """Page de paiement simulée pour un restaurant (50 DT)"""
    try:
        from django.db.models import Q
        if isinstance(restaurant_id, int) or str(restaurant_id).isdigit():
            rid = int(restaurant_id)
            restaurant = Restaurant.objects.using('mongodb').filter(
                Q(static_id=rid) | Q(user_id=rid)
            ).first()
        else:
            try:
                from bson import ObjectId
                restaurant = Restaurant.objects.using('mongodb').filter(id=ObjectId(restaurant_id)).first()
            except:
                restaurant = Restaurant.objects.using('mongodb').filter(id=restaurant_id).first()
    except:
        restaurant = None
        
    if not restaurant:
        return render(request, 'pages/error.html', {'message': 'Restaurant introuvable'})

    if request.method == 'POST':
        restaurant.payment_status = 'paid'
        restaurant.payment_date = timezone.now()
        # Le restaurant passe en 'pending' pour signalement à l'admin qu'il peut maintenant être approuvé
        restaurant.status = 'pending'
        restaurant.save(using='mongodb')
        
        # Enregistrer un message automatique dans le support pour prévenir l'admin
        from django.contrib.auth.models import User
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # Récupérer l'utilisateur associé au restaurant s'il existe
        sender_user = admin_user
        if hasattr(restaurant, 'user_id'):
            try:
                sender_user = User.objects.get(id=restaurant.user_id)
            except:
                pass
                
        if sender_user:
            SupportMessage.objects.using('mongodb').create(
                sender=sender_user,
                restaurant_id=str(restaurant_id),
                message=f"PAIEMENT EFFECTUÉ : Le restaurant {restaurant.name} a payé les frais d'inscription (50 DT).",
                is_from_admin=False
            )
            
        messages.success(request, f"Paiement de 50 DT pour {restaurant.name} effectué avec succès !")
        return render(request, 'pages/payment_success.html', {'restaurant': restaurant})

    return render(request, 'pages/payment.html', {'restaurant': restaurant})

@superadmin_required
def admin_restaurant_detail(request, restaurant_id):
    try:
        if isinstance(restaurant_id, int) or str(restaurant_id).isdigit():
            rid = int(restaurant_id)
            r = Restaurant.objects.using('mongodb').filter(
                Q(static_id=rid) | Q(user_id=rid)
            ).first()
        else:
            r = Restaurant.objects.using('mongodb').filter(id=restaurant_id).first()
    except (ValueError, TypeError):
        r = Restaurant.objects.using('mongodb').filter(id=restaurant_id).first()
    
    if not r:
        messages.error(request, "Restaurant non trouvé.")
        return redirect('admin_restaurants')

    rest_id_value = str(r.pk)

    # GESTION DES MESSAGES DE SUPPORT (Sécurisée pour éviter l'erreur IntegerField)
    if request.method == 'POST' and 'support_message' in request.POST:
        msg_text = request.POST.get('support_message', '').strip()
        if msg_text:
            try:
                # On utilise l'ID en texte (CharField) pour être compatible avec MongoDB et SQLite
                SupportMessage.objects.using('mongodb').create(
                    sender=request.user,
                    restaurant_id=str(rest_id_value),
                    message=msg_text,
                    is_from_admin=True
                )
                messages.success(request, "Message envoyé !")
            except:
                messages.error(request, "Impossible d'envoyer le message (ID incompatible).")
            return redirect('admin_restaurant_detail', restaurant_id=restaurant_id)

    # Récupérer les messages (Maintenant que restaurant_id est un CharField, c'est plus simple)
    try:
        support_messages = SupportMessage.objects.using('mongodb').filter(
            restaurant_id=str(rest_id_value)
        ).order_by('created_at')
    except:
        support_messages = []

    rest_data = None
    if r:
        # Récupération sécurisée du menu
        try:
            menu_items = MenuItem.objects.using('mongodb').filter(restaurant_id=str(rest_id_value))
        except:
            menu_items = []
            
        menu = []
        for m in menu_items:
            menu.append({'name': m.name, 'price': f"{m.price} DT", 'category': m.category})
            
        # Récupération sécurisée des avis
        try:
            reviews_qs = Review.objects.using('mongodb').filter(restaurant_id=str(rest_id_value))
        except:
            reviews_qs = []
            
        reviews = []
        for rev in reviews_qs:
            reviews.append({'user': rev.user.first_name or rev.user.username, 'rating': rev.rating, 'comment': rev.comment})
            
        rest_data = {
            'id': rest_id_value,
            'name': r.name or '',
            'cuisine': r.cuisine_type or 'Autres',
            'location': r.city or r.address or '',
            'rating': r.rating or 4.0,
            'price': r.price_range or '$$',
            'image': r.image or "https://via.placeholder.com/40x40?text=Resto",
            'description': r.description or '',
            'address': r.address or '',
            'phone': r.phone or '',
            'email': r.email or '',
            'status': getattr(r, 'status', 'approved'),
            'is_active': getattr(r, 'is_active', True),
            'payment_status': getattr(r, 'payment_status', 'unpaid'),
            'payment_date': r.payment_date.strftime('%d/%m/%Y %H:%M') if getattr(r, 'payment_date', None) else None,
            'menu': menu,
            'reviews': reviews
        }

    context = {
        'restaurant_id': restaurant_id,
        'restaurant': r,
        'support_messages': support_messages,
        'admin_restaurant_json': json.dumps(rest_data) if rest_data else 'null'
    }
    return render(request, 'pages/admin-panel/restaurant_detail.html', context)

@superadmin_required
@csrf_exempt
@superadmin_required
@csrf_exempt
def api_update_restaurant_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            restaurant_id = data.get('restaurant_id')
            new_status = data.get('status')
            
            if not restaurant_id or not new_status:
                return JsonResponse({'error': 'Données manquantes'}, status=400)
                
            try:
                from bson import ObjectId
                if isinstance(restaurant_id, int) or str(restaurant_id).isdigit():
                    rid = int(restaurant_id)
                    restaurant = Restaurant.objects.using('mongodb').filter(Q(static_id=rid) | Q(user_id=rid)).first()
                elif len(str(restaurant_id)) == 24:
                    restaurant = Restaurant.objects.using('mongodb').filter(id=ObjectId(restaurant_id)).first()
                else:
                    restaurant = Restaurant.objects.using('mongodb').filter(id=restaurant_id).first()
            except:
                restaurant = Restaurant.objects.using('mongodb').filter(id=restaurant_id).first()
                
            if not restaurant:
                return JsonResponse({'error': f'Restaurant non trouvé ({restaurant_id})'}, status=404)
                
            restaurant.status = new_status
            restaurant.save(using='mongodb')
            return JsonResponse({'status': 'success', 'message': f'Statut mis à jour : {new_status}'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@superadmin_required
@csrf_exempt
def send_payment_email_admin(request):
    """API pour simuler l'envoi d'un mail de paiement au restaurant"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            restaurant_id = data.get('restaurant_id')
            
            if not restaurant_id:
                return JsonResponse({'error': 'ID manquant'}, status=400)
                
            try:
                from bson import ObjectId
                if len(str(restaurant_id)) == 24:
                    r = Restaurant.objects.using('mongodb').filter(id=ObjectId(restaurant_id)).first()
                else:
                    r = Restaurant.objects.using('mongodb').filter(id=restaurant_id).first()
            except:
                r = Restaurant.objects.using('mongodb').filter(id=restaurant_id).first()
                
            if not r:
                return JsonResponse({'error': 'Restaurant non trouvé'}, status=404)
            
            # Générer l'URL complète pour qu'elle soit cliquable
            payment_url = request.build_absolute_uri(f"/payer/{restaurant_id}/")
            
            admin_user = User.objects.filter(is_superuser=True).first()
            SupportMessage.objects.using('mongodb').create(
                sender=admin_user if admin_user else request.user,
                restaurant_id=str(restaurant_id),
                message=f"LIEN DE PAIEMENT ENVOYÉ : Bonjour {r.name}. Pour finaliser votre inscription, merci de régler les frais (50 DT) sur ce lien sécurisé : {payment_url}",
                is_from_admin=True
            )
            return JsonResponse({'status': 'success', 'message': 'Lien envoyé par mail et posté dans le chat.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
@superadmin_required
def admin_users(request):
    user_type_filter = request.GET.get('user_type', '')
    search = request.GET.get('search', '')

    users_qs = User.objects.all().order_by('-date_joined')
    if search:
        users_qs = users_qs.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
        
    all_profiles = list(UserProfile.objects.using('mongodb').all())
    profile_map = {p.user_id: p for p in all_profiles}
    
    users = []
    for u in users_qs:
        p = profile_map.get(u.id)
        if user_type_filter and (not p or p.user_type != user_type_filter):
            continue
        u.profile = p
        users.append(u)

    user_type_counts = UserProfile.objects.using('mongodb').values('user_type').annotate(count=Count('id'))
    type_counts = {item['user_type']: item['count'] for item in user_type_counts}
    for ut in ['user', 'restaurant', 'admin']:
        if ut not in type_counts:
            type_counts[ut] = 0

    context = {
        'users': users,
        'type_counts': type_counts,
        'user_type_filter': user_type_filter,
        'search': search,
    }
    return render(request, 'pages/admin-panel/users.html', context)


@superadmin_required
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    try:
        profile = UserProfile.objects.using('mongodb').filter(user_id=user.id).first()
    except:
        profile = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'activate':
            user.is_active = True
            messages.success(request, f"Utilisateur '{user.username}' activé.")
        elif action == 'deactivate':
            user.is_active = False
            messages.success(request, f"Utilisateur '{user.username}' désactivé.")
        elif action == 'verify':
            if profile:
                profile.is_verified = True
                profile.save()
                messages.success(request, f"Utilisateur '{user.username}' vérifié.")
            else:
                messages.error(request, "Profil utilisateur introuvable.")
        elif action == 'unverify':
            if profile:
                profile.is_verified = False
                profile.save()
                messages.success(request, f"Vérification retirée pour '{user.username}'.")
            else:
                messages.error(request, "Profil utilisateur introuvable.")
        user.save()
        return redirect('admin_user_detail', user_id=user.id)

    return render(request, 'pages/admin-panel/user_detail.html', {'user': user, 'profile': profile})


@superadmin_required
def admin_reviews(request):
    status_filter = request.GET.get('status', '')
    rating_filter = request.GET.get('rating', '')
    search = request.GET.get('search', '')

    # Get reviews from MongoDB
    from .models import Review
    
    # Base query - get all reviews from MongoDB
    reviews_qs = Review.objects.using('mongodb').all()
    
    # Apply filters
    if status_filter:
        reviews_qs = reviews_qs.filter(status=status_filter)
    if rating_filter:
        reviews_qs = reviews_qs.filter(rating=rating_filter)
    if search:
        # MongoDB doesn't support Q objects the same way, so we'll filter in Python
        # Or use raw MongoDB queries for better performance
        search_lower = search.lower()
        reviews_qs = [r for r in reviews_qs if 
                      (r.user and (search_lower in r.user.username.lower() or 
                                   search_lower in r.user.email.lower())) or
                      (r.restaurant_name and search_lower in r.restaurant_name.lower()) or
                      (r.comment and search_lower in r.comment.lower())]
    else:
        # Convert to list for consistent handling
        reviews_qs = list(reviews_qs)
    
    # Calculate stats from MongoDB
    all_reviews = list(Review.objects.using('mongodb').all())
    approved_reviews = [r for r in all_reviews if r.status == 'approved']
    
    stats = {
        'total': len(all_reviews),
        'pending': len([r for r in all_reviews if r.status == 'pending']),
        'approved': len([r for r in all_reviews if r.status == 'approved']),
        'rejected': len([r for r in all_reviews if r.status == 'rejected']),
        'avg_rating': sum(r.rating for r in approved_reviews) / len(approved_reviews) if approved_reviews else 0,
    }

    # Rating distribution
    rating_dist = []
    for i in range(1, 6):
        count = len([r for r in all_reviews if r.rating == i])
        rating_dist.append({'rating': i, 'count': count})

    context = {
        'reviews': reviews_qs,
        'stats': stats,
        'rating_dist': rating_dist,
        'status_filter': status_filter,
        'rating_filter': rating_filter,
        'search': search,
    }
    return render(request, 'pages/admin-panel/reviews.html', context)


@superadmin_required
def admin_review_detail(request, review_id):
    from .models import Review
    from bson import ObjectId
    from django.contrib.auth.models import User
    
    # Try to find the review by ObjectId
    try:
        # If review_id is a string, try to convert to ObjectId
        if isinstance(review_id, str) and len(review_id) == 24:
            review = Review.objects.using('mongodb').get(id=ObjectId(review_id))
        else:
            # Try to find by string id
            review = Review.objects.using('mongodb').get(id=review_id)
    except (Review.DoesNotExist, ValueError, Exception) as e:
        messages.error(request, f"Review not found: {str(e)}")
        return redirect('admin_reviews')
    
    # Get user details from SQLite and attach to review
    try:
        if review.user and hasattr(review.user, 'id'):
            user = User.objects.get(id=review.user.id)
            # Attach user object to review for template access
            review.user_obj = user
        else:
            review.user_obj = None
    except User.DoesNotExist:
        review.user_obj = None
    except Exception as e:
        print(f"Error fetching user: {e}")
        review.user_obj = None
    
    # Get other reviews from the same user
    user_reviews = []
    if review.user and hasattr(review.user, 'id') and review.user.id:
        try:
            user_reviews_qs = Review.objects.using('mongodb').filter(user_id=review.user.id).exclude(id=review.id)[:5]
            for rev in user_reviews_qs:
                try:
                    rev.user_obj = User.objects.get(id=rev.user.id) if rev.user and rev.user.id else None
                except User.DoesNotExist:
                    rev.user_obj = None
                user_reviews.append(rev)
        except Exception as e:
            print(f"Error fetching user reviews: {e}")
    
    # Handle POST actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            review.status = 'approved'
            review.save(using='mongodb')
            messages.success(request, "Avis approuvé.")
            
            # Add loyalty points for high ratings
            if review.rating >= 4 and review.user and hasattr(review.user, 'id') and review.user.id:
                try:
                    from .models import LoyaltyPoints, LoyaltyTransaction
                    # Get or create loyalty points
                    loyalty = LoyaltyPoints.objects.using('mongodb').filter(user_id=review.user.id).first()
                    if not loyalty:
                        loyalty = LoyaltyPoints.objects.using('mongodb').create(
                            user_id=review.user.id,
                            points=0,
                            total_points_earned=0,
                            total_points_used=0,
                            tier='ekoul'
                        )
                    
                    loyalty.points += 5
                    loyalty.total_points_earned += 5
                    loyalty.save(using='mongodb')
                    
                    # Create transaction
                    LoyaltyTransaction.objects.using('mongodb').create(
                        user_id=review.user.id,
                        points=5,
                        transaction_type='earned',
                        description=f"Points bonus pour avis {review.rating}★ sur {review.restaurant_name}"
                    )
                    messages.info(request, "5 points de fidélité ont été ajoutés à l'utilisateur.")
                except Exception as e:
                    print(f"Error adding loyalty points: {e}")
                    
        elif action == 'reject':
            review.status = 'rejected'
            review.save(using='mongodb')
            messages.success(request, "Avis rejeté.")
            
        elif action == 'verify':
            review.is_verified = not review.is_verified
            review.save(using='mongodb')
            messages.success(request, f"Vérification {'activée' if review.is_verified else 'désactivée'}.")
            
        return redirect('admin_review_detail', review_id=str(review.id))
    
    context = {
        'review': review,
        'user_reviews': user_reviews,
    }
   
    return render(request, 'pages/admin-panel/review_detail.html', context)
@superadmin_required
def admin_loyalty_overview(request):
    user_id = request.GET.get('user_id')
    search = request.GET.get('search', '')
    tier_filter = request.GET.get('tier', '')
    transaction_type = request.GET.get('type', '')

    loyalty_points = list(LoyaltyPoints.objects.using('mongodb').all())
    loyalty_map = {lp.user_id: lp for lp in loyalty_points}
    loyalty_user_ids = list(loyalty_map.keys())

    users_qs = User.objects.filter(id__in=loyalty_user_ids)

    if search:
        users_qs = users_qs.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    users_with_loyalty = []
    for u in users_qs:
        lp = loyalty_map.get(u.id)
        if tier_filter and (not lp or lp.tier != tier_filter):
            continue
        u.loyalty = lp
        users_with_loyalty.append(u)

    total_points = LoyaltyPoints.objects.using('mongodb').aggregate(Sum('points'))['points__sum'] or 0
    avg_points = LoyaltyPoints.objects.using('mongodb').aggregate(Avg('points'))['points__avg'] or 0

    stats = {
        'total_points': total_points,
        'avg_points': avg_points,
        'total_users': LoyaltyPoints.objects.using('mongodb').count(),
        'tiers': {
            'ekoul': LoyaltyPoints.objects.using('mongodb').filter(tier='ekoul').count(),
            'ekoul_kbir': LoyaltyPoints.objects.using('mongodb').filter(tier='ekoul_kbir').count(),
            'makhmekh': LoyaltyPoints.objects.using('mongodb').filter(tier='makhmekh').count(),
            'makhmekh_kbir': LoyaltyPoints.objects.using('mongodb').filter(tier='makhmekh_kbir').count(),
        }
    }

    if user_id:
        target_user = get_object_or_404(User, id=user_id)
        transactions = LoyaltyTransaction.objects.using('mongodb').filter(user_id=target_user.id)
    else:
        target_user = None
        transactions = LoyaltyTransaction.objects.using('mongodb').all()

    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    transactions_list = list(transactions.order_by('-created_at'))
    transactions_count = LoyaltyTransaction.objects.using('mongodb').count()
    
    tx_user_ids = {tx.user_id for tx in transactions_list}
    tx_users = {u.id: u for u in User.objects.filter(id__in=tx_user_ids)}
    for tx in transactions_list:
        tx.user = tx_users.get(tx.user_id)
        
    transactions = transactions_list

    context = {
        'stats': stats,
        'users': users_with_loyalty,
        'tier_filter': tier_filter,
        'search': search,
        'target_user': target_user,
        'transactions': transactions,
        'transaction_type': transaction_type,
        'transactions_count': transactions_count,
    }
    return render(request, 'pages/admin-panel/loyalty_overview.html', context)


@superadmin_required
def admin_dash(request):
    return redirect('admin_dashboard_stats')


@superadmin_required
def admin_statistics(request):
    return redirect('admin_dashboard_stats')


@superadmin_required
def admin_loyalty_users(request):
    return redirect('admin_loyalty_overview')


@superadmin_required
def admin_loyalty_transactions(request, user_id=None):
    if user_id:
        return redirect(f"{reverse('admin_loyalty_overview')}?user_id={user_id}")
    return redirect('admin_loyalty_overview')


@csrf_exempt
def api_submit_review(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    
    try:
        data = json.loads(request.body)
        restaurant_id = data.get('restaurant_id')
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '')
        user_name = data.get('name', 'Anonyme')

        if not restaurant_id or rating < 1 or rating > 5:
            return JsonResponse({'error': 'Données invalides'}, status=400)

        # Validation spécifique selon les nouvelles spécifications
        if not comment or len(comment.strip()) < 5:
            return JsonResponse({'error': 'Le commentaire doit contenir au moins 5 caractères'}, status=400)

        restaurant = Restaurant.objects.using('mongodb').filter(
            Q(static_id=restaurant_id) | Q(user_id=restaurant_id)
        ).first()

        if not restaurant:
            return JsonResponse({'error': 'Restaurant non trouvé'}, status=404)

        from django.contrib.auth.models import User
        import os
        current_user = request.user if request.user.is_authenticated else User.objects.get(id=1) 

        Review.objects.using('mongodb').create(
            user=current_user,
            restaurant_id=restaurant_id,
            restaurant_name=restaurant.name,
            rating=rating,
            comment=comment,
            status='approved'
        )

        from django.db.models import Avg
        all_reviews = Review.objects.using('mongodb').filter(restaurant_id=restaurant_id, status='approved')
        avg_calc = all_reviews.aggregate(Avg('rating'))['rating__avg']
        avg_rating = float(avg_calc) if avg_calc else 4.0
        
        restaurant.rating = round(avg_rating, 1)
        restaurant.save(using='mongodb')

        return JsonResponse({
            'status': 'success',
            'new_rating': restaurant.rating,
            'message': 'Avis enregistré !'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required(login_url='auth')
def api_review_reply(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    
    try:
        data = json.loads(request.body)
        review_id = data.get('id')
        reply_text = data.get('reply', '')
        
        if not review_id:
            return JsonResponse({'error': 'ID requis'}, status=400)
            
        review = Review.objects.using('mongodb').filter(id=review_id).first()
        if not review:
            return JsonResponse({'error': 'Avis non trouvé'}, status=404)
            
        review.restaurant_reply = reply_text
        review.reply_at = timezone.now()
        review.save(using='mongodb')
        
        return JsonResponse({'status': 'success', 'message': 'Réponse enregistrée !'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)