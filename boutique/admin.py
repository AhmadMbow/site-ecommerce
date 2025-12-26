from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Produit, Categorie, Note, Commande, CommandeItem,
    UserProfile, PanierItem, Adresse, AvisLivreur, AvisProduit,
    CommandeInvite, CommandeInviteItem, Taille, ProduitTaille
)

# ---------------------------
# Tailles
# ---------------------------

@admin.register(Taille)
class TailleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ordre')
    search_fields = ('nom',)
    ordering = ('ordre', 'nom')


class ProduitTailleInline(admin.TabularInline):
    model = ProduitTaille
    extra = 1
    min_num = 0


# ---------------------------
# Catégorie et Produit
# ---------------------------

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'icon')
    search_fields = ('nom',)


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix', 'prix_promo', 'a_tailles', 'stock', 'date_creation', 'note_moyenne', 'nombre_notes')
    list_filter = ('categories', 'a_tailles', 'date_creation')
    search_fields = ('nom', 'description')
    filter_horizontal = ('categories',)
    list_editable = ('prix', 'prix_promo', 'a_tailles', 'stock')
    readonly_fields = ('date_creation', 'note_moyenne', 'nombre_notes')
    inlines = [ProduitTailleInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'description', 'image', 'categories')
        }),
        ('Prix', {
            'fields': ('prix', 'prix_promo')
        }),
        ('Stock et Tailles', {
            'fields': ('a_tailles', 'stock'),
            'description': 'Si "A tailles" est coché, gérez le stock par taille ci-dessous. Sinon, utilisez le champ Stock.'
        }),
        ('Informations', {
            'fields': ('date_creation', 'note_moyenne', 'nombre_notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProduitTaille)
class ProduitTailleAdmin(admin.ModelAdmin):
    list_display = ('produit', 'taille', 'stock')
    list_filter = ('taille', 'produit__categories')
    search_fields = ('produit__nom', 'taille__nom')
    list_editable = ('stock',)


# ---------------------------
# Notes
# ---------------------------

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('produit', 'user', 'valeur', 'date_creation')
    list_filter = ('valeur', 'date_creation')
    search_fields = ('produit__nom', 'user__username')


# ---------------------------
# Commandes et CommandeItem
# ---------------------------

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'livreur', 'date_commande', 'statut', 'total')
    list_filter = ('statut', 'date_commande')
    search_fields = ('user__username', 'livreur__username')
    readonly_fields = ('date_commande',)


@admin.register(CommandeItem)
class CommandeItemAdmin(admin.ModelAdmin):
    list_display = ('commande', 'produit', 'taille', 'quantite', 'prix_unitaire')
    list_filter = ('commande__statut', 'taille')
    search_fields = ('produit__nom', 'commande__user__username')


# ---------------------------
# Panier
# ---------------------------

@admin.register(PanierItem)
class PanierItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'produit', 'taille', 'quantite', 'prix_total', 'date_ajout')
    list_filter = ('date_ajout', 'taille')
    search_fields = ('user__username', 'produit__nom')
    readonly_fields = ('date_ajout', 'prix_total')


# ---------------------------
# Adresses
# ---------------------------

@admin.register(Adresse)
class AdresseAdmin(admin.ModelAdmin):
    list_display = ('user', 'destinataire', 'ligne1', 'ville', 'pays', 'is_default')
    list_filter = ('ville', 'pays', 'is_default')
    search_fields = ('user__username', 'destinataire', 'ligne1', 'ville')


# ---------------------------
# Avis
# ---------------------------

@admin.register(AvisLivreur)
class AvisLivreurAdmin(admin.ModelAdmin):
    list_display = ('client', 'livreur', 'note', 'date_avis')
    list_filter = ('note', 'date_avis')
    search_fields = ('client__username', 'livreur__username')


@admin.register(AvisProduit)
class AvisProduitAdmin(admin.ModelAdmin):
    list_display = ('client', 'produit', 'note', 'date_avis')
    list_filter = ('note', 'date_avis')
    search_fields = ('client__username', 'produit__nom')


# ---------------------------
# Commandes Invité
# ---------------------------

class CommandeInviteItemInline(admin.TabularInline):
    model = CommandeInviteItem
    extra = 0
    readonly_fields = ('produit', 'quantite', 'prix_unitaire')
    can_delete = False


@admin.register(CommandeInvite)
class CommandeInviteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_complet', 'email', 'telephone', 'ville', 'date_commande', 'statut', 'total', 'livreur')
    list_filter = ('statut', 'date_commande', 'ville')
    search_fields = ('nom', 'prenom', 'email', 'telephone', 'adresse')
    readonly_fields = ('date_commande',)
    inlines = [CommandeInviteItemInline]
    
    fieldsets = (
        ('Informations Client', {
            'fields': ('prenom', 'nom', 'email', 'telephone')
        }),
        ('Adresse de Livraison', {
            'fields': ('adresse', 'complement_adresse', 'ville', 'code_postal', 'latitude', 'longitude', 'adresse_gps')
        }),
        ('Commande', {
            'fields': ('date_commande', 'total', 'statut', 'livreur', 'notes')
        }),
    )


@admin.register(CommandeInviteItem)
class CommandeInviteItemAdmin(admin.ModelAdmin):
    list_display = ('commande', 'produit', 'quantite', 'prix_unitaire')
    list_filter = ('commande__statut',)
    search_fields = ('produit__nom', 'commande__email', 'commande__nom', 'commande__prenom')


# ---------------------------
# Extension du UserAdmin pour UserProfile
# ---------------------------

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


# Réenregistrement de User avec le nouveau admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
