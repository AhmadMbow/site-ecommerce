from itertools import count
from os import truncate
from functools import wraps
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, Http404
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout, update_session_auth_hash, login, authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required as staff_required
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.db.models import Q, Sum, Count, Avg
from django.db.models.functions import TruncDate, Coalesce
from django.db import transaction
from .utils import envoyer_mail_statut_commande 
from boutique.forms import (
    AdminProfileForm, AdresseForm, CategorieForm, DelivererCreateForm, 
    DelivererProfileForm, DelivererProfileUpdateForm, DelivererUserUpdateForm, 
    ProduitForm, UserUpdateForm, ProfileUpdateForm, CustomUserCreationForm, AvisLivreurForm
)
from .models import (
    Produit, Categorie, Commande, CommandeItem, PanierItem, UserProfile, 
    Note, Adresse, RoleChoices, AvisLivreur, AvisProduit, CommandeInvite, 
    CommandeInviteItem, Taille, ProduitTaille
)
from .constants import FRAIS_LIVRAISON_DEFAUT

# ===================================================================
# CLASSE WRAPPER POUR LES TAILLES AVEC STOCK
# ===================================================================

class TailleStock:
    """Wrapper pour passer les tailles avec leur stock au template"""
    def __init__(self, taille, stock):
        self.taille = taille
        self.stock = stock

# ===================================================================
# PAGE DETAIL PRODUIT
# ===================================================================

def produit_detail(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    avis = AvisProduit.objects.filter(produit=produit).select_related('client').order_by('-date_avis')
    
    # Vérifier si l'utilisateur peut noter ce produit
    peut_noter = False
    a_deja_note = False
    
    if request.user.is_authenticated:
        # Vérifier si l'utilisateur a déjà noté ce produit
        a_deja_note = AvisProduit.objects.filter(client=request.user, produit=produit).exists()
        
        # Vérifier si l'utilisateur a commandé ce produit
        a_commande = CommandeItem.objects.filter(
            commande__user=request.user,
            produit=produit,
            commande__statut__in=['LIVREE', 'EN_COURS', 'EN_ATTENTE']
        ).exists()
        
        peut_noter = a_commande and not a_deja_note
    
    # Récupérer les produits similaires (même catégorie, excluant le produit actuel)
    # Comme categories est une relation ManyToMany, on récupère les catégories du produit actuel
    categories_produit = produit.categories.all()
    
    if categories_produit.exists():
        # Récupérer les produits qui ont au moins une catégorie en commun
        produits_similaires = Produit.objects.filter(
            categories__in=categories_produit
        ).exclude(id=produit.id).distinct().order_by('-date_creation')[:6]
    else:
        # Si le produit n'a pas de catégorie, prendre les produits récents
        produits_similaires = Produit.objects.exclude(
            id=produit.id
        ).order_by('-date_creation')[:6]
    
    # Récupérer les tailles disponibles si le produit a des tailles
    tailles_disponibles = []
    if produit.a_tailles:
        tailles_disponibles = ProduitTaille.objects.filter(
            produit=produit, 
            stock__gt=0
        ).select_related('taille').order_by('taille__ordre')
    
    return render(request, 'boutique/produit_detail.html', {
        'produit': produit,
        'avis': avis,
        'peut_noter': peut_noter,
        'a_deja_note': a_deja_note,
        'produits_similaires': produits_similaires,
        'tailles_disponibles': tailles_disponibles,
    })

# ===================================================================
# FONCTIONS UTILITAIRES
# ===================================================================

def _unit_price(prod):
    """Récupère le prix unitaire d'un produit (promo ou normal)"""
    return getattr(prod, 'prix_promo', None) or getattr(prod, 'prix', 0) or 0

def _pending_choice_for_statut():
    """Récupère le choix 'en attente' pour le statut de commande"""
    try:
        field = Commande._meta.get_field('statut')
        choices = getattr(field, 'choices', []) or []
        mapping = {str(code).upper(): code for code, _ in choices}
        for key in ('EN_ATTENTE', 'EN ATTENTE', 'PENDING'):
            if key in mapping:
                return mapping[key]
    except Exception:
        pass
    return 'EN_ATTENTE'

def _get_cart_count(request):
    """Récupère le nombre d'articles dans le panier"""
    if request.user.is_authenticated:
        return PanierItem.objects.filter(user=request.user).aggregate(total=Sum('quantite'))['total'] or 0
    cart = request.session.get('panier', {})
    return sum(int(v.get('quantite', 0)) for v in cart.values())

def _merge_session_cart_to_user(request):
    """Fusionne le panier anonyme (session) dans le panier utilisateur après login."""
    if not request.user.is_authenticated:
        return
    cart = request.session.get('panier') or {}
    if not cart:
        return
    
    # Extraire les IDs de produits des clés du panier (format: "produit_id" ou "produit_id_taille_id")
    try:
        produit_ids = []
        for key in cart.keys():
            pid = key.split('_')[0] if '_' in key else key
            if str(pid).isdigit():
                produit_ids.append(int(pid))
    except Exception:
        produit_ids = []
    
    if not produit_ids:
        request.session['panier'] = {}
        request.session.modified = True
        return
    
    produits_map = {p.id: p for p in Produit.objects.filter(id__in=produit_ids)}
    
    for cart_key, data in cart.items():
        try:
            # Extraire l'ID du produit de la clé
            pid_str = cart_key.split('_')[0] if '_' in cart_key else cart_key
            pid = int(pid_str)
            
            qty = int(data.get('quantite', 0)) if isinstance(data, dict) else int(data)
            if qty <= 0:
                continue
            
            produit = produits_map.get(pid)
            if not produit:
                continue
            
            # Récupérer la taille si elle existe
            taille = None
            if isinstance(data, dict) and data.get('taille_id'):
                try:
                    taille = Taille.objects.get(pk=data['taille_id'])
                except Taille.DoesNotExist:
                    pass
            
            item, created = PanierItem.objects.get_or_create(
                user=request.user, 
                produit=produit,
                taille=taille,
                defaults={'quantite': qty}
            )
            if not created:
                # Incrémenter en base pour éviter les races
                from django.db.models import F
                item.quantite = F('quantite') + qty
                item.save(update_fields=['quantite'])
                item.refresh_from_db(fields=['quantite'])
        except Exception:
            continue
    # Vider le panier de session
    request.session['panier'] = {}
    request.session.modified = True

def is_livreur(user):
    """Vérifie si l'utilisateur est un livreur"""
    return getattr(getattr(user, 'userprofile', None), 'role', None) == RoleChoices.LIVREUR

# Fonctions pour les livreurs
def _livreur_orders_queryset(user=None):
    """Récupère TOUTES les commandes (avec et sans compte) pour un livreur"""
    from itertools import chain
    from operator import attrgetter
    
    # Récupérer les commandes classiques (utilisateurs avec compte) avec l'adresse
    commandes = list(Commande.objects.select_related('user', 'adresse', 'user__userprofile').all())
    
    # Récupérer les commandes invités (sans compte)
    commandes_invite = list(CommandeInvite.objects.all())
    
    # Combiner les deux types et trier par date de commande décroissante (plus récentes en premier)
    all_orders = sorted(
        chain(commandes, commandes_invite),
        key=lambda x: x.date_commande,
        reverse=True
    )
    
    return all_orders

def _livreur_stats(orders):
    """Calcule les statistiques pour un livreur (fonctionne avec une liste)"""
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # Utiliser la constante partagée
    FRAIS_LIVRAISON = FRAIS_LIVRAISON_DEFAUT
    
    # Convertir en liste si ce n'est pas déjà le cas
    if not isinstance(orders, list):
        orders = list(orders)
    
    # Compter les commandes par statut
    pending = len([o for o in orders if o.statut == 'EN_ATTENTE'])
    in_progress = len([o for o in orders if o.statut == 'EN_COURS'])
    completed = len([o for o in orders if o.statut == 'LIVREE'])
    
    # Commandes livrées aujourd'hui
    delivered_today = len([
        o for o in orders 
        if o.statut == 'LIVREE' and o.date_commande.date() == today
    ])
    
    # Revenus basés sur les frais de livraison
    # Seules les commandes livrées génèrent des revenus pour le livreur
    completed_orders = [o for o in orders if o.statut == 'LIVREE']
    
    # Revenus totaux = nombre de commandes livrées × frais de livraison
    revenue_total = len(completed_orders) * FRAIS_LIVRAISON
    
    # Revenus du jour = commandes livrées aujourd'hui × frais de livraison
    revenue_today = delivered_today * FRAIS_LIVRAISON
    
    # Revenus du mois
    revenue_this_month = len([
        o for o in orders 
        if o.statut == 'LIVREE' 
        and o.date_commande.month == today.month 
        and o.date_commande.year == today.year
    ]) * FRAIS_LIVRAISON
    
    return {
        'count_all': len(orders),
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'delivered_today': delivered_today,
        'revenue_total': revenue_total,
        'revenue_today': revenue_today,
        'revenue_this_month': revenue_this_month,
        'frais_livraison': FRAIS_LIVRAISON,
    }

# ===================================================================
# DÉCORATEURS PERSONNALISÉS
# ===================================================================

def admin_required(view_func):
    """Décorateur pour les vues admin uniquement"""
    @login_required
    @user_passes_test(lambda u: u.is_staff, login_url='/login/')
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper

def client_only(view_func):
    """Décorateur pour les vues clients uniquement (pas d'admin)"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

# ===================================================================
# VUES PUBLIQUES (sans authentification)
# ===================================================================

def index(request):
    """Page d'accueil - redirige selon le rôle si connecté, sinon vers la boutique"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        if is_livreur(request.user):
            return redirect('livreur_dashboard')
    return redirect('boutique')

def accueil(request):
    """Ancienne page d'accueil - redirige vers la boutique"""
    return redirect('boutique')

def boutique(request):
    """Vue boutique - liste des produits accessible à tous"""
    produits_qs = Produit.objects.all()

    # Recherche
    search = request.GET.get('search')
    if search:
        produits_qs = produits_qs.filter(Q(nom__icontains=search) | Q(description__icontains=search))

    # Filtrage par catégorie
    categorie_id = request.GET.get('categorie')
    try:
        categorie_selected_int = int(categorie_id) if categorie_id else None
    except (TypeError, ValueError):
        categorie_selected_int = None

    if categorie_selected_int:
        produits_qs = produits_qs.filter(Q(categories__id=categorie_selected_int)).distinct()

    # Tri
    tri = (request.GET.get('tri') or '').lower()
    sort = request.GET.get('sort', 'nom')

    if tri == 'populaires':
        produits_qs = produits_qs.annotate(
            total_commandees=Coalesce(
                Sum('commandeitem__quantite', filter=Q(commandeitem__commande__statut='LIVREE')),
                0
            )
        ).order_by('-total_commandees', '-date_creation')
    elif tri == 'mieux-notes':
        produits_qs = produits_qs.annotate(
            avg_note=Coalesce(Avg('notes__valeur'), 0.0),
            nb_notes=Coalesce(Count('notes'), 0)
        ).order_by('-avg_note', '-nb_notes', '-date_creation')
    elif tri == 'nouveautes':
        produits_qs = produits_qs.order_by('-date_creation')
    else:
        if sort == 'prix_asc':
            produits_qs = produits_qs.order_by('prix')
        elif sort == 'prix_desc':
            produits_qs = produits_qs.order_by('-prix')
        elif sort == 'date':
            produits_qs = produits_qs.order_by('-date_creation')
        else:
            produits_qs = produits_qs.order_by('nom')

    # Pagination
    total_count = produits_qs.count()
    per_page_param = (request.GET.get('per_page') or '').lower()
    if per_page_param == 'all':
        per_page = max(total_count, 1)
    else:
        try:
            per_page = int(request.GET.get('per_page', 12))
        except (TypeError, ValueError):
            per_page = 12

    paginator = Paginator(produits_qs, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Categorie.objects.all().order_by('nom')
    # Produits populaires: plus commandés (quantité) dans les commandes livrées
    plus_populaires = produits_qs.annotate(
        total_commandees=Sum(
            'commandeitem__quantite',
            filter=Q(commandeitem__commande__statut='LIVREE')
        )
    ).filter(total_commandees__isnull=False).order_by('-total_commandees', '-date_creation')[:8]

    # Meilleurs notés: top 3 par note moyenne puis nombre d'avis
    mieux_notes = produits_qs.annotate(
        avg_note=Avg('notes__valeur'),
        nb_notes=Count('notes')
    ).filter(avg_note__isnull=False).order_by('-avg_note', '-nb_notes', '-date_creation')[:3]

    show_all_promos = (request.GET.get('show_all_promos') == '1')
    promos_qs = produits_qs.filter(prix_promo__isnull=False)
    promotions = promos_qs if show_all_promos else promos_qs[:12]
    total_promos = promos_qs.count()

    context = {
        'produits': page_obj.object_list,
        'page_obj': page_obj,
        'categories': categories,
        'search': search,
        'current_categorie': categorie_id,
        'categorie_selected_int': categorie_selected_int,
    'current_sort': sort,
    'current_tri': tri,
        'per_page': per_page,
    'per_page_options': [12, 24, 48, 96],
        'total_count': total_count,
        'promotions': promotions,
        'total_promos': total_promos,
        'show_all_promos': show_all_promos,
        'nouveautes': produits_qs.order_by('-date_creation')[:8],
        'mieux_notes': mieux_notes,
        'plus_populaires': plus_populaires,
    }
    return render(request, 'boutique/boutique.html', context)

def wishlist(request):
    """Page Wishlist - Liste des produits favoris"""
    return render(request, 'boutique/wishlist.html')

def compare(request):
    """Page de comparaison de produits avec analyse intelligente"""
    product_ids = request.GET.get('products', '').split(',')
    product_ids = [pid for pid in product_ids if pid]
    
    produits = []
    best_product_id = None
    
    if product_ids:
        produits = list(Produit.objects.filter(id__in=product_ids).prefetch_related('categories'))
        
        # Calculer le meilleur produit basé sur plusieurs critères
        if len(produits) > 1:
            scores = []
            for p in produits:
                # Prix effectif (avec promo si disponible)
                prix_final = float(p.prix_promo) if p.prix_promo else float(p.prix)
                
                # Score basé sur : note moyenne, stock, et prix
                # Plus la note est haute, mieux c'est
                # Plus le stock est élevé, mieux c'est
                # Moins le prix est élevé, mieux c'est
                
                note_score = float(p.note_moyenne) * 20  # Note sur 100
                stock_score = min(p.stock, 20) * 2  # Stock plafonné à 20 unités = 40 points
                prix_score = 0.0
                
                # Prix inversement proportionnel (moins cher = meilleur score)
                if prix_final > 0:
                    # Normaliser le prix sur 40 points (prix le plus bas = 40 points)
                    prix_min = min([float(p2.prix_promo) if p2.prix_promo else float(p2.prix) for p2 in produits])
                    prix_score = (prix_min / prix_final) * 40
                
                total_score = note_score + stock_score + prix_score
                scores.append((p.id, total_score))
            
            # Trouver le produit avec le meilleur score
            if scores:
                best_product_id = max(scores, key=lambda x: x[1])[0]
    
    context = {
        'produits': produits,
        'product_ids': product_ids,
        'best_product_id': best_product_id,
    }
    return render(request, 'boutique/compare.html', context)

def oauth_demo(request):
    """Page de démonstration OAuth"""
    return render(request, 'boutique/oauth_demo.html')

def about(request):
    """Page à propos accessible à tous"""
    return render(request, 'boutique/about.html')

def register(request):
    """Vue d'inscription avec email et téléphone obligatoires"""
    if request.user.is_authenticated:
        return redirect('post_login_redirect')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Connexion automatique après inscription avec backend explicite
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, "Compte créé avec succès. Bienvenue !")
                return redirect('post_login_redirect')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du compte : {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

# ===================================================================
# AUTHENTIFICATION
# ===================================================================

def custom_login(request):
    """Vue de connexion personnalisée"""
    if request.user.is_authenticated:
        return redirect('post_login_redirect')

    if request.method == 'POST':
        username = request.POST.get('username') or ''
        password = request.POST.get('password') or ''
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('post_login_redirect')
        messages.error(request, "Identifiants invalides.")

    return render(request, 'registration/login.html')

def logout_view(request):
    """Vue de déconnexion simple"""
    logout(request)
    return redirect('home')

def admin_logout(request):
    """Déconnexion pour les admins"""
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('login_short')

@login_required
def dashboard(request):
    """Redirection intelligente après connexion"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    profile = getattr(request.user, 'userprofile', None)
    if getattr(profile, 'role', '').upper() == 'LIVREUR':
        return redirect('livreur_dashboard')
    return redirect('boutique')

def post_login_redirect(request):
    """Redirection après connexion: fusionne le panier session -> utilisateur, puis redirige."""
    try:
        if request.user.is_authenticated:
            _merge_session_cart_to_user(request)
    except Exception:
        # Ne bloque pas la redirection en cas d'erreur de fusion
        pass
    
    # Redirection intelligente selon le rôle
    if request.user.is_authenticated:
        # Si admin/staff -> panneau admin
        if request.user.is_staff:
            messages.success(request, f"Bienvenue {request.user.username} !")
            return redirect('admin_dashboard')
        
        # Si livreur -> dashboard livreur
        profile = getattr(request.user, 'userprofile', None)
        if profile and getattr(profile, 'role', '').upper() == 'LIVREUR':
            messages.success(request, f"Bienvenue {request.user.username} !")
            return redirect('livreur_dashboard')
        
        # Sinon -> boutique (page principale pour les clients)
        messages.success(request, f"Bienvenue {request.user.username} !")
        return redirect('boutique')
    
    # Si non authentifié (sécurité)
    return redirect('login_short')

class CustomLoginView(LoginView):
    """Vue de connexion Django personnalisée"""
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')
    
    def get_success_url(self):
        return self.success_url

@method_decorator([login_required, user_passes_test(lambda u: u.is_staff)], name='dispatch')
class AdminPasswordChangeView(PasswordChangeView):
    """Vue de changement de mot de passe pour admin"""
    template_name = 'adminpanel/change_password.html'
    success_url = '/admin-panel/profile/'
    
    def get_success_url(self):
        messages.success(self.request, 'Mot de passe modifié avec succès.')
        return super().get_success_url()

# ===================================================================
# VUES CLIENT
# ===================================================================

@login_required
def profile(request):
    """Profil utilisateur client"""
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    adresses = Adresse.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    address_form = AdresseForm()
    user_form = UserUpdateForm(instance=request.user)
    profile_form = ProfileUpdateForm(instance=profile_obj)

    if request.method == 'POST':
        section = request.POST.get('_section', '')

        if section == 'adresse_create':
            form = AdresseForm(request.POST)
            if form.is_valid():
                adr = form.save(commit=False)
                adr.user = request.user
                if not adresses.exists():
                    adr.is_default = True
                adr.save()
                messages.success(request, "Adresse ajoutée.")
                return redirect('profile')
            address_form = form

        elif 'avatar' in request.FILES:
            profile_obj.avatar = request.FILES['avatar']
            profile_obj.save(update_fields=['avatar'])
            messages.success(request, "Photo de profil mise à jour.")
            return redirect('profile')
        
        else:
            # Mise à jour des informations personnelles
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, "Profil mis à jour avec succès.")
                return redirect('profile')

    # Commandes récentes
    recent_orders = []
    try:
        recent_orders = Commande.objects.filter(user=request.user).order_by('-id')[:5]
    except Exception:
        recent_orders = []

    context = {
        'profile': profile_obj,
        'adresses': adresses,
        'address_form': address_form,
        'user_form': user_form,
        'profile_form': profile_form,
        'recent_orders': recent_orders,
    }
    return render(request, 'boutique/profile.html', context)

@login_required
def mes_commandes(request):
    """Liste des commandes de l'utilisateur"""
    # Précharger les éléments et produits pour l'affichage des détails et des évaluations
    commandes = (
        Commande.objects
        .filter(user=request.user)
        .select_related('user', 'livreur')
        .prefetch_related('items__produit')
        .order_by('-date_commande')
    )
    
    # Calculer les statistiques par statut
    commandes_livrees = commandes.filter(statut='LIVREE').count()
    commandes_en_cours = commandes.filter(statut='EN_COURS').count()
    commandes_en_attente = commandes.filter(statut='EN_ATTENTE').count()
    
    context = {
        'commandes': commandes,
        'commandes_livrees': commandes_livrees,
        'commandes_en_cours': commandes_en_cours,
        'commandes_en_attente': commandes_en_attente,
    }
    
    return render(request, 'boutique/mes_commandes.html', context)

@login_required
def annuler_commande(request, commande_id):
    """Annuler une commande (uniquement si EN_ATTENTE)"""
    from django.http import JsonResponse
    
    commande = get_object_or_404(Commande, id=commande_id, user=request.user)
    
    # Vérifier que la commande peut être annulée
    if commande.statut != 'EN_ATTENTE':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Seules les commandes en attente peuvent être annulées.'
            }, status=400)
        else:
            messages.error(request, 'Seules les commandes en attente peuvent être annulées.')
            return redirect('mes_commandes')
    
    # Annuler la commande
    commande.statut = 'ANNULEE'
    commande.save()
    
    # Restaurer les stocks (optionnel selon votre logique)
    for item in commande.items.all():
        if hasattr(item.produit, 'stock'):
            item.produit.stock += item.quantite
            item.produit.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Commande annulée avec succès.'
        })
    else:
        messages.success(request, 'Votre commande a été annulée avec succès.')
        return redirect('mes_commandes')

