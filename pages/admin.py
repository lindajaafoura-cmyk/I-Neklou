from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Avg
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from .models import Restaurant, UserProfile, LoyaltyPoints, LoyaltyTransaction, Review, LoyaltyReward, UserRedemption


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'city', 'status', 'is_active', 'created_at')
    list_filter = ('status', 'is_active', 'created_at', 'city')
    search_fields = ('name', 'email', 'city')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_restaurants', 'reject_restaurants', 'suspend_restaurants']

    fieldsets = (
        ('Informations principales', {
            'fields': ('user_id', 'name', 'email', 'phone')
        }),
        ('Adresse', {
            'fields': ('address', 'city', 'postal_code')
        }),
        ('Détails', {
            'fields': ('cuisine_type', 'description', 'image', 'price_range', 'rating')
        }),
        ('Statut', {
            'fields': ('status', 'is_active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def approve_restaurants(self, request, queryset):
        updated = queryset.update(status='approved', is_active=True)
        self.message_user(request, f'{updated} restaurants ont été approuvés.')
    approve_restaurants.short_description = "Approuver les restaurants sélectionnés"

    def reject_restaurants(self, request, queryset):
        updated = queryset.update(status='rejected', is_active=False)
        self.message_user(request, f'{updated} restaurants ont été rejetés.')
    reject_restaurants.short_description = "Rejeter les restaurants sélectionnés"

    def suspend_restaurants(self, request, queryset):
        updated = queryset.update(status='suspended', is_active=False)
        self.message_user(request, f'{updated} restaurants ont été suspendus.')
    suspend_restaurants.short_description = "Suspendre les restaurants sélectionnés"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'is_verified', 'loyalty_points_display', 'created_at')
    list_filter = ('user_type', 'is_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'loyalty_link')
    actions = ['verify_users', 'unverify_users', 'add_bonus_points']

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'user_type')
        }),
        ('Informations personnelles', {
            'fields': ('phone', 'address')
        }),
        ('Vérification', {
            'fields': ('is_verified',)
        }),
        ('Fidélité', {
            'fields': ('loyalty_link',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def loyalty_points_display(self, obj):
        if hasattr(obj.user, 'loyalty'):
            return f"{obj.user.loyalty.points} pts ({obj.user.loyalty.tier})"
        return "0 pts"
    loyalty_points_display.short_description = "Points fidélité"

    def loyalty_link(self, obj):
        if hasattr(obj.user, 'loyalty'):
            url = reverse('admin:pages_loyaltypoints_change', args=[obj.user.loyalty.id])
            return format_html('<a href="{}">Voir détails fidélité ({} points - {})</a>',
                             url, obj.user.loyalty.points, obj.user.loyalty.tier)
        return "Aucun programme fidélité"
    loyalty_link.short_description = "Programme fidélité"

    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} utilisateurs ont été vérifiés.')
    verify_users.short_description = "Vérifier les utilisateurs sélectionnés"

    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} utilisateurs ne sont plus vérifiés.')
    unverify_users.short_description = "Retirer la vérification"

    def add_bonus_points(self, request, queryset):
        if 'apply' in request.POST:
            points = int(request.POST.get('bonus_points', 0))
            description = request.POST.get('description', 'Points bonus administrateur')

            count = 0
            for profile in queryset:
                loyalty, created = LoyaltyPoints.objects.get_or_create(user=profile.user)
                loyalty.points += points
                loyalty.total_points_earned += points
                loyalty.save()
                loyalty.update_tier()

                LoyaltyTransaction.objects.create(
                    user=profile.user,
                    points=points,
                    transaction_type='bonus',
                    description=description
                )
                count += 1

            self.message_user(request, f'{count} utilisateurs ont reçu {points} points bonus.')
            return

        return render(request, 'admin/add_bonus_points.html', {
            'profiles': queryset,
            'title': 'Ajouter des points bonus'
        })
    add_bonus_points.short_description = "Ajouter des points bonus"


@admin.register(LoyaltyPoints)
class LoyaltyPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'tier', 'total_points_earned', 'last_updated')
    list_filter = ('tier',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('last_updated',)
    actions = ['reset_points', 'upgrade_tier']

    def reset_points(self, request, queryset):
        queryset.update(points=0, total_points_earned=0, total_points_used=0, tier='bronze')
        self.message_user(request, 'Points réinitialisés pour les utilisateurs sélectionnés.')
    reset_points.short_description = "Réinitialiser les points"

    def upgrade_tier(self, request, queryset):
        for loyalty in queryset:
            loyalty.update_tier()
            loyalty.save()
        self.message_user(request, 'Niveaux mis à jour.')
    upgrade_tier.short_description = "Mettre à jour les niveaux"


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'transaction_type', 'description', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'description')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant_name', 'rating', 'status', 'is_verified', 'helpful_count', 'created_at')
    list_filter = ('status', 'rating', 'is_verified', 'created_at')
    search_fields = ('user__username', 'restaurant_name', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_reviews', 'reject_reviews', 'verify_reviews']

    fieldsets = (
        ('Avis', {
            'fields': ('user', 'restaurant_id', 'restaurant_name', 'rating', 'comment')
        }),
        ('Statut', {
            'fields': ('status', 'is_verified', 'helpful_count')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def approve_reviews(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} avis ont été approuvés.')
    approve_reviews.short_description = "Approuver les avis sélectionnés"

    def reject_reviews(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} avis ont été rejetés.')
    reject_reviews.short_description = "Rejeter les avis sélectionnés"

    def verify_reviews(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} avis sont maintenant vérifiés.')
    verify_reviews.short_description = "Marquer comme vérifié"


@admin.register(LoyaltyReward)
class LoyaltyRewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_required', 'reward_type', 'is_active', 'stock', 'valid_until')
    list_filter = ('reward_type', 'is_active')
    search_fields = ('name', 'description')
    actions = ['duplicate_reward']

    fieldsets = (
        ('Informations', {
            'fields': ('name', 'description', 'reward_type', 'points_required')
        }),
        ('Détails de la récompense', {
            'fields': ('discount_percentage', 'free_item_description', 'voucher_code')
        }),
        ('Gestion', {
            'fields': ('is_active', 'stock', 'valid_until')
        }),
    )

    def duplicate_reward(self, request, queryset):
        for reward in queryset:
            reward.pk = None
            reward.name = f"{reward.name} (copie)"
            reward.save()
        self.message_user(request, f'{queryset.count()} récompenses ont été dupliquées.')
    duplicate_reward.short_description = "Dupliquer les récompenses"


@admin.register(UserRedemption)
class UserRedemptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'reward', 'points_spent', 'status', 'redeemed_at')
    list_filter = ('status', 'redeemed_at')
    search_fields = ('user__username', 'reward__name')
    readonly_fields = ('redeemed_at',)
    actions = ['mark_as_used', 'mark_as_expired']

    def mark_as_used(self, request, queryset):
        queryset.update(status='used', used_at=timezone.now())
        self.message_user(request, 'Récompenses marquées comme utilisées.')
    mark_as_used.short_description = "Marquer comme utilisé"

    def mark_as_expired(self, request, queryset):
        queryset.update(status='expired')
        self.message_user(request, 'Récompenses marquées comme expirées.')
    mark_as_expired.short_description = "Marquer comme expiré"