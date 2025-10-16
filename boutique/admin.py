from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Produit, Categorie, Note, Commande, CommandeItem,
    UserProfile, PanierItem, Adresse, AvisLivreur, AvisProduit
)

# ---------------------------
# Catégorie et Produit
# ---------------------------

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'icon')
    search_fields = ('nom',)


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix', 'prix_promo', 'date_creation', 'note_moyenne', 'nombre_notes')
    list_filter = ('categories', 'date_creation')
    search_fields = ('nom', 'description')
    filter_horizontal = ('categories',)
    list_editable = ('prix', 'prix_promo')
    readonly_fields = ('date_creation', 'note_moyenne', 'nombre_notes')


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
    list_display = ('commande', 'produit', 'quantite', 'prix_unitaire')
    list_filter = ('commande__statut',)
    search_fields = ('produit__nom', 'commande__user__username')


# ---------------------------
# Panier
# ---------------------------

@admin.register(PanierItem)
class PanierItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'produit', 'quantite', 'prix_total', 'date_ajout')
    list_filter = ('date_ajout',)
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
