# -*- coding: utf-8 -*-
# ============================================================
# Vues Admin - Panneau d'administration DineTunis
# ============================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, Avg
from datetime import date, timedelta
from .models import (
    Restaurant, UserProfile, Review, LoyaltyPoints,
    LoyaltyTransaction, Reservation, Favorite,
    MenuItem, RestaurantGallery, Promotion, SupportMessage, MongoUser
)
from .utils import is_superadmin, superadmin_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json
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
            
            email_msg = f"Bonjour {r.name},\n\nVotre demande d'inscription sur DineTunis a été pré-approuvée !\nPour finaliser votre inscription et activer votre compte, veuillez régler les frais de dossier (50 DT) via le lien suivant :\n\n{payment_url}\n\nÀ très vite sur DineTunis !"
            
            # 1. Envoyer le vrai mail
            from django.core.mail import send_mail
            from django.conf import settings
            try:
                send_mail(
                    subject="Finalisez votre inscription sur DineTunis - Paiement requis",
                    message=email_msg,
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'admin@dinetunis.tn',
                    recipient_list=[r.email],
                    fail_silently=False,
                )
            except Exception as mail_error:
                print(f"Erreur d'envoi d'email: {mail_error}")
                # On continue même si le mail échoue (peut-être config SMTP manquante)
            
            # 2. Enregistrer le message de support
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

    total_points = sum(lp.points for lp in loyalty_points)
    avg_points = total_points / len(loyalty_points) if len(loyalty_points) > 0 else 0

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