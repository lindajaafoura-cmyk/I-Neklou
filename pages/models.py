from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import django_mongodb_backend.fields


class Restaurant(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)

    STATUS_CHOICES = [
        ('pending', 'En attente de validation'),
        ('awaiting_payment', 'En attente de paiement'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('suspended', 'Suspendu'),
    ]

    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('unpaid', 'Non payé'),
            ('paid', 'Payé'),
        ],
        default='unpaid',
        verbose_name="Statut du paiement"
    )
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")

    user_id = models.IntegerField(null=True, blank=True, verbose_name="ID propriétaire")
    name = models.CharField(max_length=255, verbose_name="Nom du restaurant")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name="Téléphone")
    cin = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name="CIN responsable")
    password = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mot de passe")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    gouvernorat = models.CharField(max_length=50, blank=True, null=True, verbose_name="Gouvernorat")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")
    postal_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Code postal")
    cuisine_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Type de cuisine")
    image = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Image")
    price_range = models.CharField(max_length=10, blank=True, null=True, verbose_name="Gamme de prix")
    rating = models.FloatField(default=0, verbose_name="Note moyenne")
    static_id = models.IntegerField(null=True, blank=True, verbose_name="ID statique")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )

    is_active = models.BooleanField(default=True, verbose_name="Actif")

    hours_weekday = models.CharField(max_length=100, blank=True, null=True, verbose_name="Horaires semaine")
    hours_saturday = models.CharField(max_length=100, blank=True, null=True, verbose_name="Horaires samedi")
    hours_sunday = models.CharField(max_length=100, blank=True, null=True, verbose_name="Horaires dimanche")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'restaurant'
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)
    USER_TYPE_CHOICES = [
        ('user', 'Utilisateur'),
        ('restaurant', 'Restaurant'),
        ('admin', 'Administrateur'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='user',
        verbose_name="Type d'utilisateur"
    )

    is_verified = models.BooleanField(default=False, verbose_name="Vérifié")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'profile'
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_user_type_display()})"


class LoyaltyPoints(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    points = models.IntegerField(default=0, verbose_name="Points")
    tier = models.CharField(
        max_length=20,
        choices=[
            ('ekoul', 'Ekoul'),
            ('ekoul_kbir', 'Ekoul Kbir'),
            ('makhmekh', 'Makhmekh'),
            ('makhmekh_kbir', 'Makhmekh Kbir'),
        ],
        default='ekoul',
        verbose_name="Niveau"
    )
    total_points_earned = models.IntegerField(default=0, verbose_name="Total points gagnés")
    total_points_used = models.IntegerField(default=0, verbose_name="Total points utilisés")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        db_table = 'loyalty_points'
        verbose_name = "Points de fidélité"
        verbose_name_plural = "Points de fidélité"

    def __str__(self):
        return f"{self.user.username} - {self.points} points ({self.tier})"

    def update_tier(self):
        if self.total_points_earned >= 1000:
            self.tier = 'makhmekh_kbir'
        elif self.total_points_earned >= 500:
            self.tier = 'makhmekh'
        elif self.total_points_earned >= 200:
            self.tier = 'ekoul_kbir'
        else:
            self.tier = 'ekoul'


class LoyaltyTransaction(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)
    TRANSACTION_TYPES = [
        ('earned', 'Gagné'),
        ('spent', 'Dépensé'),
        ('bonus', 'Bonus'),
        ('expired', 'Expiré'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_transactions')
    points = models.IntegerField(verbose_name="Points")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name="Type")
    description = models.CharField(max_length=255, verbose_name="Description")
    reference_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID de référence")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        db_table = 'loyalty_transactions'
        verbose_name = "Transaction de points"
        verbose_name_plural = "Transactions de points"
        ordering = ['-created_at']


class Review(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    restaurant_id = models.CharField(max_length=255, verbose_name="ID du restaurant")
    restaurant_name = models.CharField(max_length=255, verbose_name="Nom du restaurant")
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name="Note")
    comment = models.TextField(verbose_name="Commentaire")

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('approved', 'Approuvé'),
            ('rejected', 'Rejeté'),
        ],
        default='pending',
        verbose_name="Statut"
    )

    is_verified = models.BooleanField(default=False, verbose_name="Avis vérifié")
    helpful_count = models.IntegerField(default=0, verbose_name="Utile")
    
    restaurant_reply = models.TextField(blank=True, null=True, verbose_name="Réponse du restaurant")
    reply_at = models.DateTimeField(blank=True, null=True, verbose_name="Date de réponse")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review'
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.restaurant_name} ({self.rating}★)"


class LoyaltyReward(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Nom")
    description = models.TextField(verbose_name="Description")
    points_required = models.IntegerField(verbose_name="Points requis")
    reward_type = models.CharField(
        max_length=50,
        choices=[
            ('discount', 'Réduction'),
            ('free_item', 'Article gratuit'),
            ('voucher', 'Bon d\'achat'),
            ('special', 'Offre spéciale'),
        ],
        verbose_name="Type"
    )
    discount_percentage = models.IntegerField(blank=True, null=True, verbose_name="% de réduction")
    free_item_description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Article gratuit")
    voucher_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Code promo")

    is_active = models.BooleanField(default=True, verbose_name="Active")
    stock = models.IntegerField(default=999, verbose_name="Stock")
    valid_until = models.DateField(blank=True, null=True, verbose_name="Valable jusqu'au")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loyalty_reward'
        verbose_name = "Récompense"
        verbose_name_plural = "Récompenses"

    def __str__(self):
        return f"{self.name} ({self.points_required} points)"


class UserRedemption(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redemptions')
    reward = models.ForeignKey(LoyaltyReward, on_delete=models.CASCADE)
    points_spent = models.IntegerField(verbose_name="Points dépensés")
    redeemed_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'échange")
    used_at = models.DateTimeField(blank=True, null=True, verbose_name="Date d'utilisation")
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Actif'),
            ('used', 'Utilisé'),
            ('expired', 'Expiré'),
        ],
        default='active'
    )

    class Meta:
        db_table = 'user_redemption'
        verbose_name = "Échange de récompense"
        verbose_name_plural = "Échanges de récompenses"

    def __str__(self):
        return f"{self.user.username} - {self.reward.name}"


