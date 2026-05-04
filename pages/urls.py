from django.urls import path
from .views_user       import (
    presentation, index, auth, logout_view,
    mon_compte, modifier_profil, reserver,
    favorites, toggle_favorite, is_favorite_api,
    loyalty, restaurant_detail, dashboard,
)
from .views_restaurant import (
    api_dashboard_data, api_menu_item, api_reservation_action,
    api_gallery, api_promotion, api_restaurant_settings,
)
from .views_admin      import (
    admin_dash, admin_dashboard_stats,
    admin_restaurants, admin_restaurant_detail, restaurant_payment,
    admin_users, admin_user_detail,
    admin_reviews, admin_review_detail,
    admin_loyalty_overview,
    api_update_restaurant_status, send_payment_email_admin,
    api_submit_review, api_review_reply,
)

urlpatterns = [
    # ── Pages utilisateur ──────────────────────────────────
    path('',                                presentation,           name='presentation'),
    path('catalogue/',                      index,                  name='index'),
    path('connexion/',                      auth,                   name='auth'),
    path('deconnexion/',                    logout_view,            name='logout'),
    path('mon-compte/',                     mon_compte,             name='mon_compte'),
    path('modifier-profil/',                modifier_profil,        name='modifier_profil'),
    path('favoris/',                        favorites,              name='favorites'),
    path('fidelite/',                       loyalty,                name='loyalty'),
    path('reserver/<str:restaurant_id>/',   reserver,               name='reserver'),
    path('restaurant/<str:restaurant_id>/', restaurant_detail,      name='restaurant_detail'),
    path('restaurant-detail/<str:restaurant_id>/', restaurant_detail, name='restaurant_detail_alt'),
    path('toggle-favorite/',                toggle_favorite,        name='toggle_favorite'),
    path('api/is-favorite/<str:restaurant_id>/', is_favorite_api,  name='is_favorite_api'),
    path('api/submit-review/',              api_submit_review,      name='api_submit_review'),
    path('api/review-reply/',               api_review_reply,       name='api_review_reply'),

    # ── Dashboard restaurant ───────────────────────────────
    path('dashboard/',                      dashboard,              name='dashboard'),
    path('api/dashboard-data/',             api_dashboard_data,     name='api_dashboard_data'),
    path('api/menu-item/',                  api_menu_item,          name='api_menu_item'),
    path('api/reservation-action/',         api_reservation_action, name='api_reservation_action'),
    path('api/gallery/',                    api_gallery,            name='api_gallery'),
    path('api/promotion/',                  api_promotion,          name='api_promotion'),
    path('api/restaurant-settings/',        api_restaurant_settings,name='api_restaurant_settings'),

    # ── Panneau admin ──────────────────────────────────────
    path('admin-panel/',                                    admin_dash,                  name='admin_dash'),
    path('admin-panel/dashboard-stats/',                    admin_dashboard_stats,       name='admin_dashboard_stats'),
    path('admin-panel/restaurants/',                        admin_restaurants,           name='admin_restaurants'),
    path('admin-panel/restaurants/<str:restaurant_id>/',    admin_restaurant_detail,     name='admin_restaurant_detail'),
    path('payer/<str:restaurant_id>/',                      restaurant_payment,          name='restaurant_payment'),
    path('admin-panel/utilisateurs/',                       admin_users,                 name='admin_users'),
    path('admin-panel/utilisateurs/<int:user_id>/',         admin_user_detail,           name='admin_user_detail'),
    path('admin-panel/avis/',                               admin_reviews,               name='admin_reviews'),
    path('admin-panel/avis/<str:review_id>/',               admin_review_detail,         name='admin_review_detail'),
    path('admin-panel/fidelite/',                           admin_loyalty_overview,      name='admin_loyalty_overview'),
    path('api/update-restaurant-status/',                   api_update_restaurant_status,name='api_update_restaurant_status'),
    path('api/send-payment-link/',                          send_payment_email_admin,    name='send_payment_email_admin'),
]