@login_required
def change_password(request):
    """Changement de mot de passe utilisateur"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mot de passe changé avec succès !')
            return redirect('profile')
        else:
            messages.error(request, 'Erreur dans le formulaire.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'boutique/change_password.html', {'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def noter_produit(request, produit_id):
    """Notation d'un produit par l'utilisateur.
    Règle: l'utilisateur doit avoir au moins une commande livrée contenant ce produit.
    """
    produit = get_object_or_404(Produit, id=produit_id)

    if request.method == "GET":
        # Afficher le formulaire d'avis
        return render(request, "boutique/noter_produit.html", {"produit": produit})
    
    # Vérifier que l'utilisateur a reçu au moins une commande avec ce produit
    a_recu = CommandeItem.objects.filter(
        commande__user=request.user,
        commande__statut='LIVREE',
        produit=produit
    ).exists()
    
    if not a_recu:
        messages.error(request, "Vous ne pouvez noter ce produit que si vous l'avez reçu dans une commande livrée.")
        return redirect('produit_detail', pk=produit.id)

    # Vérifier si l'utilisateur a déjà noté ce produit
    avis_existant = AvisProduit.objects.filter(client=request.user, produit=produit).exists()
    if avis_existant:
        messages.warning(request, "Vous avez déjà laissé un avis pour ce produit.")
        return redirect('produit_detail', pk=produit.id)

    # Récupérer et valider la note
    raw = request.POST.get('note', '0')
    try:
        valeur = int(raw)
    except (TypeError, ValueError):
        messages.error(request, "Note invalide.")
        return redirect('produit_detail', pk=produit.id)
    
    if valeur < 1 or valeur > 5:
        messages.error(request, "La note doit être entre 1 et 5.")
        return redirect('produit_detail', pk=produit.id)

    commentaire = request.POST.get('commentaire', '').strip()

    # Créer l'avis
    AvisProduit.objects.create(
        client=request.user,
        produit=produit,
        note=valeur,
        commentaire=commentaire
    )

    messages.success(request, "Votre avis a été enregistré avec succès. Merci pour votre retour !")
    return redirect('produit_detail', pk=produit.id)

# ===================================================================
# GESTION DU PANIER
# ===================================================================

@require_POST
def ajouter_au_panier(request, produit_id):
    produit = get_object_or_404(Produit, pk=produit_id)
    
    # Récupérer la taille si le produit a des tailles
    taille_id = request.POST.get('taille') or request.GET.get('taille')
    taille = None
    stock_disponible = produit.stock
    
    if produit.a_tailles:
        # Le produit nécessite une taille
        if not taille_id:
            return JsonResponse({
                'success': False,
                'message': 'Veuillez sélectionner une taille.',
                'requires_size': True
            }, status=400)
        
        try:
            taille = Taille.objects.get(pk=taille_id)
            # Vérifier que cette taille existe pour ce produit
            produit_taille = ProduitTaille.objects.get(produit=produit, taille=taille)
            stock_disponible = produit_taille.stock
        except (Taille.DoesNotExist, ProduitTaille.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Taille non disponible pour ce produit.',
            }, status=400)

    # Vérifier le stock disponible
    if stock_disponible <= 0:
        message = f'Désolé, {produit.nom}'
        if taille:
            message += f' (taille {taille.nom})'
        message += ' est en rupture de stock.'
        return JsonResponse({
            'success': False,
            'message': message,
            'stock': 0
        }, status=400)

    if request.user.is_authenticated:
        # Pour les utilisateurs connectés
        item, created = PanierItem.objects.get_or_create(
            user=request.user,
            produit=produit,
            taille=taille,
            defaults={'quantite': 1}
        )
        if not created:
            # Vérifier si on peut ajouter une unité de plus
            nouvelle_quantite = item.quantite + 1
            if nouvelle_quantite > stock_disponible:
                message = f'Stock insuffisant pour {produit.nom}'
                if taille:
                    message += f' (taille {taille.nom})'
                message += f'. Stock disponible: {stock_disponible}'
                return JsonResponse({
                    'success': False,
                    'message': message,
                    'stock': stock_disponible,
                    'current_cart_quantity': item.quantite
                }, status=400)
            
            item.quantite = nouvelle_quantite
            item.save(update_fields=['quantite'])
        else:
            # Nouveau produit ajouté, vérifier quand même le stock
            if stock_disponible < 1:
                item.delete()  # Supprimer l'item créé
                message = f'Désolé, {produit.nom}'
                if taille:
                    message += f' (taille {taille.nom})'
                message += ' est en rupture de stock.'
                return JsonResponse({
                    'success': False,
                    'message': message,
                    'stock': 0
                }, status=400)
        
        stock_restant = stock_disponible - item.quantite
    else:
        # Pour les utilisateurs non connectés (session)
        cart = request.session.get('panier', {})
        # Clé unique: produit_id + taille_id (si existe)
        key = f"{produit_id}_{taille_id}" if taille_id else str(produit_id)
        
        existing_data = cart.get(key, {})
        qty = int(existing_data.get('quantite', 0)) + 1
        
        # Vérifier si la quantité demandée ne dépasse pas le stock
        if qty > stock_disponible:
            message = f'Stock insuffisant pour {produit.nom}'
            if taille:
                message += f' (taille {taille.nom})'
            message += f'. Stock disponible: {stock_disponible}'
            return JsonResponse({
                'success': False,
                'message': message,
                'stock': stock_disponible,
                'current_cart_quantity': qty - 1
            }, status=400)
        
        cart[key] = {
            'quantite': qty,
            'taille_id': int(taille_id) if taille_id else None,
            'taille_nom': taille.nom if taille else None
        }
        request.session['panier'] = cart
        request.session.modified = True
        
        stock_restant = stock_disponible - qty

    count = _get_cart_count(request)
    
    # Message de succès avec indication de la taille et du stock restant
    message = f'{produit.nom}'
    if taille:
        message += f' (taille {taille.nom})'
    message += ' ajouté au panier'
    if stock_restant <= 5 and stock_restant > 0:
        message += f' (Plus que {stock_restant} disponible{"s" if stock_restant > 1 else ""})'
    
    return JsonResponse({
        'success': True,
        'message': message,
        'cart_count': count,
        'count': count,
        'stock_restant': stock_restant
    }, status=200)


def cart_count_ajax(request):
    count = _get_cart_count(request)
    return JsonResponse({
        'success': True,
        'cart_count': count,
        'count': count
    }, status=200)


# --- Fonction pour calculer le tarif de livraison ---
def calcul_livraison(distance_km):
    """
    Calcul du tarif de livraison selon la distance (en km)
    Exemple :
        - Gratuit pour <= 5 km
        - 500 FCFA par km au-delà de 5 km
    """
    if distance_km is None or distance_km <= 5:
        return 0
    return int((distance_km - 5) * 500)

# --- View du panier ---
def voir_panier(request):
    """Affichage du contenu du panier avec calcul du total et livraison (accessible à tous)"""
    items = []
    total = 0
    adresse_defaut = None
    adresses = []
    
    # Si l'utilisateur est connecté, récupérer le panier de la base de données
    if request.user.is_authenticated:
        items_qs = PanierItem.objects.select_related('produit', 'taille').filter(user=request.user)
        for it in items_qs:
            # Prix unitaire (promo si existante)
            pu = it.produit.prix_promo if it.produit.prix_promo else it.produit.prix
            sous_total = pu * it.quantite
            total += sous_total
            it.prix_total = sous_total
            items.append(it)
        
        # Récupérer les adresses de l'utilisateur
        adresses = Adresse.objects.filter(user=request.user).order_by('-is_default', '-created_at')
        adresse_defaut = adresses.filter(is_default=True).first()
        if not adresse_defaut and adresses.exists():
            adresse_defaut = adresses.first()
    else:
        # Pour les visiteurs non connectés, utiliser le panier de session
        cart = request.session.get('panier', {})
        for cart_key, data in cart.items():
            try:
                # Gérer les deux formats possibles: dict avec 'quantite' ou int direct
                if isinstance(data, dict):
                    qty = data.get('quantite', 1)
                    taille_id = data.get('taille_id')
                    taille_nom = data.get('taille_nom')
                else:
                    qty = int(data)
                    taille_id = None
                    taille_nom = None
                
                # Extraire l'ID du produit de la clé (format: "produit_id" ou "produit_id_taille_id")
                produit_id = cart_key.split('_')[0] if '_' in cart_key else cart_key
                
                produit = Produit.objects.get(id=produit_id)
                pu = produit.prix_promo if produit.prix_promo else produit.prix
                sous_total = pu * qty
                total += sous_total
                
                # Créer un objet similaire à PanierItem pour l'affichage
                class SessionCartItem:
                    def __init__(self, produit, quantite, prix_total, taille_id=None, taille_nom=None, cart_key=None):
                        self.id = produit.id
                        self.produit = produit
                        self.quantite = quantite
                        self.prix_total = prix_total
                        self.taille = None
                        self.taille_id = taille_id
                        self.taille_nom = taille_nom
                        self.cart_key = cart_key  # Pour identifier l'item unique dans la session
                items.append(SessionCartItem(produit, qty, sous_total, taille_id, taille_nom, cart_key))
            except (Produit.DoesNotExist, ValueError, TypeError):
                continue

    # Frais de livraison fixes
    shipping = 2000  # 2000 FCFA de frais de livraison fixes

    context = {
        'items': items,
        'total': total,
        'shipping': shipping,
        'cart_count': sum(i.quantite for i in items),
        'adresse_defaut': adresse_defaut,
        'adresses': adresses,
    }

    return render(request, 'boutique/panier.html', context)


@login_required
def retirer_du_panier(request, item_id):
    """Retirer un produit du panier (utilisateurs connectés uniquement)"""
    item = get_object_or_404(PanierItem, id=item_id, user=request.user)
    nom_produit = item.produit.nom
    item.delete()
    messages.success(request, f'{nom_produit} retiré du panier.')
    return redirect('panier')


def retirer_du_panier_session(request, produit_id):
    """Retirer un produit du panier de session (visiteurs non connectés)"""
    cart = request.session.get('panier', {})
    produit_id_str = str(produit_id)
    
    # Chercher la clé dans le panier (peut être produit_id ou produit_id_taille_id)
    found_key = None
    if produit_id_str in cart:
        found_key = produit_id_str
    else:
        # Chercher une clé qui commence par produit_id
        for key in list(cart.keys()):
            if key.startswith(f"{produit_id_str}_") or key == produit_id_str:
                found_key = key
                break
    
    if found_key:
        try:
            produit = Produit.objects.get(id=produit_id)
            del cart[found_key]
            request.session['panier'] = cart
            request.session.modified = True
            messages.success(request, f'{produit.nom} retiré du panier.')
        except Produit.DoesNotExist:
            del cart[found_key]
            request.session['panier'] = cart
            request.session.modified = True
            messages.error(request, 'Produit introuvable.')
    else:
        messages.error(request, 'Produit non trouvé dans le panier.')
    
    return redirect('panier')


@login_required
@require_POST
def modifier_quantite(request):
    """Modifier la quantité d'un produit dans le panier (utilisateurs connectés)"""
    try:
        item_id = int(request.POST.get('item_id'))
        nouvelle_quantite = int(request.POST.get('qty'))
        item = get_object_or_404(PanierItem, id=item_id, user=request.user)

        if nouvelle_quantite <= 0:
            nom_produit = item.produit.nom
            item.delete()
            messages.info(request, f'{nom_produit} retiré du panier.')
        else:
            item.quantite = nouvelle_quantite
            item.save()
            messages.success(request, 'Quantité mise à jour.')

    except (ValueError, TypeError):
        messages.error(request, 'Quantité invalide.')
    except Exception:
        messages.error(request, 'Erreur lors de la modification.')

    return redirect('panier')