class Reservation(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée'),
        ('completed', 'Terminée'),
    ]

    user_id = models.IntegerField(verbose_name="ID utilisateur")
    user_email = models.EmailField(verbose_name="Email utilisateur")
    user_name = models.CharField(max_length=255, verbose_name="Nom utilisateur")

    restaurant_id = models.CharField(max_length=255, verbose_name="ID du restaurant")
    restaurant_name = models.CharField(max_length=255, verbose_name="Nom du restaurant")

    date = models.DateField(verbose_name="Date")
    time = models.TimeField(verbose_name="Heure")
    guests = models.IntegerField(default=2, verbose_name="Nombre de personnes")
    special_requests = models.TextField(blank=True, null=True, verbose_name="Demandes spéciales")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'reservation'
        app_label = 'pages'
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_name} → {self.restaurant_name} le {self.date} ({self.status})"

    def get_status_display_fr(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def get_status_class(self):
        classes = {
            'pending': 'warning',
            'confirmed': 'success',
            'cancelled': 'danger',
            'completed': 'secondary',
        }
        return classes.get(self.status, 'secondary')


class Favorite(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris')
    restaurant_id = models.CharField(max_length=255, verbose_name="ID du restaurant")
    restaurant_name = models.CharField(max_length=255, verbose_name="Nom du restaurant")
    restaurant_image = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Image du restaurant")
    cuisine = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cuisine")
    rating = models.CharField(max_length=10, blank=True, null=True, verbose_name="Note")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Localisation")
    category = models.CharField(max_length=50, blank=True, null=True, verbose_name="Catégorie")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")

    class Meta:
        db_table = 'favorite'
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"
        unique_together = ('user', 'restaurant_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} favori: {self.restaurant_name}"


class MenuItem(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)

    restaurant_id = models.CharField(max_length=255, verbose_name="ID du restaurant")
    category = models.CharField(max_length=100, verbose_name="Catégorie")
    name = models.CharField(max_length=255, verbose_name="Nom du plat")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (TND)")
    image_url = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Image du plat")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'menuitem'
        app_label = 'pages'
        verbose_name = "Élément du menu"
        verbose_name_plural = "Éléments du menu"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} - {self.price} TND"


class RestaurantGallery(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)

    restaurant_id = models.CharField(max_length=255, verbose_name="ID du restaurant")
    image_url = models.URLField(max_length=1000, verbose_name="URL de l'image")
    caption = models.CharField(max_length=255, blank=True, null=True, verbose_name="Légende")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gallery'
        app_label = 'pages'
        verbose_name = "Photo de galerie"
        verbose_name_plural = "Photos de galerie"
        ordering = ['-created_at']

    def __str__(self):
        return f"Photo {self.id} pour le restaurant {self.restaurant_id}"


class Promotion(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)

    restaurant_id = models.CharField(max_length=255, verbose_name="ID du restaurant")
    title = models.CharField(max_length=255, verbose_name="Titre de la promotion")
    description = models.TextField(verbose_name="Description détaillée")
    discount_percentage = models.IntegerField(verbose_name="Pourcentage de réduction")

    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    is_active = models.BooleanField(default=True, verbose_name="Active")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'promotion'
        app_label = 'pages'
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        ordering = ['-end_date']

    def __str__(self):
        return f"{self.title} (-{self.discount_percentage}%)"


class MongoUser(models.Model):
    """
    Modèle pour interagir directement avec la collection 'user' MongoDB
    """
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)
    
    email = models.EmailField(unique=True, verbose_name="Email")
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    password = models.CharField(max_length=255, verbose_name="Mot de passe hashé")
    
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    user_type = models.CharField(
        max_length=20,
        choices=[
            ('user', 'Utilisateur'),
            ('restaurant', 'Restaurant'),
            ('admin', 'Administrateur'),
        ],
        default='user'
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'user'  # Nom de la collection MongoDB
        app_label = 'pages'
        managed = False  # Django ne crée pas la table, elle existe déjà
        verbose_name = "Utilisateur MongoDB"
        verbose_name_plural = "Utilisateurs MongoDB"
    
    def __str__(self):
        return self.email


class SupportMessage(models.Model):
    id = django_mongodb_backend.fields.ObjectIdAutoField(primary_key=True)
    
    # Message lié à un utilisateur (admin ou resto)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    # ID du restaurant concerné par la discussion
    restaurant_id = models.CharField(max_length=255, verbose_name="ID du restaurant")
    
    message = models.TextField(verbose_name="Message")
    
    # Indique si c'est l'admin qui parle ou le restaurant
    is_from_admin = models.BooleanField(default=True, verbose_name="Envoyé par admin")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'support_messages'
        verbose_name = "Message de support"
        verbose_name_plural = "Messages de support"
        ordering = ['created_at']

    def __str__(self):
        return f"Message de {self.sender.username} pour resto {self.restaurant_id}"