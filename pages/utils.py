# ============================================================
# Fonctions utilitaires partagées entre les vues
# ============================================================

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Restaurant, UserProfile, MongoUser

# Données statiques de fallback pour les images des restaurants
RESTAURANTS_DATA = {
    1001: {"name": "El Mida",              "image": "https://images.unsplash.com/photo-1544148103-0773bf10d330?w=800&q=80"},
    1002: {"name": "Le Golfe",             "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2a/5b/3c/7a/caption.jpg?w=1400&h=800&s=1"},
    1003: {"name": "Dar El Jeld",          "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/12/24/4a/36/au-coeur-de-la-medina.jpg?w=1800&h=1000&s=1"},
    1004: {"name": "Bella Napoli",         "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1c/19/fe/9d/bella-napoli.jpg?w=1400&h=-1&s=1"},
    1005: {"name": "The Creek",            "image": "https://lh3.googleusercontent.com/p/AF1QipPOpWVJf5Ss7S2R1_g0bv3-5NGtzNuTl3JZJ6JP=s1360-w1360-h1020-rw"},
    1006: {"name": "Fondouk El Attarine",  "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/11/fb/75/c9/photo8jpg.jpg?w=2000&h=-1&s=1"},
    1007: {"name": "La Salle à Manger",    "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2f/ad/8e/9b/la-terasse-espace-fumeur.jpg?w=1400&h=-1&s=1"},
    1008: {"name": "Boragó",               "image": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=800&q=80"},
    1009: {"name": "Bab Tounès",           "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2e/e0/a5/85/caption.jpg?w=1100&h=-1&s=1"},
}


def is_superadmin(user):
    """Vérifie si l'utilisateur est administrateur."""
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
    """Décorateur : redirige si l'utilisateur n'est pas admin."""
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
    """Retourne le restaurant associé à l'utilisateur connecté."""
    try:
        return Restaurant.objects.using('mongodb').filter(user_id=user.id).first()
    except:
        return None