@require_POST
def modifier_quantite_session(request):
    """Modifier la quantité d'un produit dans le panier de session (visiteurs non connectés)"""
    try:
        produit_id = str(request.POST.get('produit_id'))
        taille_id = request.POST.get('taille_id')
        nouvelle_quantite = int(request.POST.get('qty'))
        
        cart = request.session.get('panier', {})
        
        # Construire la clé du panier (format: produit_id ou produit_id_taille_id)
        cart_key = f"{produit_id}_{taille_id}" if taille_id else produit_id
        
        # Chercher la clé dans le panier
        found_key = None
        if cart_key in cart:
            found_key = cart_key
        elif produit_id in cart:
            found_key = produit_id
        else:
            # Chercher une clé qui commence par produit_id
            for key in cart.keys():
                if key.startswith(f"{produit_id}_") or key == produit_id:
                    found_key = key
                    break
        
        if found_key:
            if nouvelle_quantite <= 0:
                try:
                    produit = Produit.objects.get(id=produit_id)
                    del cart[found_key]
                    messages.info(request, f'{produit.nom} retiré du panier.')
                except Produit.DoesNotExist:
                    del cart[found_key]
            else:
                # Conserver les données existantes et mettre à jour la quantité
                existing_data = cart[found_key] if isinstance(cart[found_key], dict) else {}
                existing_data['quantite'] = nouvelle_quantite
                cart[found_key] = existing_data
                messages.success(request, 'Quantité mise à jour.')
            
            request.session['panier'] = cart
            request.session.modified = True
        else:
            messages.error(request, 'Produit non trouvé dans le panier.')

    except (ValueError, TypeError):
        messages.error(request, 'Quantité invalide.')
    except Exception as e:
        messages.error(request, 'Erreur lors de la modification.')

    return redirect('panier')


# ===================================================================
# CONFIRMATION DE COMMANDE
# ===================================================================

