from itertools import count
from os import truncate
from functools import wraps
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
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
    ProduitForm, UserUpdateForm, CustomUserCreationForm, AvisLivreurForm
)
from .models import (
    Produit, Categorie, Commande, CommandeItem, PanierItem, UserProfile, 
    Note, Adresse, RoleChoices, AvisLivreur, AvisProduit
)
from .constants import FRAIS_LIVRAISON_DEFAUT

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
    
    return render(request, 'boutique/produit_detail.html', {
        'produit': produit,
        'avis': avis,
        'peut_noter': peut_noter,
        'a_deja_note': a_deja_note,
        'produits_similaires': produits_similaires,
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
    # Précharger les produits
    try:
        produit_ids = [int(pid) for pid in cart.keys() if str(pid).isdigit()]
    except Exception:
        produit_ids = []
    if not produit_ids:
        request.session['panier'] = {}
        request.session.modified = True
        return
    produits_map = {p.id: p for p in Produit.objects.filter(id__in=produit_ids)}
    for pid_str, data in cart.items():
        try:
            pid = int(pid_str)
            qty = int(data.get('quantite', 0))
            if qty <= 0:
                continue
            produit = produits_map.get(pid)
            if not produit:
                continue
            item, created = PanierItem.objects.get_or_create(
                user=request.user, produit=produit, defaults={'quantite': qty}
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
    """Récupère les commandes pour un livreur"""
    return Commande.objects.select_related('user').order_by('-id')

def _livreur_stats(orders):
    """Calcule les statistiques pour un livreur"""
    from django.db.models import Sum, Count
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # Utiliser la constante partagée
    FRAIS_LIVRAISON = FRAIS_LIVRAISON_DEFAUT
    
    # Compter les commandes par statut
    pending = orders.filter(statut='EN_ATTENTE').count()
    in_progress = orders.filter(statut='EN_COURS').count()
    completed = orders.filter(statut='LIVREE').count()
    
    # Commandes livrées aujourd'hui
    delivered_today = orders.filter(
        statut='LIVREE',
        date_commande__date=today
    ).count()
    
    # Revenus basés sur les frais de livraison
    # Seules les commandes livrées génèrent des revenus pour le livreur
    completed_orders = orders.filter(statut='LIVREE')
    
    # Revenus totaux = nombre de commandes livrées × frais de livraison
    revenue_total = completed_orders.count() * FRAIS_LIVRAISON
    
    # Revenus du jour = commandes livrées aujourd'hui × frais de livraison
    revenue_today = delivered_today * FRAIS_LIVRAISON
    
    # Revenus du mois
    revenue_this_month = orders.filter(
        statut='LIVREE',
        date_commande__month=today.month,
        date_commande__year=today.year
    ).count() * FRAIS_LIVRAISON
    
    return {
        'count_all': orders.count(),
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
            return redirect('admin_dashboard')
        
        # Si livreur -> dashboard livreur
        profile = getattr(request.user, 'userprofile', None)
        if profile and getattr(profile, 'role', '').upper() == 'LIVREUR':
            return redirect('livreur_dashboard')
        
        # Sinon -> dashboard client
        return redirect('dashboard')
    
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

    # Vérifier le stock disponible
    if produit.stock <= 0:
        return JsonResponse({
            'success': False,
            'message': f'Désolé, {produit.nom} est en rupture de stock.',
            'stock': 0
        }, status=400)

    if request.user.is_authenticated:
        item, created = PanierItem.objects.get_or_create(
            user=request.user,
            produit=produit,
            defaults={'quantite': 1}
        )
        if not created:
            # Vérifier si on peut ajouter une unité de plus
            nouvelle_quantite = item.quantite + 1
            if nouvelle_quantite > produit.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Stock insuffisant pour {produit.nom}. Stock disponible: {produit.stock}',
                    'stock': produit.stock,
                    'current_cart_quantity': item.quantite
                }, status=400)
            
            item.quantite = nouvelle_quantite
            item.save(update_fields=['quantite'])
        else:
            # Nouveau produit ajouté, vérifier quand même le stock
            if produit.stock < 1:
                item.delete()  # Supprimer l'item créé
                return JsonResponse({
                    'success': False,
                    'message': f'Désolé, {produit.nom} est en rupture de stock.',
                    'stock': 0
                }, status=400)
    else:
        cart = request.session.get('panier', {})
        key = str(produit_id)
        qty = int(cart.get(key, {}).get('quantite', 0)) + 1
        
        # Vérifier si la quantité demandée ne dépasse pas le stock
        if qty > produit.stock:
            return JsonResponse({
                'success': False,
                'message': f'Stock insuffisant pour {produit.nom}. Stock disponible: {produit.stock}',
                'stock': produit.stock,
                'current_cart_quantity': qty - 1
            }, status=400)
        
        cart[key] = {'quantite': qty}
        request.session['panier'] = cart
        request.session.modified = True

    count = _get_cart_count(request)
    
    # Message de succès avec indication du stock restant
    stock_restant = produit.stock - (item.quantite if request.user.is_authenticated else qty)
    message = f'{produit.nom} ajouté au panier'
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
@login_required
def voir_panier(request):
    """Affichage du contenu du panier avec calcul du total et livraison"""
    items_qs = PanierItem.objects.select_related('produit').filter(user=request.user)
    items = []
    total = 0

    for it in items_qs:
        # Prix unitaire (promo si existante)
        pu = it.produit.prix_promo if it.produit.prix_promo else it.produit.prix
        sous_total = pu * it.quantite
        total += sous_total
        it.prix_total = sous_total
        items.append(it)

    # Exemple : distance fictive (à remplacer par vrai calcul GPS)
    distance_km = request.session.get('distance_km', 10)  # tu peux stocker la distance réelle en session après géolocalisation
    shipping = calcul_livraison(distance_km)

    # Récupérer la position GPS de l'adresse par défaut du client
    adresse_defaut = Adresse.objects.filter(user=request.user, is_default=True).first()
    latitude = adresse_defaut.latitude if adresse_defaut else None
    longitude = adresse_defaut.longitude if adresse_defaut else None

    context = {
        'items': items,
        'total': total,
        'shipping': shipping,
        'distance_km': distance_km,
        'cart_count': sum(i.quantite for i in items),
        'adresse_latitude': latitude,
        'adresse_longitude': longitude,
    }

    return render(request, 'boutique/panier.html', context)


@login_required
def retirer_du_panier(request, item_id):
    item = get_object_or_404(PanierItem, id=item_id, user=request.user)
    nom_produit = item.produit.nom
    item.delete()
    messages.success(request, f'{nom_produit} retiré du panier.')
    return redirect('panier')


@login_required
@require_POST
def modifier_quantite(request):
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


# ===================================================================
# CONFIRMATION DE COMMANDE
# ===================================================================

@login_required
@require_POST
@transaction.atomic
def confirmer_commande(request):
    items = list(PanierItem.objects.select_related('produit').filter(user=request.user))
    if not items:
        messages.error(request, "Votre panier est vide.")
        return redirect('panier')

    # Vérification du stock AVANT de créer la commande
    produits_insuffisants = []
    for it in items:
        if it.produit.stock < it.quantite:
            produits_insuffisants.append({
                'nom': it.produit.nom,
                'demande': it.quantite,
                'disponible': it.produit.stock
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

    # Récupération de l'adresse
    adresse_defaut = Adresse.objects.filter(user=request.user, is_default=True).first()

    # Récupération des données GPS du client
    latitude = request.POST.get('latitude')
    longitude = request.POST.get('longitude')
    adresse_gps = request.POST.get('adresse_gps')

    # Création de la commande
    cmd_kwargs = {'user': request.user, 'total': total}
    if hasattr(Commande, 'statut'):
        cmd_kwargs['statut'] = _pending_choice_for_statut()
    elif hasattr(Commande, 'status'):
        cmd_kwargs['status'] = 'pending'

    if adresse_defaut:
        # Met à jour l'adresse avec la position GPS si fournie
        if latitude and longitude:
            try:
                adresse_defaut.latitude = latitude
                adresse_defaut.longitude = longitude
                adresse_defaut.save(update_fields=['latitude', 'longitude'])
            except Exception:
                pass
        if hasattr(Commande, 'adresse'):
            cmd_kwargs['adresse'] = adresse_defaut
        if hasattr(Commande, 'adresse_livraison'):
            cmd_kwargs['adresse_livraison'] = adresse_defaut

    # Ajout des coordonnées GPS à la commande
    if latitude:
        cmd_kwargs['latitude'] = latitude
    if longitude:
        cmd_kwargs['longitude'] = longitude
    if adresse_gps:
        cmd_kwargs['adresse_gps'] = adresse_gps

    # Utiliser une transaction pour garantir la cohérence
    with transaction.atomic():
        commande = Commande.objects.create(**cmd_kwargs)
        
        # Création des lignes de commande
        for it in items:
            pu = _unit_price(it.produit)
            ci_kwargs = {'commande': commande, 'produit': it.produit, 'quantite': it.quantite}
            if hasattr(CommandeItem, 'prix_unitaire'):
                ci_kwargs['prix_unitaire'] = pu
            elif hasattr(CommandeItem, 'prix'):
                ci_kwargs['prix'] = pu
            CommandeItem.objects.create(**ci_kwargs)
        
        # Vider le panier
        PanierItem.objects.filter(user=request.user).delete()
    
    # Envoyer l'email après la transaction
    envoyer_mail_statut_commande(commande)
    
    if 'panier' in request.session:
        request.session['panier'] = {}
        request.session.modified = True

    messages.success(request, "Commande confirmée avec localisation. Merci pour votre achat !")
    return redirect('mes_commandes')

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
    total_livraisons = orders.count()
    livraisons_reussies = orders.filter(statut='LIVREE').count()
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
        orders = orders.filter(statut=status_filter)
    
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
    
    orders = _livreur_orders_queryset(request.user)
    stats = _livreur_stats(orders)
    
    # Statistiques par mois avec revenus
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    from decimal import Decimal
    
    FRAIS_LIVRAISON = Decimal('1000')
    
    monthly_stats = (
        orders.filter(statut='LIVREE')  # Seulement les commandes livrées
        .annotate(month=TruncMonth('date_commande'))
        .values('month')
        .annotate(
            count=Count('id'),
        )
        .order_by('month')
    )
    
    # Ajouter les revenus mensuels
    for month_data in monthly_stats:
        month_data['revenue'] = month_data['count'] * FRAIS_LIVRAISON
    
    # Commandes à encaisser (EN_COURS et LIVREE)
    orders_to_collect = orders.filter(
        statut__in=['EN_COURS', 'LIVREE']
    ).select_related('user', 'user__userprofile').order_by('-date_commande')[:10]
    
    context = {
        'stats': stats,
        'monthly_stats': monthly_stats,
        'orders_count': orders.count(),
        'orders_to_collect': orders_to_collect,
        'today': timezone.now(),
        'active_tab': 'stats'
    }
    return render(request, 'livreur/stats.html', context)

@login_required
def livreur_map(request):
    """Carte des livraisons"""
    # Récupérer toutes les commandes avec user pour le nom du client
    orders = _livreur_orders_queryset(request.user).select_related('user', 'user__userprofile')

    # Liste des commandes ayant des coordonnées GPS (latitude ET longitude)
    orders_with_coords = [
        o for o in orders
        if o.latitude is not None and o.longitude is not None
    ]

    stats = _livreur_stats(orders)
    
    context = {
        'orders': orders,
        'orders_with_coords': orders_with_coords,
        'stats': stats,
        'active_tab': 'map'
    }
    return render(request, 'livreur/map.html', context)

@login_required
@user_passes_test(is_livreur)
def livreur_order_detail(request, pk):
    """Détail d'une commande pour le livreur"""
    order = get_object_or_404(Commande.objects.select_related('user'), pk=pk)
    items = list(CommandeItem.objects.select_related('produit').filter(commande=order))
    for it in items:
        unit = getattr(it, 'prix_unitaire', None) or getattr(it, 'prix', None) or 0
        qty = getattr(it, 'quantite', 0) or 0
        it.unit_price = unit
        it.line_total = unit * qty

    return render(request, 'livreur/order_detail.html', {'order': order, 'items': items})

@login_required
@user_passes_test(is_livreur)
@require_POST
def livreur_order_accept(request, pk):
    """Accepter une commande"""
    order = get_object_or_404(Commande, pk=pk)

    if hasattr(order, 'livreur') and not getattr(order, 'livreur', None):
        order.livreur = request.user

    if getattr(order, 'statut', None) == 'EN_ATTENTE':
        order.statut = 'EN_COURS'
        update_fields = ['statut']
        if hasattr(order, 'livreur'):
            update_fields.append('livreur')
        order.save(update_fields=update_fields)
        messages.success(request, f"Commande #{order.id} acceptée.")
    else:
        messages.info(request, f"Commande #{order.id} déjà {order.statut or 'traitée'}.")

    return redirect(request.POST.get('next') or 'livreur_orders')

@login_required
@user_passes_test(is_livreur)
@require_POST
def livreur_order_update_status(request, pk):
    """Mettre à jour le statut d'une commande"""
    order = get_object_or_404(Commande, pk=pk)
    action = request.POST.get('action', '')
    
    current_status = getattr(order, 'statut', None)
    
    if action == 'accept' and current_status == 'EN_ATTENTE':
        # Accepter la commande
        if hasattr(order, 'livreur') and not getattr(order, 'livreur', None):
            order.livreur = request.user
        
        order.statut = 'EN_COURS'
        update_fields = ['statut']
        if hasattr(order, 'livreur'):
            update_fields.append('livreur')
        
        order.save(update_fields=update_fields)
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
        messages.success(request, f"Commande #{order.id} marquée comme livrée.")
        
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
    total_orders = Commande.objects.count()
    total_users = User.objects.count()
    revenue = Commande.objects.aggregate(total=Sum('total'))['total'] or 0

    per_day = (
        Commande.objects
        .annotate(day=TruncDate('date_commande'))
        .values('day')
        .annotate(c=Count('id'))
        .order_by('day')
    )
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_users': total_users,
        'revenue': revenue,
        'chart_days': json.dumps([d['day'].strftime('%d/%m') for d in per_day]),
        'chart_counts': json.dumps([d['c'] for d in per_day]),
        'top_products': (
            CommandeItem.objects
            .values('produit__nom')
            .annotate(qty=Sum('quantite'))
            .order_by('-qty')[:5]
        ),
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
    
    # Calculer les statistiques de stock
    all_products = Produit.objects.all()
    total_products = all_products.count()
    products_in_stock = all_products.filter(stock__gt=0).count()
    products_low_stock = all_products.filter(stock__gt=0, stock__lt=5).count()
    products_out_of_stock = all_products.filter(stock=0).count()
    
    return render(request, 'adminpanel/products.html', {
        'produits': page_obj.object_list,
        'page_obj': page_obj,
        'total_count': qs.count(),
        'categories': categories,
        'total_products': total_products,
        'products_in_stock': products_in_stock,
        'products_low_stock': products_low_stock,
        'products_out_of_stock': products_out_of_stock,
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
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Produit créé avec succès.")
        return redirect('admin_products')
    return render(request, 'adminpanel/product_form.html', {'form': form, 'mode': 'create'})

@staff_required
def admin_product_update(request, pk):
    """Modification d'un produit"""
    produit = get_object_or_404(Produit, pk=pk)
    form = ProduitForm(request.POST or None, request.FILES or None, instance=produit)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Produit modifié avec succès.")
        return redirect('admin_products')
    return render(request, 'adminpanel/product_form.html', {'form': form, 'mode': 'update', 'produit': produit})

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
    form = CategorieForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Catégorie créée avec succès.")
        return redirect('admin_categories')
    return render(request, 'adminpanel/category_form.html', {'form': form, 'mode': 'create'})

@staff_required
def admin_category_update(request, pk):
    """Modification d'une catégorie"""
    categorie = get_object_or_404(Categorie, pk=pk)
    form = CategorieForm(request.POST or None, instance=categorie)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Catégorie modifiée avec succès.")
        return redirect('admin_categories')
    return render(request, 'adminpanel/category_form.html', {'form': form, 'mode': 'update', 'categorie': categorie})

@staff_required
def admin_category_delete(request, pk):
    """Suppression d'une catégorie"""
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        categorie.delete()
        messages.success(request, "Catégorie supprimée.")
        return redirect('admin_categories')
    return render(request, 'adminpanel/category_confirm_delete.html', {'categorie': categorie})

# Gestion des livreurs
@admin_required
def admin_livreurs_list(request):
    """Liste des livreurs"""
    q = request.GET.get('q', '')
    qs = UserProfile.objects.select_related('user').filter(role=RoleChoices.LIVREUR)
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(phone__icontains=q))
    return render(request, 'adminpanel/deliverers.html', {'deliverers': qs, 'q': q})

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
    """Liste des clients"""
    clients_list = User.objects.filter(is_staff=False).select_related('userprofile').order_by('-date_joined')
    
    search = request.GET.get('q')
    if search:
        clients_list = clients_list.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    paginator = Paginator(clients_list, 20)
    page_number = request.GET.get('page')
    clients = paginator.get_page(page_number)
    
    context = {
        'clients': clients,
        'search': search,
        'total_clients': clients_list.count(),
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

# Gestion des commandes
@staff_required
def admin_orders_list(request):
    """Liste des commandes pour l'admin"""
    q = request.GET.get('q', '')
    status = request.GET.get('status')

    orders = Commande.objects.select_related('user').order_by('-id')
    if q:
        orders = orders.filter(
            Q(id__icontains=q) |
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)
        )
    if status:
        orders = orders.filter(statut=status)

    stats = {
        'all': Commande.objects.count(),
        'pending': Commande.objects.filter(statut='EN_ATTENTE').count(),
        'in_progress': Commande.objects.filter(statut='EN_COURS').count(),
        'completed': Commande.objects.filter(statut='LIVREE').count(),
        'revenue': Commande.objects.filter(statut='LIVREE').aggregate(Sum('total'))['total__sum'] or 0,
    }
    return render(request, 'adminpanel/orders_list.html', {'orders': orders, 'stats': stats, 'q': q})

@staff_required
def admin_order_detail(request, pk):
    """Détail d'une commande pour l'admin"""
    order = get_object_or_404(Commande.objects.select_related('user'), pk=pk)
    items = list(CommandeItem.objects.select_related('produit').filter(commande=order))

    for it in items:
        unit = getattr(it, 'prix_unitaire', None)
        if unit is None:
            unit = getattr(it, 'prix', None)
        if unit is None:
            unit = 0
        it.unit_price = unit
        it.line_total = unit * (getattr(it, 'quantite', 0) or 0)

    return render(request, 'adminpanel/order_detail.html', {'order': order, 'items': items})

@staff_required
def admin_cancel_order(request, pk):
    """Annuler une commande (uniquement si elle n'est pas livrée)"""
    order = get_object_or_404(Commande, pk=pk)
    
    # Vérifier que la commande n'est pas déjà livrée
    if order.statut == 'LIVREE':
        messages.error(request, 'Impossible d\'annuler une commande déjà livrée.')
        return redirect('admin_order_detail', pk=pk)
    
    # Vérifier que la commande n'est pas déjà annulée
    if order.statut == 'ANNULEE':
        messages.warning(request, 'Cette commande est déjà annulée.')
        return redirect('admin_order_detail', pk=pk)
    
    if request.method == 'POST':
        # Annuler la commande
        order.statut = 'ANNULEE'
        order.save()
        messages.success(request, f'La commande #{order.id} a été annulée avec succès.')
        return redirect('admin_orders')
    
    return redirect('admin_order_detail', pk=pk)

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
