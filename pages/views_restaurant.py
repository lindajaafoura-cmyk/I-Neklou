# -*- coding: utf-8 -*-
# ============================================================
# Vues Restaurant - Dashboard propriétaire DineTunis
# ============================================================
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from datetime import date, timedelta, datetime
from .models import (
    Restaurant, Review, LoyaltyPoints, Reservation,
    Favorite, MenuItem, RestaurantGallery, Promotion, SupportMessage
)
from .utils import get_user_restaurant
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
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