@login_required
@require_POST
@transaction.atomic
def confirmer_commande(request):
    """Confirmer une commande pour un utilisateur connecté"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        items = list(PanierItem.objects.select_related('produit', 'taille').filter(user=request.user))
        if not items:
            messages.error(request, "Votre panier est vide.")
            return redirect('panier')

        # Vérification du stock AVANT de créer la commande
        produits_insuffisants = []
        for it in items:
            # Vérifier le stock selon la taille ou le stock total
            if it.taille:
                try:
                    produit_taille = ProduitTaille.objects.get(produit=it.produit, taille=it.taille)
                    stock_disponible = produit_taille.stock
                except ProduitTaille.DoesNotExist:
                    stock_disponible = 0
            else:
                stock_disponible = it.produit.stock_total
            
            if stock_disponible < it.quantite:
                nom_complet = it.produit.nom
                if it.taille:
                    nom_complet += f" (taille {it.taille.nom})"
                produits_insuffisants.append({
                    'nom': nom_complet,
                    'demande': it.quantite,
                    'disponible': stock_disponible
                })
        
        if produits_insuffisants:
            # Construire le message d'erreur
            msg_parts = ["Stock insuffisant pour les produits suivants :"]
            for p in produits_insuffisants:
                if p['disponible'] == 0:
                    msg_parts.append(f"• {p['nom']}: en rupture de stock")
                else:
                    msg_parts.append(f"• {p['nom']}: demandé {p['demande']}, disponible {p['disponible']}")
            messages.error(request, " ".join(msg_parts))
            return redirect('panier')

        # Calcul du total
        total = sum(_unit_price(it.produit) * it.quantite for it in items)
        
        logger.info(f"Commande en cours pour {request.user.username}, total: {total}, items: {len(items)}")

        # Récupération de l'adresse (choix de l'utilisateur ou par défaut)
        adresse_id = request.POST.get('adresse_id')
        adresse = None
        if adresse_id:
            adresse = Adresse.objects.filter(user=request.user, id=adresse_id).first()
            logger.info(f"Adresse sélectionnée ID: {adresse_id}, trouvée: {adresse is not None}")
        else:
            adresse = Adresse.objects.filter(user=request.user, is_default=True).first()
            if not adresse:
                adresse = Adresse.objects.filter(user=request.user).first()
            logger.info(f"Adresse par défaut trouvée: {adresse is not None}")
        
        # L'adresse n'est plus obligatoire - on peut utiliser les coordonnées GPS
        # Récupération des données GPS du client
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        adresse_gps = request.POST.get('adresse_gps')
        
        logger.info(f"Données GPS - Lat: {latitude}, Long: {longitude}, Adresse GPS: {adresse_gps}")

        # Création de la commande
        cmd_kwargs = {'user': request.user, 'total': total}
        if hasattr(Commande, 'statut'):
            cmd_kwargs['statut'] = _pending_choice_for_statut()
        elif hasattr(Commande, 'status'):
            cmd_kwargs['status'] = 'pending'

        # Ajouter l'adresse si disponible
        if hasattr(Commande, 'adresse') and adresse:
            cmd_kwargs['adresse'] = adresse
        if hasattr(Commande, 'adresse_livraison') and adresse:
            cmd_kwargs['adresse_livraison'] = adresse
        
        # Ajouter les coordonnées GPS si disponibles
        if hasattr(Commande, 'latitude') and latitude:
            try:
                cmd_kwargs['latitude'] = float(latitude)
            except (ValueError, TypeError):
                logger.warning(f"Latitude invalide: {latitude}")
        
        if hasattr(Commande, 'longitude') and longitude:
            try:
                cmd_kwargs['longitude'] = float(longitude)
            except (ValueError, TypeError):
                logger.warning(f"Longitude invalide: {longitude}")
        
        if hasattr(Commande, 'adresse_gps') and adresse_gps:
            cmd_kwargs['adresse_gps'] = adresse_gps

        # Utiliser une transaction pour garantir la cohérence
        with transaction.atomic():
            logger.info(f"Création de la commande avec les paramètres: {cmd_kwargs.keys()}")
            commande = Commande.objects.create(**cmd_kwargs)
            logger.info(f"Commande créée: #{commande.id}")
            
            # Création des lignes de commande et décrémenter le stock
            for it in items:
                pu = _unit_price(it.produit)
                ci_kwargs = {'commande': commande, 'produit': it.produit, 'quantite': it.quantite}
                if hasattr(CommandeItem, 'prix_unitaire'):
                    ci_kwargs['prix_unitaire'] = pu
                elif hasattr(CommandeItem, 'prix'):
                    ci_kwargs['prix'] = pu
                
                # Ajouter la taille si disponible
                if hasattr(CommandeItem, 'taille') and it.taille:
                    ci_kwargs['taille'] = it.taille
                
                CommandeItem.objects.create(**ci_kwargs)
                
                # Décrémenter le stock selon la taille
                if it.taille:
                    try:
                        produit_taille = ProduitTaille.objects.get(produit=it.produit, taille=it.taille)
                        produit_taille.stock -= it.quantite
                        produit_taille.save(update_fields=['stock'])
                    except ProduitTaille.DoesNotExist:
                        pass
                else:
                    # Fallback: décrémenter le stock du premier ProduitTaille disponible
                    produit_tailles = ProduitTaille.objects.filter(produit=it.produit, stock__gt=0).order_by('-stock')
                    reste = it.quantite
                    for pt in produit_tailles:
                        if reste <= 0:
                            break
                        decrement = min(pt.stock, reste)
                        pt.stock -= decrement
                        pt.save(update_fields=['stock'])
                        reste -= decrement
            
            # Vider le panier
        PanierItem.objects.filter(user=request.user).delete()
        logger.info(f"Panier vidé pour l'utilisateur {request.user.username}")
    
        # Envoyer l'email après la transaction
        try:
            envoyer_mail_statut_commande(commande)
            logger.info(f"Email de confirmation envoyé pour la commande #{commande.id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email pour la commande #{commande.id}: {str(e)}")
            # Ne pas bloquer la commande si l'email échoue
        
        if 'panier' in request.session:
            request.session['panier'] = {}
            request.session.modified = True

        messages.success(request, "Commande confirmée ! Merci pour votre achat !")
        logger.info(f"Commande #{commande.id} confirmée avec succès pour {request.user.username}")
        return redirect('mes_commandes')
        
    except Exception as e:
        logger.error(f"Erreur lors de la confirmation de commande pour {request.user.username}: {str(e)}", exc_info=True)
        messages.error(request, f"Une erreur est survenue lors de la confirmation de votre commande. Veuillez réessayer ou contacter le support. Erreur: {str(e)}")
        return redirect('panier')


# ===================================================================
# COMMANDE INVITÉ (SANS COMPTE)
# ===================================================================

@require_POST
@transaction.atomic
def commande_invite(request):
    """Permet aux visiteurs non connectés de commander directement sans créer de compte"""
    from .forms import CommandeInviteForm
    from .models import CommandeInvite, CommandeInviteItem
    
    # Récupérer le panier de session
    cart = request.session.get('panier', {})
    if not cart:
        messages.error(request, "Votre panier est vide.")
        return redirect('panier')
    
    # Validation du formulaire
    form = CommandeInviteForm(request.POST)
    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
        return redirect('panier')
    
    # Récupération des produits et calcul du total
    produits_data = []
    total = 0
    produits_insuffisants = []
    
    for cart_key, data in cart.items():
        try:
            # Gérer les deux formats possibles: dict avec 'quantite' ou int direct
            if isinstance(data, dict):
                qty = data.get('quantite', 1)
                taille_id = data.get('taille_id')
            else:
                qty = int(data)
                taille_id = None
            
            # Extraire l'ID du produit de la clé (format: "produit_id" ou "produit_id_taille_id")
            produit_id = cart_key.split('_')[0] if '_' in cart_key else cart_key
            
            produit = Produit.objects.get(id=produit_id)
            
            # Vérification du stock selon la taille
            taille = None
            if taille_id:
                try:
                    taille = Taille.objects.get(id=taille_id)
                    produit_taille = ProduitTaille.objects.get(produit=produit, taille=taille)
                    stock_disponible = produit_taille.stock
                except (Taille.DoesNotExist, ProduitTaille.DoesNotExist):
                    stock_disponible = 0
            else:
                stock_disponible = produit.stock_total
            
            if stock_disponible < qty:
                nom_complet = produit.nom
                if taille:
                    nom_complet += f" (taille {taille.nom})"
                produits_insuffisants.append({
                    'nom': nom_complet,
                    'demande': qty,
                    'disponible': stock_disponible
                })
                continue
            
            prix_unitaire = produit.prix_promo if produit.prix_promo else produit.prix
            sous_total = prix_unitaire * qty
            total += sous_total
            
            produits_data.append({
                'produit': produit,
                'quantite': qty,
                'prix_unitaire': prix_unitaire,
                'taille': taille
            })
        except Produit.DoesNotExist:
            continue
    
    if produits_insuffisants:
        # Construire le message d'erreur
        msg_parts = ["Stock insuffisant pour les produits suivants :"]
        for p in produits_insuffisants:
            if p['disponible'] == 0:
                msg_parts.append(f"• {p['nom']}: en rupture de stock")
            else:
                msg_parts.append(f"• {p['nom']}: demandé {p['demande']}, disponible {p['disponible']}")
        messages.error(request, " ".join(msg_parts))
        return redirect('panier')
    
    if not produits_data:
        messages.error(request, "Aucun produit valide dans le panier.")
        return redirect('panier')
    
    # Création de la commande invité
    commande = form.save(commit=False)
    commande.total = total
    commande.save()
    
    # Création des lignes de commande et mise à jour du stock
    for data in produits_data:
        item_kwargs = {
            'commande': commande,
            'produit': data['produit'],
            'quantite': data['quantite'],
            'prix_unitaire': data['prix_unitaire']
        }
        
        # Ajouter la taille si disponible
        if hasattr(CommandeInviteItem, 'taille') and data.get('taille'):
            item_kwargs['taille'] = data['taille']
        
        CommandeInviteItem.objects.create(**item_kwargs)
        
        # Décrémenter le stock selon la taille
        if data.get('taille'):
            try:
                produit_taille = ProduitTaille.objects.get(produit=data['produit'], taille=data['taille'])
                produit_taille.stock -= data['quantite']
                produit_taille.save(update_fields=['stock'])
            except ProduitTaille.DoesNotExist:
                pass
        else:
            # Fallback: décrémenter le stock du premier ProduitTaille disponible
            produit_tailles = ProduitTaille.objects.filter(produit=data['produit'], stock__gt=0).order_by('-stock')
            reste = data['quantite']
            for pt in produit_tailles:
                if reste <= 0:
                    break
                decrement = min(pt.stock, reste)
                pt.stock -= decrement
                pt.save(update_fields=['stock'])
                reste -= decrement
    
    # Vider le panier de session
    request.session['panier'] = {}
    request.session.modified = True
    
    # Envoyer l'email de confirmation pour la commande invité
    from .utils import envoyer_mail_statut_commande
    envoyer_mail_statut_commande(commande, is_guest=True)
    
    messages.success(request, f"Commande {commande.numero_commande} confirmée ! Vous recevrez un email de confirmation à {commande.email}.")
    return redirect('boutique')


# ===================================================================
# GESTION DES ADRESSES
# ===================================================================

@login_required
@require_POST
def adresse_defaut(request, pk):
    """Définir une adresse par défaut"""
    adr = get_object_or_404(Adresse, pk=pk, user=request.user)
    Adresse.objects.filter(user=request.user, is_default=True).update(is_default=False)
    adr.is_default = True
    adr.save(update_fields=['is_default'])
    messages.success(request, "Adresse définie par défaut.")
    return HttpResponseRedirect(reverse('profile'))

@login_required
@require_http_methods(['POST'])
def adresse_supprimer(request, pk):
    """Supprimer une adresse"""
    adr = get_object_or_404(Adresse, pk=pk, user=request.user)
    was_default = adr.is_default
    adr.delete()
    if was_default:
        reste = Adresse.objects.filter(user=request.user).order_by('-created_at').first()
        if reste:
            reste.is_default = True
            reste.save(update_fields=['is_default'])
    messages.success(request, "Adresse supprimée.")
    return HttpResponseRedirect(reverse('profile'))

@login_required
@require_http_methods(['POST'])
def adresse_modifier(request, pk):
    """Modifier une adresse"""
    adr = get_object_or_404(Adresse, pk=pk, user=request.user)
    form = AdresseForm(request.POST, instance=adr)
    if form.is_valid():
        form.save()
        messages.success(request, "Adresse mise à jour.")
    else:
        messages.error(request, "Vérifiez le formulaire d'adresse.")
    return HttpResponseRedirect(reverse('profile'))

# ===================================================================
# VUES LIVREUR
# ===================================================================

@login_required
def livreur_profile(request):
    """Profil du livreur avec gestion complète"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # Créer un profil si inexistant
        profile = UserProfile.objects.create(user=request.user)
    
    # Calculer les statistiques du livreur
    orders = _livreur_orders_queryset(request.user)
    stats = _livreur_stats(orders)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'personal_info':
            # Mise à jour des informations personnelles
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            
            # Mise à jour du profil
            profile.phone = request.POST.get('phone', '')
            profile.address = request.POST.get('address', '')
            
            # Gestion de l'upload photo
            if 'photo' in request.FILES:
                profile.photo = request.FILES['photo']
            
            profile.save()
            messages.success(request, 'Vos informations personnelles ont été mises à jour avec succès.')
            return redirect('livreur_profile')
            
        elif form_type == 'vehicle_info':
            # Mise à jour des informations du véhicule
            profile.vehicle_type = request.POST.get('vehicle_type', '')
            profile.vehicle_plate = request.POST.get('vehicle_plate', '')
            profile.vehicle_model = request.POST.get('vehicle_model', '')
            profile.vehicle_color = request.POST.get('vehicle_color', '')
            profile.save()
            
            messages.success(request, 'Les informations de votre véhicule ont été mises à jour avec succès.')
            return redirect('livreur_profile')
            
        elif form_type == 'password_change':
            # Changement de mot de passe
            old_password = request.POST.get('old_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if not request.user.check_password(old_password):
                messages.error(request, 'Le mot de passe actuel est incorrect.')
            elif new_password1 != new_password2:
                messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
            elif len(new_password1) < 8:
                messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
            else:
                request.user.set_password(new_password1)
                request.user.save()
                # Re-authentifier l'utilisateur
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Votre mot de passe a été changé avec succès.')
                return redirect('livreur_profile')
    
    # Calculer les stats pour l'affichage
    total_livraisons = len(orders)
    livraisons_reussies = len([o for o in orders if o.statut == 'LIVREE'])
    taux_reussite = round((livraisons_reussies / total_livraisons * 100) if total_livraisons > 0 else 0)
    revenus_generes = livraisons_reussies * 1000  # 1000 FCFA par livraison
    
    context = {
        'profile': profile,
        'stats': stats,
        'total_livraisons': total_livraisons,
        'taux_reussite': taux_reussite,
        'revenus_generes': revenus_generes,
        'active_tab': 'profile'
    }
    return render(request, 'livreur/livreur_profile.html', context)

@login_required
def livreur_dashboard(request):
    """Tableau de bord du livreur"""
    orders = _livreur_orders_queryset(request.user)
    stats = _livreur_stats(orders)
    
    # Commandes récentes pour le dashboard
    recent_orders = orders[:5]
    
    context = {
        'orders': recent_orders, 
        'stats': stats,
        'recent_orders': recent_orders,
        'active_tab': 'dashboard'
    }
    return render(request, 'livreur/dashboard.html', context)

@login_required
def livreur_orders(request):
    """Liste complète des commandes pour le livreur"""
    orders = _livreur_orders_queryset(request.user)
    stats = _livreur_stats(orders)
    
    # Filtrage par statut si nécessaire
    status_filter = request.GET.get('status')
    if status_filter:
        orders = [o for o in orders if o.statut == status_filter]
    
    context = {
        'orders': orders,
        'stats': stats,
        'status_filter': status_filter,
        'active_tab': 'orders'
    }
    return render(request, 'livreur/orders.html', context)

@login_required
def livreur_stats(request):
    """Statistiques détaillées du livreur"""
    from django.utils import timezone
    from decimal import Decimal
    
    orders = _livreur_orders_queryset(request.user)
    stats = _livreur_stats(orders)
    
    FRAIS_LIVRAISON = Decimal('2000')  # Frais de livraison fixes
    
    # Calculer les statistiques mensuelles manuellement (liste au lieu de QuerySet)
    from collections import defaultdict
    monthly_data = defaultdict(int)
    
    for order in orders:
        if order.statut == 'LIVREE':
            month_key = order.date_commande.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_data[month_key] += 1
    
    # Convertir en liste de dictionnaires
    monthly_stats = [
        {
            'month': month,
            'count': count,
            'revenue': count * FRAIS_LIVRAISON
        }
        for month, count in sorted(monthly_data.items())
    ]
    
    # Commandes à encaisser (EN_COURS et LIVREE)
    orders_to_collect = [
        o for o in orders 
        if o.statut in ['EN_COURS', 'LIVREE']
    ][:10]
    
    context = {
        'stats': stats,
        'monthly_stats': monthly_stats,
        'orders_count': len(orders),
        'orders_to_collect': orders_to_collect,
        'today': timezone.now(),
        'active_tab': 'stats'
    }
    return render(request, 'livreur/stats.html', context)

@login_required
@user_passes_test(is_livreur)
def livreur_order_detail(request, pk):
    """Détail d'une commande pour le livreur (gère les deux types)"""
    order = None
    items = []
    is_guest_order = False
    
    # Vérifier le paramètre type dans l'URL
    order_type = request.GET.get('type', 'user')
    
    if order_type == 'guest':
        # Commande invité UNIQUEMENT
        try:
            order = CommandeInvite.objects.get(pk=pk)
            items = list(CommandeInviteItem.objects.select_related('produit').filter(commande=order))
            is_guest_order = True
        except CommandeInvite.DoesNotExist:
            from django.http import Http404
            raise Http404(f"Commande invité #{pk} introuvable")
    else:
        # Commande normale UNIQUEMENT
        try:
            order = Commande.objects.select_related('user').get(pk=pk)
            items = list(CommandeItem.objects.select_related('produit').filter(commande=order))
        except Commande.DoesNotExist:
            from django.http import Http404
            raise Http404(f"Commande #{pk} introuvable")
    
    # Calculer les totaux pour chaque item
    for it in items:
        unit = getattr(it, 'prix_unitaire', None) or getattr(it, 'prix', None) or 0
        qty = getattr(it, 'quantite', 0) or 0
        it.unit_price = unit
        it.line_total = unit * qty

    return render(request, 'livreur/order_detail.html', {
        'order': order, 
        'items': items,
        'is_guest_order': is_guest_order
    })

@login_required
@user_passes_test(is_livreur)
@require_POST
def livreur_order_accept(request, pk):
    """Accepter une commande (supporte les deux types)"""
    # Déterminer le type de commande
    order_type = request.POST.get('type') or request.GET.get('type') or 'user'
    
    if order_type == 'guest':
        order = get_object_or_404(CommandeInvite, pk=pk)
        is_guest = True
    else:
        order = get_object_or_404(Commande, pk=pk)
        is_guest = False

    if hasattr(order, 'livreur') and not getattr(order, 'livreur', None):
        order.livreur = request.user

    if getattr(order, 'statut', None) == 'EN_ATTENTE':
        statut_precedent = order.statut
        order.statut = 'EN_COURS'
        update_fields = ['statut']
        if hasattr(order, 'livreur'):
            update_fields.append('livreur')
        order.save(update_fields=update_fields)
        
        # Envoyer l'email de notification EN_COURS
        from .utils import envoyer_mail_statut_commande
        envoyer_mail_statut_commande(order, statut_precedent=statut_precedent, is_guest=is_guest)
        
        messages.success(request, f"Commande {order.numero_commande} acceptée.")
    else:
        messages.info(request, f"Commande {order.numero_commande} déjà {order.statut or 'traitée'}.")

    return redirect(request.POST.get('next') or 'livreur_orders')

@login_required
@user_passes_test(is_livreur)
@require_POST
def livreur_order_update_status(request, pk):
    """Mettre à jour le statut d'une commande (gère les deux types)"""
    from .utils import send_delivery_email_with_receipt
    
    # Chercher dans les deux types de commandes
    order = None
    is_guest = False
    
    # Vérifier le type de commande - priorité au POST, puis GET
    order_type = request.POST.get('type') or request.GET.get('type') or 'user'
    
    # Debug
    print(f"[DEBUG] livreur_order_update_status: pk={pk}, order_type={order_type}")
    
    if order_type == 'guest':
        # Commande invité UNIQUEMENT
        try:
            order = CommandeInvite.objects.get(pk=pk)
            is_guest = True
            print(f"[DEBUG] Trouvé CommandeInvite: {order.numero_commande}, statut={order.statut}")
        except CommandeInvite.DoesNotExist:
            messages.error(request, f"Commande invité #{pk} introuvable.")
            return redirect(request.POST.get('next') or 'livreur_orders')
    else:
        # Commande normale UNIQUEMENT
        try:
            order = Commande.objects.get(pk=pk)
            print(f"[DEBUG] Trouvé Commande: {order.numero_commande}, statut={order.statut}")
        except Commande.DoesNotExist:
            messages.error(request, f"Commande #{pk} introuvable.")
            return redirect(request.POST.get('next') or 'livreur_orders')
    
    action = request.POST.get('action', '')
    current_status = getattr(order, 'statut', None)
    
    print(f"[DEBUG] Action={action}, current_status={current_status}")
    
    if action == 'accept' and current_status == 'EN_ATTENTE':
        # Accepter la commande
        if hasattr(order, 'livreur') and not getattr(order, 'livreur', None):
            order.livreur = request.user
        
        statut_precedent = order.statut
        order.statut = 'EN_COURS'
        update_fields = ['statut']
        if hasattr(order, 'livreur'):
            update_fields.append('livreur')
        
        order.save(update_fields=update_fields)
        
        # Envoyer l'email de notification EN_COURS
        from .utils import envoyer_mail_statut_commande
        envoyer_mail_statut_commande(order, statut_precedent=statut_precedent, is_guest=is_guest)
        
        messages.success(request, f"Commande #{order.id} acceptée.")
        
    elif action == 'complete' and current_status == 'EN_COURS':
        # Marquer comme livrée
        order.statut = 'LIVREE'
        update_fields = ['statut']
        
        # Ajouter la date de livraison si le champ existe
        if hasattr(order, 'date_livraison'):
            order.date_livraison = timezone.now()
            update_fields.append('date_livraison')
        
        order.save(update_fields=update_fields)
        
        # Envoyer l'email de notification LIVREE
        from .utils import envoyer_mail_statut_commande
        envoyer_mail_statut_commande(order, statut_precedent='EN_COURS', is_guest=is_guest)
        
        messages.success(request, f"Commande #{order.id} marquée comme livrée.")
        
        # ✨ Envoyer l'email avec le reçu PDF au client
        try:
            email_sent = send_delivery_email_with_receipt(order, is_guest=is_guest)
            if email_sent:
                messages.success(request, f"📧 Reçu PDF envoyé au client par email.")
            else:
                messages.warning(request, f"⚠️ Le reçu PDF n'a pas pu être envoyé.")
        except Exception as e:
            messages.warning(request, f"⚠️ Erreur lors de l'envoi du reçu PDF: {str(e)}")
            print(f"Erreur envoi reçu PDF: {e}")
            import traceback
            traceback.print_exc()
        
    else:
        messages.warning(request, f"Action '{action}' non autorisée pour la commande #{order.id} (statut: {current_status})")

    return redirect(request.POST.get('next') or 'livreur_orders')

# ===================================================================
# VUES ADMIN
# ===================================================================

@admin_required
def admin_dashboard(request):
    """Tableau de bord administrateur"""
    total_products = Produit.objects.count()
    # Compter toutes les commandes (clients + invités)
    total_orders = Commande.objects.count() + CommandeInvite.objects.count()
    total_users = User.objects.count()
    # Revenus de toutes les commandes
    revenue_clients = Commande.objects.aggregate(total=Sum('total'))['total'] or 0
    revenue_invites = CommandeInvite.objects.aggregate(total=Sum('total'))['total'] or 0
    revenue = revenue_clients + revenue_invites

    # Commandes par jour (clients)
    per_day_clients = (
        Commande.objects
        .annotate(day=TruncDate('date_commande'))
        .values('day')
        .annotate(c=Count('id'))
        .order_by('day')
    )
    
    # Commandes par jour (invités)
    per_day_invites = (
        CommandeInvite.objects
        .annotate(day=TruncDate('date_commande'))
        .values('day')
        .annotate(c=Count('id'))
        .order_by('day')
    )
    
    # Fusionner les données par jour
    daily_counts = {}
    for d in per_day_clients:
        if d['day']:
            daily_counts[d['day']] = daily_counts.get(d['day'], 0) + d['c']
    for d in per_day_invites:
        if d['day']:
            daily_counts[d['day']] = daily_counts.get(d['day'], 0) + d['c']
    
    # Trier par date
    sorted_days = sorted(daily_counts.keys())
    chart_days = [d.strftime('%d/%m') for d in sorted_days]
    chart_counts = [daily_counts[d] for d in sorted_days]
    
    # Top produits (clients + invités)
    top_clients = (
        CommandeItem.objects
        .values('produit__nom')
        .annotate(qty=Sum('quantite'))
    )
    top_invites = (
        CommandeInviteItem.objects
        .values('produit__nom')
        .annotate(qty=Sum('quantite'))
    )
    
    # Fusionner les top produits
    product_totals = {}
    for item in top_clients:
        if item['produit__nom']:
            product_totals[item['produit__nom']] = product_totals.get(item['produit__nom'], 0) + item['qty']
    for item in top_invites:
        if item['produit__nom']:
            product_totals[item['produit__nom']] = product_totals.get(item['produit__nom'], 0) + item['qty']
    
    # Trier et prendre les 5 premiers
    top_products = sorted(product_totals.items(), key=lambda x: x[1], reverse=True)[:5]
    top_products = [{'produit__nom': name, 'qty': qty} for name, qty in top_products]
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_users': total_users,
        'revenue': revenue,
        'chart_days': json.dumps(chart_days),
        'chart_counts': json.dumps(chart_counts),
        'top_products': top_products,
        'recent_orders': Commande.objects.order_by('-date_commande')[:10],
    }
    return render(request, 'adminpanel/dashboard.html', context)

@admin_required
def admin_profile(request):
    """Profil administrateur"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = AdminProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profil mis à jour avec succès!")
            return redirect("admin_profile")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = AdminProfileForm(instance=profile)
    
    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "profile": profile,
    }
    return render(request, "adminpanel/profile.html", context)

@admin_required
def admin_products(request):
    """Gestion des produits"""
    qs = Produit.objects.all().order_by('-date_creation')
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Récupérer toutes les catégories pour les filtres
    categories = Categorie.objects.all().order_by('nom')
    
    # Calculer les statistiques de stock en tenant compte des tailles
    all_products = Produit.objects.all()
    total_products = all_products.count()
    
    # Compter les tailles par niveau de stock
    tailles_out_of_stock = ProduitTaille.objects.filter(stock=0).count()
    tailles_low_stock = ProduitTaille.objects.filter(stock__gt=0, stock__lt=5).count()
    
    # Produits en stock = tous les produits avec au moins une taille en stock
    products_in_stock = 0
    for p in all_products:
        if p.stock_total > 0:
            products_in_stock += 1
    
    return render(request, 'adminpanel/products.html', {
        'produits': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'categories': categories,
        'total_products': total_products,
        'products_in_stock': products_in_stock,
        'products_low_stock': tailles_low_stock,  # Nombre de tailles avec stock bas
        'products_out_of_stock': tailles_out_of_stock,  # Nombre de tailles en rupture
        'tailles_out_of_stock': tailles_out_of_stock,
    })

@admin_required
def admin_categories(request):
    """Gestion des catégories"""
    categories = Categorie.objects.all().order_by('nom')
    return render(request, 'adminpanel/categories.html', {'categories': categories})

# CRUD Produits
@staff_required
def admin_product_create(request):
    """Création d'un produit"""
    form = ProduitForm(request.POST or None, request.FILES or None)
    all_tailles = Taille.objects.all().order_by('ordre')
    
    # Préparer les tailles avec stock 0 pour l'affichage
    tailles_avec_stock = []
    for taille in all_tailles:
        tailles_avec_stock.append({
            'taille': taille,
            'stock': 0
        })
    
    if request.method == 'POST' and form.is_valid():
        produit = form.save(commit=False)
        # Forcer a_tailles à True (toujours activé)
        produit.a_tailles = True
        produit.save()
        form.save_m2m()  # Sauvegarder les relations many-to-many (catégories)
        
        # Sauvegarder les stocks par taille (toujours)
        for taille in all_tailles:
            stock_key = f'taille_stock_{taille.id}'
            stock_value = request.POST.get(stock_key, 0)
            try:
                stock_value = int(stock_value)
            except ValueError:
                stock_value = 0
            
            ProduitTaille.objects.update_or_create(
                produit=produit,
                taille=taille,
                defaults={'stock': stock_value}
            )
        
        messages.success(request, "Produit créé avec succès.")
        
        # Vérifier si on doit continuer l'édition
        if 'save_continue' in request.POST:
            return redirect('admin_product_update', pk=produit.pk)
        return redirect('admin_products')
    
    # Préparer les tailles avec un stock initial de 0 (utiliser TailleStock pour le template)
    tailles_avec_stock = [TailleStock(taille, 0) for taille in all_tailles]
    
    return render(request, 'adminpanel/product_form.html', {
        'form': form, 
        'mode': 'create',
        'all_tailles': all_tailles,
        'tailles': tailles_avec_stock,
    })

@staff_required
def admin_product_update(request, pk):
    """Modification d'un produit"""
    produit = get_object_or_404(Produit, pk=pk)
    form = ProduitForm(request.POST or None, request.FILES or None, instance=produit)
    all_tailles = Taille.objects.all().order_by('ordre')
    
    # Récupérer les tailles existantes pour ce produit
    tailles_produit = ProduitTaille.objects.filter(produit=produit).select_related('taille').order_by('taille__ordre')
    
    # Créer un dictionnaire des stocks existants
    stocks_existants = {pt.taille.id: pt.stock for pt in tailles_produit}
    
    if request.method == 'POST' and form.is_valid():
        produit = form.save(commit=False)
        # Forcer a_tailles à True (toujours activé)
        produit.a_tailles = True
        produit.save()
        form.save_m2m()  # Sauvegarder les relations many-to-many (catégories)
        
        # Sauvegarder les stocks par taille (toujours)
        for taille in all_tailles:
            stock_key = f'taille_stock_{taille.id}'
            stock_value = request.POST.get(stock_key, 0)
            try:
                stock_value = int(stock_value)
            except ValueError:
                stock_value = 0
            
            # Mettre à jour ou créer l'entrée ProduitTaille
            ProduitTaille.objects.update_or_create(
                produit=produit,
                taille=taille,
                defaults={'stock': stock_value}
            )
        
        messages.success(request, "Produit modifié avec succès.")
        
        # Vérifier si on doit continuer l'édition
        if 'save_continue' in request.POST:
            return redirect('admin_product_update', pk=produit.pk)
        return redirect('admin_products')
    
    # Préparer les tailles avec leurs stocks pour l'affichage (utiliser TailleStock pour le template)
    tailles_avec_stock = [
        TailleStock(taille, stocks_existants.get(taille.id, 0)) 
        for taille in all_tailles
    ]
    
    return render(request, 'adminpanel/product_form.html', {
        'form': form, 
        'mode': 'update', 
        'produit': produit,
        'all_tailles': all_tailles,
        'tailles': tailles_avec_stock,
    })

@staff_required
def admin_product_delete(request, pk):
    """Suppression d'un produit"""
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        produit.delete()
        messages.success(request, "Produit supprimé.")
        return redirect('admin_products')
    return render(request, 'adminpanel/product_confirm_delete.html', {'produit': produit})

# CRUD Catégories
@staff_required
def admin_category_create(request):
    """Création d'une catégorie"""
    if request.method == 'POST':
        form = CategorieForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie créée avec succès.")
            return redirect('admin_categories')
    else:
        form = CategorieForm()
    return render(request, 'adminpanel/category_form.html', {'form': form, 'mode': 'create'})

@staff_required
def admin_category_update(request, pk):
    """Modification d'une catégorie"""
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        form = CategorieForm(request.POST, request.FILES, instance=categorie)
        # Gestion de la suppression d'image
        if request.POST.get('remove_image') == '1':
            if categorie.image:
                categorie.image.delete(save=False)
                categorie.image = None
                categorie.save()
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie modifiée avec succès.")
            return redirect('admin_categories')
    else:
        form = CategorieForm(instance=categorie)
    return render(request, 'adminpanel/category_form.html', {'form': form, 'mode': 'update', 'category': categorie})

@staff_required
def admin_category_delete(request, pk):
    """Suppression d'une catégorie"""
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        categorie.delete()
        messages.success(request, "Catégorie supprimée.")
        return redirect('admin_categories')
    return render(request, 'adminpanel/category_confirm_delete.html', {'categorie': categorie})

@staff_required
def admin_category_delete_image(request, pk):
    """Suppression de l'image d'une catégorie via AJAX"""
    from django.http import JsonResponse
    if request.method == 'POST':
        categorie = get_object_or_404(Categorie, pk=pk)
        if categorie.image:
            categorie.image.delete(save=False)
            categorie.image = None
            categorie.save()
            return JsonResponse({'success': True, 'message': 'Image supprimée avec succès'})
        return JsonResponse({'success': False, 'message': 'Aucune image à supprimer'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

# Gestion des livreurs
@admin_required
def admin_livreurs_list(request):
    """Liste des livreurs avec leurs statistiques réelles"""
    from django.db.models import Count, Q, Avg
    from datetime import datetime, timedelta
    
    q = request.GET.get('q', '')
    qs = UserProfile.objects.select_related('user').filter(role=RoleChoices.LIVREUR)
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(phone__icontains=q))
    
    # Enrichir chaque livreur avec ses statistiques
    deliverers_with_stats = []
    now = timezone.now()
    month_ago = now - timedelta(days=30)
    
    for profile in qs:
        livreur_user = profile.user
        
        # Nombre total de commandes livrées
        total_deliveries = Commande.objects.filter(
            livreur=livreur_user,
            statut__in=['LIVREE', 'TERMINEE']
        ).count()
        
        # Commandes en cours
        ongoing_deliveries = Commande.objects.filter(
            livreur=livreur_user,
            statut__in=['EN_LIVRAISON', 'ASSIGNEE']
        ).count()
        
        # Livraisons ce mois
        monthly_deliveries = Commande.objects.filter(
            livreur=livreur_user,
            statut__in=['LIVREE', 'TERMINEE'],
            date_commande__gte=month_ago
        ).count()
        
        # Note moyenne du livreur (avis clients)
        avg_rating = AvisLivreur.objects.filter(
            livreur=livreur_user
        ).aggregate(avg=Avg('note'))['avg'] or 0
        
        # Nombre d'avis reçus
        total_reviews = AvisLivreur.objects.filter(livreur=livreur_user).count()
        
        deliverers_with_stats.append({
            'profile': profile,
            'total_deliveries': total_deliveries,
            'ongoing_deliveries': ongoing_deliveries,
            'monthly_deliveries': monthly_deliveries,
            'avg_rating': round(avg_rating, 2) if avg_rating else 0,
            'total_reviews': total_reviews,
        })
    
    # Statistiques globales
    total_livreurs = len(deliverers_with_stats)
    active_livreurs = sum(1 for d in deliverers_with_stats if d['profile'].user.is_active)
    total_all_deliveries = sum(d['total_deliveries'] for d in deliverers_with_stats)
    total_monthly_deliveries = sum(d['monthly_deliveries'] for d in deliverers_with_stats)
    
    context = {
        'deliverers': deliverers_with_stats,
        'q': q,
        'stats': {
            'total_livreurs': total_livreurs,
            'active_livreurs': active_livreurs,
            'total_deliveries': total_all_deliveries,
            'monthly_deliveries': total_monthly_deliveries,
        }
    }
    
    return render(request, 'adminpanel/deliverers.html', context)

@admin_required
def admin_livreurs_create(request):
    """Création d'un livreur"""
    if request.method == 'POST':
        form = DelivererCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Livreur {user.username} créé.")
            return redirect('admin_livreurs_list')
    else:
        form = DelivererCreateForm()
    return render(request, 'adminpanel/deliverer_form.html', {'form': form, 'mode': 'create'})

@admin_required
def admin_livreurs_edit(request, user_id):
    """Modification d'un livreur"""
    user = get_object_or_404(User, pk=user_id)
    profile = get_object_or_404(UserProfile, user=user, role=RoleChoices.LIVREUR)
    if request.method == 'POST':
        uform = DelivererUserUpdateForm(request.POST, instance=user)
        pform = DelivererProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            messages.success(request, "Livreur mis à jour.")
            return redirect('admin_livreurs_list')
    else:
        uform = DelivererUserUpdateForm(instance=user)
        pform = DelivererProfileUpdateForm(instance=profile)
    return render(request, 'adminpanel/deliverer_form.html', {'uform': uform, 'pform': pform, 'mode': 'update', 'deliverer': user})

@admin_required
def admin_livreurs_toggle_active(request, user_id):
    """Activer/désactiver un livreur"""
    user = get_object_or_404(User, pk=user_id)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    messages.success(request, f"Statut de {user.username} mis à jour.")
    return redirect('admin_livreurs_list')

# Gestion des clients
@admin_required
def admin_clients_list(request):
    """Liste des clients avec marquage automatique des notifications"""
    from boutique.models import NotificationAdminVue
    from datetime import timedelta
    
    clients_list = User.objects.filter(is_staff=False).select_related('userprofile').order_by('-date_joined')
    
    search = request.GET.get('q')
    if search:
        clients_list = clients_list.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Date limite pour "nouveau" (dernières 24h)
    date_limite = timezone.now() - timedelta(hours=24)
    
    # Récupérer les nouveaux clients
    nouveaux_clients = clients_list.filter(date_joined__gte=date_limite)
    
    # Marquer automatiquement tous les nouveaux clients comme vus par cet admin
    for client in nouveaux_clients:
        NotificationAdminVue.objects.get_or_create(
            admin=request.user,
            type_notification='NOUVEAU_CLIENT',
            objet_id=client.id
        )
    
    paginator = Paginator(clients_list, 20)
    page_number = request.GET.get('page')
    clients = paginator.get_page(page_number)
    
    context = {
        'clients': clients,
        'search': search,
        'total_clients': clients_list.count(),
        'nouveaux_clients_count': nouveaux_clients.count(),
    }
    return render(request, 'adminpanel/clients_list.html', context)

@admin_required
def admin_client_toggle_active(request, user_id):
    """Activer/désactiver un client"""
    client = get_object_or_404(User, id=user_id, is_staff=False)
    client.is_active = not client.is_active
    client.save()
    
    status = "activé" if client.is_active else "désactivé"
    messages.success(request, f"Client {client.username} {status}.")
    return redirect('admin_clients_list')

@admin_required
def admin_client_detail(request, user_id):
    """Détail d'un client"""
    client = get_object_or_404(User, id=user_id, is_staff=False)
    profile = getattr(client, 'userprofile', None)
    
    context = {
        'client': client,
        'profile': profile,
    }
    return render(request, 'adminpanel/client_detail.html', context)

@admin_required
def admin_send_email_client(request, user_id):
    """Envoyer un email à un client depuis le panneau admin"""
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        client = get_object_or_404(User, id=user_id, is_staff=False)
        
        if not client.email:
            return JsonResponse({'success': False, 'message': 'Ce client n\'a pas d\'adresse email'})
        
        # Récupérer les données du formulaire
        data = json.loads(request.body)
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        if not subject:
            return JsonResponse({'success': False, 'message': 'Le sujet est requis'})
        if not message:
            return JsonResponse({'success': False, 'message': 'Le message est requis'})
        
        client_name = client.first_name or client.username
        
        # Message texte brut (important pour éviter le spam)
        text_message = f"""Bonjour {client_name},

{message}

---
Cordialement,
L'équipe SadibouShop

Cet email vous a été envoyé par SadibouShop.
Si vous avez des questions, n'hésitez pas à nous contacter à {settings.DEFAULT_FROM_EMAIL}
"""
        
        # Construire le message HTML avec logo SadibouShop
        html_message = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, Helvetica, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    <!-- Header avec Logo SadibouShop -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 25px 30px; text-align: center;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <td align="center">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="padding-right: 12px; vertical-align: middle;">
                                                    <div style="width: 45px; height: 45px; background: linear-gradient(135deg, #ffc107 0%, #e6ac00 100%); border-radius: 10px; text-align: center; line-height: 45px;">
                                                        <span style="font-size: 24px;">👔</span>
                                                    </div>
                                                </td>
                                                <td style="vertical-align: middle;">
                                                    <h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 0.5px;">
                                                        SADIBOU<span style="color: #ffc107;">SHOP</span>
                                                    </h1>
                                                    <p style="color: #888888; margin: 2px 0 0 0; font-size: 10px; letter-spacing: 2px; text-transform: uppercase;">
                                                        Mode & Tendances
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 35px 30px;">
                            <p style="color: #333333; font-size: 16px; line-height: 1.5; margin: 0 0 20px 0;">
                                Bonjour <strong>{client_name}</strong>,
                            </p>
                            <div style="color: #555555; font-size: 15px; line-height: 1.7; white-space: pre-wrap;">{message}</div>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #1a1a1a; padding: 25px 30px; text-align: center;">
                            <p style="color: #ffc107; font-size: 16px; font-weight: 700; margin: 0 0 5px 0;">
                                SADIBOU<span style="color: #ffffff;">SHOP</span>
                            </p>
                            <p style="color: #888888; font-size: 11px; margin: 0 0 15px 0; letter-spacing: 1px;">
                                MODE & TENDANCES
                            </p>
                            <p style="color: #666666; font-size: 12px; line-height: 1.6; margin: 0;">
                                Cordialement,<br>
                                <strong style="color: #888;">L'équipe SadibouShop</strong>
                            </p>
                            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #333;">
                                <p style="color: #555555; font-size: 11px; margin: 0;">
                                    Pour toute question : {settings.DEFAULT_FROM_EMAIL}
                                </p>
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
        
        # Utiliser EmailMultiAlternatives pour un meilleur contrôle des headers
        email = EmailMultiAlternatives(
            subject=subject,  # Sans préfixe pour éviter le look "spam"
            body=text_message,
            from_email=f"SadibouShop <{settings.DEFAULT_FROM_EMAIL}>",
            to=[client.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
        )
        
        # Ajouter la version HTML
        email.attach_alternative(html_message, "text/html")
        
        # Headers supplémentaires pour améliorer la délivrabilité
        email.extra_headers = {
            'X-Priority': '3',  # Priorité normale
            'X-Mailer': 'SadibouShop Mailer',
        }
        
        # Envoyer l'email
        email.send(fail_silently=False)
        
        return JsonResponse({
            'success': True, 
            'message': f'Email envoyé avec succès à {client.email}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Données invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur lors de l\'envoi: {str(e)}'})


@admin_required
def admin_send_mass_email(request):
    """Envoyer un email promotionnel à tous les clients avec possibilité d'ajouter une image"""
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    from email.mime.image import MIMEImage
    import base64
    import uuid
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        image = request.FILES.get('image')
        
        if not subject:
            return JsonResponse({'success': False, 'message': 'Le sujet est requis'})
        if not message:
            return JsonResponse({'success': False, 'message': 'Le message est requis'})
        
        # Récupérer tous les clients actifs avec email
        clients = User.objects.filter(is_staff=False, is_active=True).exclude(email='').exclude(email__isnull=True)
        
        if not clients.exists():
            return JsonResponse({'success': False, 'message': 'Aucun client avec email trouvé'})
        
        # Préparer l'image si fournie
        image_cid = None
        image_data = None
        if image:
            image_cid = f"product_image_{uuid.uuid4().hex[:8]}"
            image_data = image.read()
            image_content_type = image.content_type
        
        success_count = 0
        error_count = 0
        
        for client in clients:
            try:
                client_name = client.first_name or client.username
                
                # Message texte brut
                text_message = f"""Bonjour {client_name},

{message}

Visitez notre boutique : https://sadiboushop.com

---
Cordialement,
L'equipe SadibouShop

SadibouShop - Votre boutique de confiance
Email: {settings.DEFAULT_FROM_EMAIL}

Vous recevez cet email car vous etes client chez SadibouShop.
Pour ne plus recevoir nos emails, repondez a ce message avec "STOP".
"""
                
                # Construire le message HTML avec image - VERSION ANTI-SPAM
                image_html = ""
                if image_cid:
                    image_html = f'''
                    <tr>
                        <td style="padding: 20px 30px; text-align: center;">
                            <img src="cid:{image_cid}" alt="Nouveau produit SadibouShop" style="max-width: 100%; height: auto; border-radius: 8px;">
                        </td>
                    </tr>
                    '''
                
                html_message = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, Helvetica, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 30px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    <!-- Header avec Logo SadibouShop -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 25px 30px; text-align: center;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <td align="center">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="padding-right: 12px; vertical-align: middle;">
                                                    <div style="width: 45px; height: 45px; background: linear-gradient(135deg, #ffc107 0%, #e6ac00 100%); border-radius: 10px; text-align: center; line-height: 45px;">
                                                        <span style="font-size: 24px;">👔</span>
                                                    </div>
                                                </td>
                                                <td style="vertical-align: middle;">
                                                    <h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 0.5px;">
                                                        SADIBOU<span style="color: #ffc107;">SHOP</span>
                                                    </h1>
                                                    <p style="color: #888888; margin: 2px 0 0 0; font-size: 10px; letter-spacing: 2px; text-transform: uppercase;">
                                                        Mode & Tendances
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 30px;">
                            <p style="color: #333333; font-size: 16px; line-height: 1.5; margin: 0 0 20px 0;">
                                Bonjour {client_name},
                            </p>
                            <div style="color: #444444; font-size: 15px; line-height: 1.7; white-space: pre-wrap;">{message}</div>
                        </td>
                    </tr>
                    <!-- Image -->
                    {image_html}
                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 20px 30px 30px 30px; text-align: center;">
                            <a href="https://sadiboushop.com" style="display: inline-block; background: linear-gradient(135deg, #ffc107 0%, #e6ac00 100%); color: #1a1a1a; text-decoration: none; padding: 14px 35px; border-radius: 8px; font-weight: bold; font-size: 15px; box-shadow: 0 4px 15px rgba(255,193,7,0.3);">
                                Visiter notre boutique
                            </a>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #1a1a1a; padding: 25px 30px; text-align: center;">
                            <p style="color: #ffc107; font-size: 16px; font-weight: 700; margin: 0 0 5px 0;">
                                SADIBOU<span style="color: #ffffff;">SHOP</span>
                            </p>
                            <p style="color: #888888; font-size: 11px; margin: 0 0 15px 0; letter-spacing: 1px;">
                                MODE & TENDANCES
                            </p>
                            <p style="color: #666666; font-size: 12px; line-height: 1.6; margin: 0;">
                                Cordialement,<br>
                                <strong style="color: #888;">L'équipe SadibouShop</strong>
                            </p>
                            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #333;">
                                <p style="color: #555555; font-size: 10px; margin: 0;">
                                    SadibouShop - Votre boutique de confiance<br>
                                    Contact: {settings.DEFAULT_FROM_EMAIL}<br><br>
                                    Vous recevez cet email car vous etes inscrit sur SadibouShop.<br>
                                    Pour vous desabonner, repondez "STOP" a cet email.
                                </p>
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
                
                # Créer l'email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=f"SadibouShop <{settings.DEFAULT_FROM_EMAIL}>",
                    to=[client.email],
                    reply_to=[settings.DEFAULT_FROM_EMAIL],
                )
                
                # Ajouter la version HTML
                email.attach_alternative(html_message, "text/html")
                email.mixed_subtype = 'related'
                
                # Attacher l'image si présente
                if image_data:
                    mime_image = MIMEImage(image_data)
                    mime_image.add_header('Content-ID', f'<{image_cid}>')
                    mime_image.add_header('Content-Disposition', 'inline', filename='produit.jpg')
                    email.attach(mime_image)
                
                # Headers
                email.extra_headers = {
                    'X-Priority': '3',
                    'X-Mailer': 'SadibouShop Newsletter',
                    'List-Unsubscribe': f'<mailto:{settings.DEFAULT_FROM_EMAIL}?subject=Unsubscribe>',
                }
                
                email.send(fail_silently=False)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Erreur envoi à {client.email}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'Email envoyé à {success_count} client(s) avec succès!',
            'details': {
                'success': success_count,
                'errors': error_count,
                'total': clients.count()
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})


# Gestion des commandes
@staff_required
def admin_orders_list(request):
    """Liste des commandes pour l'admin (avec et sans compte)"""
    from itertools import chain
    from boutique.models import NotificationAdminVue
    
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')

    # Récupérer les IDs des commandes déjà vues par cet admin
    commandes_vues_ids = set(NotificationAdminVue.objects.filter(
        admin=request.user,
        type_notification='NOUVELLE_COMMANDE'
    ).values_list('objet_id', flat=True))
    
    commandes_invites_vues_ids = set(NotificationAdminVue.objects.filter(
        admin=request.user,
        type_notification='NOUVELLE_COMMANDE_INVITE'
    ).values_list('objet_id', flat=True))

    # Récupérer les commandes classiques
    orders = Commande.objects.select_related('user').all()
    if q:
        orders = orders.filter(
            Q(id__icontains=q) |
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)
        )
    if status and status != '':
        orders = orders.filter(statut=status)
    
    # Récupérer les commandes invités
    orders_invite = CommandeInvite.objects.all()
    if q:
        orders_invite = orders_invite.filter(
            Q(id__icontains=q) |
            Q(prenom__icontains=q) |
            Q(nom__icontains=q) |
            Q(email__icontains=q)
        )
    if status and status != '':
        orders_invite = orders_invite.filter(statut=status)
    
    # Marquer chaque commande si elle est "nouvelle" (non vue et en attente/en cours)
    orders_list = list(orders)
    for order in orders_list:
        order.is_new = (
            order.id not in commandes_vues_ids and 
            order.statut in ['EN_ATTENTE', 'EN_COURS']
        )
    
    orders_invite_list = list(orders_invite)
    for order in orders_invite_list:
        order.is_new = (
            order.id not in commandes_invites_vues_ids and 
            order.statut in ['EN_ATTENTE', 'EN_COURS']
        )
    
    # Combiner et trier par date décroissante
    all_orders = sorted(
        chain(orders_list, orders_invite_list),
        key=lambda x: x.date_commande,
        reverse=True
    )

    # Calculer les stats sur les deux types de commandes
    total_commandes = Commande.objects.count() + CommandeInvite.objects.count()
    total_pending = Commande.objects.filter(statut='EN_ATTENTE').count() + CommandeInvite.objects.filter(statut='EN_ATTENTE').count()
    total_in_progress = Commande.objects.filter(statut='EN_COURS').count() + CommandeInvite.objects.filter(statut='EN_COURS').count()
    total_completed = Commande.objects.filter(statut='LIVREE').count() + CommandeInvite.objects.filter(statut='LIVREE').count()
    
    revenue_user = Commande.objects.filter(statut='LIVREE').aggregate(Sum('total'))['total__sum'] or 0
    revenue_guest = CommandeInvite.objects.filter(statut='LIVREE').aggregate(Sum('total'))['total__sum'] or 0
    total_revenue = revenue_user + revenue_guest

    stats = {
        'all': total_commandes,
        'pending': total_pending,
        'in_progress': total_in_progress,
        'completed': total_completed,
        'revenue': total_revenue,
    }
    
    return render(request, 'adminpanel/orders_list.html', {'orders': all_orders, 'stats': stats, 'q': q, 'status_filter': status})

@staff_required
def admin_order_detail(request, pk):
    """Détail d'une commande pour l'admin (gère les deux types)"""
    from boutique.models import NotificationAdminVue
    
    order = None
    items = []
    is_guest_order = False
    
    # Vérifier le type de commande
    order_type = request.GET.get('type', 'user')
    
    if order_type == 'guest':
        try:
            order = CommandeInvite.objects.get(pk=pk)
            items = list(CommandeInviteItem.objects.select_related('produit').filter(commande=order))
            is_guest_order = True
            
            # Marquer comme vue si pas encore fait
            NotificationAdminVue.objects.get_or_create(
                admin=request.user,
                type_notification='NOUVELLE_COMMANDE_INVITE',
                objet_id=pk
            )
        except CommandeInvite.DoesNotExist:
            try:
                order = Commande.objects.select_related('user').get(pk=pk)
                items = list(CommandeItem.objects.select_related('produit').filter(commande=order))
                
                # Marquer comme vue
                NotificationAdminVue.objects.get_or_create(
                    admin=request.user,
                    type_notification='NOUVELLE_COMMANDE',
                    objet_id=pk
                )
            except Commande.DoesNotExist:
                raise Http404("Commande introuvable")
    else:
        try:
            order = Commande.objects.select_related('user').get(pk=pk)
            items = list(CommandeItem.objects.select_related('produit').filter(commande=order))
            
            # Marquer comme vue
            NotificationAdminVue.objects.get_or_create(
                admin=request.user,
                type_notification='NOUVELLE_COMMANDE',
                objet_id=pk
            )
        except Commande.DoesNotExist:
            try:
                order = CommandeInvite.objects.get(pk=pk)
                items = list(CommandeInviteItem.objects.select_related('produit').filter(commande=order))
                is_guest_order = True
                
                # Marquer comme vue
                NotificationAdminVue.objects.get_or_create(
                    admin=request.user,
                    type_notification='NOUVELLE_COMMANDE_INVITE',
                    objet_id=pk
                )
            except CommandeInvite.DoesNotExist:
                raise Http404("Commande introuvable")

    for it in items:
        unit = getattr(it, 'prix_unitaire', None)
        if unit is None:
            unit = getattr(it, 'prix', None)
        if unit is None:
            unit = 0
        it.unit_price = unit
        it.line_total = unit * (getattr(it, 'quantite', 0) or 0)

    return render(request, 'adminpanel/order_detail.html', {
        'order': order, 
        'items': items,
        'is_guest_order': is_guest_order
    })

@staff_required
def admin_cancel_order(request, pk):
    """Annuler une commande (clients ou invités) et envoyer un email de notification"""
    order_type = request.GET.get('type', 'user')
    
    # Déterminer le type de commande
    if order_type == 'guest':
        order = get_object_or_404(CommandeInvite, pk=pk)
        is_guest = True
        redirect_url = 'admin_orders'
    else:
        order = get_object_or_404(Commande, pk=pk)
        is_guest = False
        redirect_url = 'admin_orders'
    
    # Vérifier que la commande n'est pas déjà livrée
    if order.statut == 'LIVREE':
        messages.error(request, 'Impossible d\'annuler une commande déjà livrée.')
        return redirect(redirect_url)
    
    # Vérifier que la commande n'est pas déjà annulée
    if order.statut == 'ANNULEE':
        messages.warning(request, 'Cette commande est déjà annulée.')
        return redirect(redirect_url)
    
    if request.method == 'POST':
        # Sauvegarder l'ancien statut
        ancien_statut = order.statut
        
        # Annuler la commande
        order.statut = 'ANNULEE'
        order.save()
        
        # Envoyer l'email d'annulation
        try:
            envoyer_mail_statut_commande(order, statut_precedent=ancien_statut, is_guest=is_guest)
            messages.success(request, f'La commande {order.numero_commande} a été annulée et un email a été envoyé au client.')
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email d'annulation: {e}")
            messages.success(request, f'La commande {order.numero_commande} a été annulée. (Email non envoyé)')
        
        return redirect(redirect_url)
    
    return redirect(redirect_url)

@login_required
def livreur_change_password(request):
    """Changement de mot de passe pour livreur"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mot de passe changé avec succès !')
            return redirect('livreur_profile')
        else:
            messages.error(request, 'Erreur dans le formulaire.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'livreur/change_password.html', {'form': form})


# ---------------------------
# Vue pour donner un avis sur le livreur
# ---------------------------
@login_required
def donner_avis_livreur(request, commande_id):
    """
    Permet à un client de donner un avis sur le livreur d'une commande livrée.
    Compatible avec le template personnalisé d'avis étoilé.
    """
    commande = get_object_or_404(Commande, id=commande_id, user=request.user)

    # ✅ Vérifie si la commande a un livreur
    if not hasattr(commande, 'livreur') or commande.livreur is None:
        messages.error(request, "Cette commande n’a pas de livreur attribué.")
        return redirect('mes_commandes')

    # ✅ Vérifie si un avis a déjà été donné
    avis_existant = AvisLivreur.objects.filter(client=request.user, livreur=commande.livreur).first()
    if avis_existant:
        messages.info(request, "Vous avez déjà donné un avis sur ce livreur.")
        return redirect('mes_commandes')

    # ✅ Traitement du formulaire
    if request.method == 'POST':
        note = request.POST.get('note')
        commentaire = request.POST.get('commentaire', '').strip()
        criteria = request.POST.getlist('criteria')  # Récupérer les critères cochés

        if not note:
            messages.error(request, "Veuillez donner une note avant d'envoyer.")
            return redirect(request.path)

        # Ajouter les critères au commentaire s'ils existent
        if criteria and not commentaire:
            criteria_texts = {
                'ponctuel': 'Ponctuel',
                'aimable': 'Aimable',
                'professionnel': 'Professionnel',
                'soigne': 'Colis soigné'
            }
            criteria_str = ', '.join([criteria_texts.get(c, c) for c in criteria])
            commentaire = f"Points forts : {criteria_str}."
        elif criteria:
            # Ajouter les critères en complément du commentaire
            criteria_texts = {
                'ponctuel': 'Ponctuel',
                'aimable': 'Aimable',
                'professionnel': 'Professionnel',
                'soigne': 'Colis soigné'
            }
            criteria_str = ', '.join([criteria_texts.get(c, c) for c in criteria])
            commentaire = f"{commentaire}\n\nPoints forts : {criteria_str}."

        # Création de l'avis
        AvisLivreur.objects.create(
            client=request.user,
            livreur=commande.livreur,
            note=int(note),
            commentaire=commentaire
        )

        messages.success(request, "Merci pour votre évaluation ! 😊")
        return redirect('mes_commandes')

    # Calculer les statistiques du livreur
    avis_livreur = AvisLivreur.objects.filter(livreur=commande.livreur)
    note_moyenne = avis_livreur.aggregate(Avg('note'))['note__avg']
    nombre_livraisons = Commande.objects.filter(livreur=commande.livreur, statut='LIVREE').count()

    # ✅ Affichage du formulaire
    return render(request, 'boutique/avis_livreur.html', {
        'livreur': commande.livreur,
        'commande': commande,
        'note_moyenne': note_moyenne,
        'nombre_livraisons': nombre_livraisons,
    })




# Calcule du tarif de livraison selon la distance 
import math
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Coordonnées du dépôt
DEPOT_LAT = 14.6940
DEPOT_LON = -17.4441

def distance_km(lat1, lon1, lat2, lon2):
    """
    Calcul de la distance entre deux points GPS (Haversine)
    """
    R = 6371  # rayon de la Terre en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@csrf_exempt  # nécessaire pour AJAX si CSRF token envoyé correctement
def calculer_shipping(request):
    if request.method == "POST":
        try:
            lat = float(request.POST.get('latitude', 0))
            lon = float(request.POST.get('longitude', 0))
        except ValueError:
            return JsonResponse({'error': 'Coordonnées invalides'}, status=400)

        dist = distance_km(lat, lon, DEPOT_LAT, DEPOT_LON)

        # Exemple de tarif par tranche
        if dist <= 5:
            shipping = 500
        elif dist <= 10:
            shipping = 1000
        else:
            shipping = 2000

        return JsonResponse({'shipping': shipping, 'distance_km': round(dist, 2)})

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


from .models import AvisProduit
@login_required
def donner_avis_produit(request, item_id):
    """Permet de donner un avis sur un produit d'une commande livrée.
    L'item référencé est un CommandeItem (ligne de commande), pas un PanierItem.
    """
    # Récupérer la ligne de commande appartenant à l'utilisateur
    item = get_object_or_404(
        CommandeItem.objects.select_related('commande', 'produit'),
        id=item_id,
        commande__user=request.user,
    )

    # Autoriser l'avis uniquement lorsque la commande est livrée
    if getattr(item.commande, 'statut', None) != 'LIVREE':
        messages.error(request, "Vous pourrez donner un avis une fois la commande livrée.")
        return redirect('mes_commandes')

    if request.method == 'POST':
        # Valider la note
        raw_note = request.POST.get('note', '')
        try:
            note = int(raw_note)
        except (TypeError, ValueError):
            messages.error(request, "Note invalide.")
            return redirect(request.path)

        if note < 1 or note > 5:
            messages.error(request, "La note doit être comprise entre 1 et 5.")
            return redirect(request.path)

        commentaire = (request.POST.get('commentaire') or '').strip()

        # Éviter les doublons: un avis par client et produit
        AvisProduit.objects.update_or_create(
            client=request.user,
            produit=item.produit,
            defaults={
                'note': note,
                'commentaire': commentaire,
            }
        )

        messages.success(request, "Merci pour votre avis !")
        return redirect('mes_commandes')

    return render(request, 'boutique/donner_avis_produit.html', {'item': item})

# ========================================================================
# VUES ADMIN - GESTION DES AVIS
# ========================================================================

@admin_required
def admin_avis(request):
    """Gestion des avis des produits et livreurs"""
    from django.db.models import Q
    from django.core.paginator import Paginator
    
    # Type d'avis à afficher (produits ou livreurs)
    type_avis = request.GET.get('type', 'produits')
    
    if type_avis == 'livreurs':
        # Avis des livreurs
        avis_query = AvisLivreur.objects.select_related('client', 'livreur').order_by('-date_avis')
        
        # Filtrage par note
        note_filter = request.GET.get('note')
        if note_filter and note_filter.isdigit():
            avis_query = avis_query.filter(note=int(note_filter))
        
        # Recherche par nom du livreur ou client
        search = request.GET.get('search')
        if search:
            avis_query = avis_query.filter(
                Q(livreur__username__icontains=search) |
                Q(livreur__first_name__icontains=search) |
                Q(livreur__last_name__icontains=search) |
                Q(client__username__icontains=search) |
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search)
            )
        
        # Statistiques pour les livreurs
        total_avis = avis_query.count()
        note_moyenne = avis_query.aggregate(Avg('note'))['note__avg'] or 0
        avis_positifs = avis_query.filter(note__gte=4).count()
        avis_negatifs = avis_query.filter(note__lt=3).count()
        
    else:
        # Avis des produits (par défaut)
        avis_query = AvisProduit.objects.select_related('client', 'produit').order_by('-date_avis')
        
        # Filtrage par note
        note_filter = request.GET.get('note')
        if note_filter and note_filter.isdigit():
            avis_query = avis_query.filter(note=int(note_filter))
        
        # Recherche par nom du produit ou client
        search = request.GET.get('search')
        if search:
            avis_query = avis_query.filter(
                Q(produit__nom__icontains=search) |
                Q(client__username__icontains=search) |
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search) |
                Q(commentaire__icontains=search)
            )
        
        # Statistiques pour les produits
        total_avis = avis_query.count()
        note_moyenne = avis_query.aggregate(Avg('note'))['note__avg'] or 0
        avis_positifs = avis_query.filter(note__gte=4).count()
        avis_negatifs = avis_query.filter(note__lt=3).count()
    
    # Pagination
    paginator = Paginator(avis_query, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Statistiques générales
    total_avis_produits = AvisProduit.objects.count()
    total_avis_livreurs = AvisLivreur.objects.count()
    
    context = {
        'avis': page_obj.object_list,
        'page_obj': page_obj,
        'type_avis': type_avis,
        'note_filter': note_filter,
        'search': search or '',
        'total_avis': total_avis,
        'note_moyenne': round(note_moyenne, 1),
        'avis_positifs': avis_positifs,
        'avis_negatifs': avis_negatifs,
        'total_avis_produits': total_avis_produits,
        'total_avis_livreurs': total_avis_livreurs,
        'notes_choices': range(1, 6),
    }
    
    return render(request, 'adminpanel/avis_list.html', context)

@admin_required
def admin_avis_delete(request, avis_id):
    """Supprimer un avis (produit ou livreur)"""
    type_avis = request.GET.get('type', 'produits')
    
    if type_avis == 'livreurs':
        avis = get_object_or_404(AvisLivreur, id=avis_id)
        messages.success(request, f"L'avis sur le livreur {avis.livreur.get_full_name() or avis.livreur.username} a été supprimé.")
    else:
        avis = get_object_or_404(AvisProduit, id=avis_id)
        messages.success(request, f"L'avis sur le produit {avis.produit.nom} a été supprimé.")
    
    avis.delete()
    
    return redirect(f"{reverse('admin_avis')}?type={type_avis}")

@admin_required
def admin_avis_marquer_examine(request, avis_id):
    """Marquer un avis comme examiné"""
    type_avis = request.GET.get('type', 'produits')
    
    if type_avis == 'livreurs':
        avis = get_object_or_404(AvisLivreur, id=avis_id)
        avis.examine = not avis.examine  # Toggle
        avis.save()
        if avis.examine:
            messages.success(request, f"L'avis a été marqué comme examiné.")
        else:
            messages.info(request, f"L'avis a été marqué comme non examiné.")
    else:
        avis = get_object_or_404(AvisProduit, id=avis_id)
        avis.examine = not avis.examine  # Toggle
        avis.save()
        if avis.examine:
            messages.success(request, f"L'avis a été marqué comme examiné.")
        else:
            messages.info(request, f"L'avis a été marqué comme non examiné.")
    
    return redirect(f"{reverse('admin_avis')}?type={type_avis}")

@admin_required
def admin_avis_marquer_tous_examines(request):
    """Marquer tous les avis comme examinés"""
    type_avis = request.GET.get('type', 'produits')
    
    if type_avis == 'livreurs':
        count = AvisLivreur.objects.filter(examine=False).update(examine=True)
        messages.success(request, f"{count} avis de livreurs ont été marqués comme examinés.")
    else:
        count = AvisProduit.objects.filter(examine=False).update(examine=True)
        messages.success(request, f"{count} avis de produits ont été marqués comme examinés.")
    
    return redirect(f"{reverse('admin_avis')}?type={type_avis}")

# ========================================================================
# VUES - MESSAGERIE SUPPORT CLIENT
# ========================================================================

def contact_support(request):
    """Formulaire de contact pour les clients et visiteurs"""
    if request.method == 'POST':
        sujet = request.POST.get('sujet')
        message_texte = request.POST.get('message')
        priorite = request.POST.get('priorite', 'NORMALE')
        nom_visiteur = request.POST.get('nom_visiteur', '')
        email_contact = request.POST.get('email_contact', '')
        telephone_contact = request.POST.get('telephone_contact', '')
        
        # Si l'utilisateur est connecté, utiliser ses infos
        if request.user.is_authenticated:
            email_contact = request.POST.get('email_contact', request.user.email) or request.user.email
        
        if not sujet or not message_texte:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('contact_support')
        
        # Valider l'email pour les visiteurs
        if not request.user.is_authenticated and not email_contact:
            messages.error(request, "Veuillez fournir une adresse email pour que nous puissions vous répondre.")
            return redirect('contact_support')
        
        # Créer le message
        from boutique.models import MessageSupport
        message_support = MessageSupport.objects.create(
            client=request.user if request.user.is_authenticated else None,
            nom_visiteur=nom_visiteur if not request.user.is_authenticated else None,
            sujet=sujet,
            message=message_texte,
            priorite=priorite,
            email_contact=email_contact,
            telephone_contact=telephone_contact
        )
        
        # Déterminer le nom pour l'email
        if request.user.is_authenticated:
            client_nom = request.user.get_full_name() or request.user.username
        else:
            client_nom = nom_visiteur or 'Visiteur'
        
        # Envoyer un email de confirmation au client
        try:
            from django.core.mail import send_mail
            
            html_message = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 0; }}
                    .header {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: white; padding: 25px 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .logo-container {{ display: inline-block; }}
                    .logo-icon {{ display: inline-block; width: 40px; height: 40px; background: linear-gradient(135deg, #ffc107 0%, #e6ac00 100%); border-radius: 10px; text-align: center; line-height: 40px; vertical-align: middle; margin-right: 10px; }}
                    .logo-text {{ display: inline-block; vertical-align: middle; }}
                    .logo-text h2 {{ color: #ffffff; margin: 0; font-size: 22px; font-weight: 800; }}
                    .logo-text h2 span {{ color: #ffc107; }}
                    .logo-tagline {{ color: #888888; margin: 0; font-size: 9px; letter-spacing: 2px; text-transform: uppercase; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .message-box {{ background: white; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                    .info-box {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }}
                    .footer {{ text-align: center; margin-top: 30px; padding: 25px 30px; background: #1a1a1a; color: #666; font-size: 12px; border-radius: 0 0 10px 10px; }}
                    .footer-logo {{ color: #ffc107; font-weight: 700; font-size: 14px; margin: 0 0 15px 0; }}
                    .footer-logo span {{ color: #ffffff; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo-container">
                            <span class="logo-icon">👔</span>
                            <div class="logo-text">
                                <h2>SADIBOU<span>SHOP</span></h2>
                                <p class="logo-tagline">Mode & Tendances</p>
                            </div>
                        </div>
                        <h1 style="margin: 15px 0 0 0; font-size: 18px;">✅ Votre demande a été reçue</h1>
                    </div>
                    <div class="content">
                        <p>Bonjour <strong>{client_nom}</strong>,</p>
                        
                        <p>Nous avons bien reçu votre demande de support. Notre équipe va l'examiner et vous répondra dans les plus brefs délais.</p>
                        
                        <div class="message-box">
                            <h3 style="color: #1a1a1a; margin-top: 0;">📋 Récapitulatif de votre demande :</h3>
                            <p><strong>Numéro de ticket :</strong> #{message_support.id}</p>
                            <p><strong>Sujet :</strong> {sujet}</p>
                            <p><strong>Priorité :</strong> {message_support.get_priorite_display()}</p>
                            <p><strong>Votre message :</strong></p>
                            <p style="white-space: pre-wrap; background: #f5f5f5; padding: 15px; border-radius: 5px;">{message_texte}</p>
                        </div>
                        
                        <div class="info-box">
                            <p style="margin: 0;"><strong>⏱️ Temps de réponse moyen :</strong> Moins de 2 heures pendant les heures ouvrables</p>
                        </div>
                        
                        <p>Vous recevrez un email dès que notre équipe aura répondu à votre demande.</p>
                        
                        <p style="margin-top: 30px;">
                            Cordialement,<br>
                            <strong>L'équipe Support SadibouShop</strong>
                        </p>
                    </div>
                    <div class="footer">
                        <p class="footer-logo">SADIBOU<span>SHOP</span></p>
                        <p>Référence du ticket : #{message_support.id}</p>
                        <p>Cet email a été envoyé automatiquement suite à votre demande de support.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_message = f"""
Bonjour {client_nom},

Nous avons bien reçu votre demande de support. Notre équipe va l'examiner et vous répondra dans les plus brefs délais.

RÉCAPITULATIF DE VOTRE DEMANDE :
- Numéro de ticket : #{message_support.id}
- Sujet : {sujet}
- Priorité : {message_support.get_priorite_display()}

VOTRE MESSAGE :
{message_texte}

Temps de réponse moyen : Moins de 2 heures pendant les heures ouvrables

Vous recevrez un email dès que notre équipe aura répondu à votre demande.

Cordialement,
L'équipe Support

Référence du ticket : #{message_support.id}
            """
            
            from django.conf import settings
            send_mail(
                subject=f"Confirmation de votre demande de support - Ticket #{message_support.id}",
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_contact],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de confirmation : {e}")
        
        messages.success(request, "Votre message a été envoyé avec succès ! Nous vous répondrons dans les plus brefs délais.")
        
        # Rediriger selon le type d'utilisateur
        if request.user.is_authenticated:
            return redirect('mes_commandes')
        else:
            return redirect('home')
    
    return render(request, 'boutique/contact_support.html')

@admin_required
def admin_messagerie(request):
    """Page admin pour gérer les messages de support"""
    from boutique.models import MessageSupport
    from django.db.models import Q, Count
    
    # Filtres
    statut_filter = request.GET.get('statut')
    priorite_filter = request.GET.get('priorite')
    search = request.GET.get('search')
    
    # Récupérer les messages
    messages_query = MessageSupport.objects.select_related('client').annotate(
        nb_reponses=Count('reponses')
    ).order_by('-date_creation')
    
    # Appliquer les filtres
    if statut_filter:
        messages_query = messages_query.filter(statut=statut_filter)
    if priorite_filter:
        messages_query = messages_query.filter(priorite=priorite_filter)
    if search:
        messages_query = messages_query.filter(
            Q(sujet__icontains=search) |
            Q(message__icontains=search) |
            Q(client__username__icontains=search) |
            Q(client__email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(messages_query, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Statistiques
    total_messages = MessageSupport.objects.count()
    messages_nouveaux = MessageSupport.objects.filter(statut='NOUVEAU').count()
    messages_en_cours = MessageSupport.objects.filter(statut='EN_COURS').count()
    messages_resolus = MessageSupport.objects.filter(statut='RESOLU').count()
    messages_fermes = MessageSupport.objects.filter(statut='FERME').count()
    messages_non_lus = MessageSupport.objects.filter(lu=False).count()
    
    context = {
        'messages_list': page_obj.object_list,
        'page_obj': page_obj,
        'statut_filter': statut_filter,
        'priorite_filter': priorite_filter,
        'search': search or '',
        'total_messages': total_messages,
        'stats': {
            'nouveau': messages_nouveaux,
            'en_cours': messages_en_cours,
            'resolu': messages_resolus,
            'ferme': messages_fermes,
            'non_lus': messages_non_lus,
        },
        'statuts': MessageSupport.STATUT_CHOICES,
        'priorites': MessageSupport.PRIORITE_CHOICES,
    }
    
    return render(request, 'adminpanel/messagerie.html', context)

@admin_required
def admin_message_detail(request, message_id):
    """Voir les détails d'un message et répondre"""
    from boutique.models import MessageSupport, ReponseSupport
    
    message_support = get_object_or_404(
        MessageSupport.objects.select_related('client').prefetch_related('reponses__auteur'),
        id=message_id
    )
    
    # Marquer comme lu
    if not message_support.lu:
        message_support.lu = True
        message_support.save(update_fields=['lu'])
    
    # Traiter la soumission
    if request.method == 'POST':
        # Répondre au message
        contenu = request.POST.get('contenu')
        if contenu:
            ReponseSupport.objects.create(
                message=message_support,
                auteur=request.user,
                contenu=contenu,
                est_admin=True
            )
            
            # Envoyer un email au client
            try:
                from django.core.mail import send_mail
                from django.template.loader import render_to_string
                from django.utils.html import strip_tags
                from django.conf import settings
                
                # Déterminer l'email du destinataire
                if message_support.email_contact:
                    email_destinataire = message_support.email_contact
                elif message_support.client:
                    email_destinataire = message_support.client.email
                else:
                    email_destinataire = None
                
                if email_destinataire:
                    # Contexte pour le template email
                    context_email = {
                        'client_nom': message_support.get_client_name(),
                        'sujet': message_support.sujet,
                        'reponse': contenu,
                        'message_original': message_support.message,
                        'message_id': message_support.id,
                        'site_url': request.build_absolute_uri('/'),
                    }
                    
                    # Créer le contenu HTML de l'email avec logo SadibouShop
                    html_message = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 600px; margin: 0 auto; padding: 0; }}
                            .header {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: white; padding: 25px 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                            .logo-container {{ display: inline-block; }}
                            .logo-icon {{ display: inline-block; width: 40px; height: 40px; background: linear-gradient(135deg, #ffc107 0%, #e6ac00 100%); border-radius: 10px; text-align: center; line-height: 40px; vertical-align: middle; margin-right: 10px; }}
                            .logo-text {{ display: inline-block; vertical-align: middle; }}
                            .logo-text h2 {{ color: #ffffff; margin: 0; font-size: 22px; font-weight: 800; }}
                            .logo-text h2 span {{ color: #ffc107; }}
                            .logo-tagline {{ color: #888888; margin: 0; font-size: 9px; letter-spacing: 2px; text-transform: uppercase; }}
                            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                            .response-box {{ background: white; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                            .original-message {{ background: #f0f0f0; padding: 15px; margin: 20px 0; border-radius: 5px; font-size: 14px; }}
                            .footer {{ text-align: center; padding: 25px 30px; background: #1a1a1a; color: #666; font-size: 12px; border-radius: 0 0 10px 10px; }}
                            .footer-logo {{ color: #ffc107; font-weight: 700; font-size: 14px; margin: 0 0 15px 0; }}
                            .footer-logo span {{ color: #ffffff; }}
                            .button {{ display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #ffc107 0%, #e6ac00 100%); color: #1a1a1a; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <div class="logo-container">
                                    <span class="logo-icon">👔</span>
                                    <div class="logo-text">
                                        <h2>SADIBOU<span>SHOP</span></h2>
                                        <p class="logo-tagline">Mode & Tendances</p>
                                    </div>
                                </div>
                                <h1 style="margin: 15px 0 0 0; font-size: 18px;">📧 Nouvelle réponse à votre demande</h1>
                            </div>
                            <div class="content">
                                <p>Bonjour <strong>{context_email['client_nom']}</strong>,</p>
                                
                                <p>Notre équipe support vient de répondre à votre demande concernant : <strong>{context_email['sujet']}</strong></p>
                                
                                <div class="response-box">
                                    <h3 style="color: #1a1a1a; margin-top: 0;">💬 Réponse de notre équipe :</h3>
                                    <p style="white-space: pre-wrap;">{context_email['reponse']}</p>
                                </div>
                                
                                <div class="original-message">
                                    <strong>Votre message initial :</strong>
                                    <p style="white-space: pre-wrap; margin-top: 10px;">{context_email['message_original']}</p>
                                </div>
                                
                                <div style="text-align: center;">
                                    <a href="{context_email['site_url']}contact-support/" class="button">
                                        Répondre ou consulter la conversation
                                    </a>
                                </div>
                                
                                <p style="margin-top: 30px;">Si vous avez d'autres questions, n'hésitez pas à nous répondre via votre espace client.</p>
                                
                                <p style="margin-top: 20px;">
                                    Cordialement,<br>
                                    <strong>L'équipe Support SadibouShop</strong>
                                </p>
                            </div>
                            <div class="footer">
                                <p class="footer-logo">SADIBOU<span>SHOP</span></p>
                                <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre directement.</p>
                                <p>Pour toute question, contactez-nous via votre espace client.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Version texte simple
                    text_message = f"""
Bonjour {context_email['client_nom']},

Notre équipe support vient de répondre à votre demande concernant : {context_email['sujet']}

RÉPONSE DE NOTRE ÉQUIPE :
{context_email['reponse']}

VOTRE MESSAGE INITIAL :
{context_email['message_original']}

Vous pouvez consulter la conversation complète et répondre via votre espace client : {context_email['site_url']}contact-support/

Cordialement,
L'équipe Support
                    """
                    
                    send_mail(
                        subject=f"Réponse à votre demande : {message_support.sujet}",
                        message=text_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email_destinataire],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    
                    messages.success(request, "Votre réponse a été envoyée et un email a été envoyé au client.")
                else:
                    messages.success(request, "Votre réponse a été envoyée (aucun email configuré pour ce client).")
                    
            except Exception as e:
                messages.warning(request, f"Votre réponse a été envoyée mais l'email n'a pas pu être envoyé : {str(e)}")
            
            return redirect('admin_message_detail', message_id=message_id)
        
        # Changer le statut
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut and nouveau_statut != message_support.statut:
            message_support.statut = nouveau_statut
            message_support.save(update_fields=['statut'])
            messages.success(request, f"Statut changé en : {message_support.get_statut_display()}")
            return redirect('admin_message_detail', message_id=message_id)
        
        # Changer la priorité
        nouvelle_priorite = request.POST.get('priorite')
        if nouvelle_priorite and nouvelle_priorite != message_support.priorite:
            message_support.priorite = nouvelle_priorite
            message_support.save(update_fields=['priorite'])
            messages.success(request, f"Priorité changée en : {message_support.get_priorite_display()}")
            return redirect('admin_message_detail', message_id=message_id)
    
    context = {
        'message': message_support,
        'reponses': message_support.reponses.all(),
        'statuts': MessageSupport.STATUT_CHOICES,
        'priorites': MessageSupport.PRIORITE_CHOICES,
    }
    
    return render(request, 'adminpanel/message_detail.html', context)

@admin_required
def admin_message_delete(request, message_id):
    """Supprimer un message"""
    from boutique.models import MessageSupport
    message_support = get_object_or_404(MessageSupport, id=message_id)
    message_support.delete()
    messages.success(request, "Le message a été supprimé.")
    return redirect('admin_messagerie')

@admin_required
def admin_messages_marquer_tous_lus(request):
    """Marquer tous les messages comme lus"""
    from boutique.models import MessageSupport
    if request.method == 'POST':
        nb_messages = MessageSupport.objects.filter(lu=False).update(lu=True)
        messages.success(request, f"{nb_messages} message(s) marqué(s) comme lu(s).")
    return redirect('admin_messagerie')


# ===================================================================
# VUES NOTIFICATIONS ADMIN
# ===================================================================

@login_required
@require_POST
def admin_marquer_notification_vue(request):
    """
    Marquer une notification comme vue (AJAX)
    """
    from boutique.models import NotificationAdminVue
    import json
    
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    
    try:
        data = json.loads(request.body)
        type_notification = data.get('type')
        objet_id = data.get('id')
        
        if not type_notification or not objet_id:
            return JsonResponse({'success': False, 'error': 'Paramètres manquants'}, status=400)
        
        # Créer ou récupérer la notification vue
        notification, created = NotificationAdminVue.objects.get_or_create(
            admin=request.user,
            type_notification=type_notification,
            objet_id=objet_id
        )
        
        return JsonResponse({
            'success': True,
            'created': created,
            'message': 'Notification marquée comme vue'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def admin_marquer_toutes_notifications_vues(request):
    """
    Marquer toutes les notifications d'un type comme vues (AJAX)
    """
    from boutique.models import NotificationAdminVue, Commande, MessageSupport, AvisProduit, AvisLivreur, Produit
    from django.contrib.auth.models import User
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    
    try:
        data = json.loads(request.body)
        type_notification = data.get('type')
        
        if not type_notification:
            return JsonResponse({'success': False, 'error': 'Type manquant'}, status=400)
        
        count = 0
        
        if type_notification == 'NOUVELLE_COMMANDE':
            # Marquer toutes les commandes EN_ATTENTE et EN_COURS comme vues
            commandes = Commande.objects.filter(statut__in=['EN_ATTENTE', 'EN_COURS'])
            for cmd in commandes:
                obj, created = NotificationAdminVue.objects.get_or_create(
                    admin=request.user,
                    type_notification='NOUVELLE_COMMANDE',
                    objet_id=cmd.id
                )
                if created:
                    count += 1
                    
        elif type_notification == 'NOUVEAU_MESSAGE':
            # Marquer tous les messages non lus comme vus
            messages = MessageSupport.objects.filter(lu=False)
            for msg in messages:
                obj, created = NotificationAdminVue.objects.get_or_create(
                    admin=request.user,
                    type_notification='NOUVEAU_MESSAGE',
                    objet_id=msg.id
                )
                if created:
                    count += 1
                    
        elif type_notification == 'AVIS_PRODUIT':
            # Marquer tous les avis produits non examinés comme vus
            avis = AvisProduit.objects.filter(examine=False)
            for a in avis:
                obj, created = NotificationAdminVue.objects.get_or_create(
                    admin=request.user,
                    type_notification='AVIS_PRODUIT',
                    objet_id=a.id
                )
                if created:
                    count += 1
                    
        elif type_notification == 'AVIS_LIVREUR':
            # Marquer tous les avis livreurs non examinés comme vus
            avis = AvisLivreur.objects.filter(examine=False)
            for a in avis:
                obj, created = NotificationAdminVue.objects.get_or_create(
                    admin=request.user,
                    type_notification='AVIS_LIVREUR',
                    objet_id=a.id
                )
                if created:
                    count += 1
                    
        elif type_notification == 'NOUVEAU_CLIENT':
            # Marquer tous les nouveaux clients (dernières 24h) comme vus
            date_limite = timezone.now() - timedelta(hours=24)
            clients = User.objects.filter(
                date_joined__gte=date_limite,
                is_staff=False,
                is_superuser=False
            )
            for client in clients:
                obj, created = NotificationAdminVue.objects.get_or_create(
                    admin=request.user,
                    type_notification='NOUVEAU_CLIENT',
                    objet_id=client.id
                )
                if created:
                    count += 1
                    
        elif type_notification == 'RUPTURE_STOCK':
            # Marquer tous les produits en rupture comme vus
            produits = Produit.objects.filter(stock=0)
            for prod in produits:
                obj, created = NotificationAdminVue.objects.get_or_create(
                    admin=request.user,
                    type_notification='RUPTURE_STOCK',
                    objet_id=prod.id
                )
                if created:
                    count += 1
        
        return JsonResponse({
            'success': True,
            'count': count,
            'message': f'{count} notifications marquées comme vues'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
