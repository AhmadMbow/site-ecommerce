from django.utils import timezone
from datetime import timedelta

def admin_notifications(request):
    """
    Context processor pour les badges de notification dans le panel admin
    Version améliorée avec gestion des tailles en rupture
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}
    
    from boutique.models import Commande, CommandeInvite, MessageSupport, AvisLivreur, AvisProduit, Produit, ProduitTaille, NotificationAdminVue
    from django.contrib.auth.models import User
    
    # Date limite pour "nouveau" (dernières 24h)
    date_limite = timezone.now() - timedelta(hours=24)
    
    # Récupérer les IDs des notifications déjà vues par cet admin
    commandes_vues_ids = NotificationAdminVue.objects.filter(
        admin=request.user,
        type_notification='NOUVELLE_COMMANDE'
    ).values_list('objet_id', flat=True)
    
    commandes_invites_vues_ids = NotificationAdminVue.objects.filter(
        admin=request.user,
        type_notification='NOUVELLE_COMMANDE_INVITE'
    ).values_list('objet_id', flat=True)
    
    avis_produit_vus_ids = NotificationAdminVue.objects.filter(
        admin=request.user,
        type_notification='AVIS_PRODUIT'
    ).values_list('objet_id', flat=True)
    
    avis_livreur_vus_ids = NotificationAdminVue.objects.filter(
        admin=request.user,
        type_notification='AVIS_LIVREUR'
    ).values_list('objet_id', flat=True)
    
    clients_vus_ids = NotificationAdminVue.objects.filter(
        admin=request.user,
        type_notification='NOUVEAU_CLIENT'
    ).values_list('objet_id', flat=True)
    
    rupture_vus_ids = NotificationAdminVue.objects.filter(
        admin=request.user,
        type_notification='RUPTURE_STOCK'
    ).values_list('objet_id', flat=True)
    
    # Compter les nouvelles commandes (statut EN_ATTENTE ou EN_COURS) NON VUES
    # Inclure les commandes clients ET invités
    nouvelles_commandes_clients = Commande.objects.filter(
        statut__in=['EN_ATTENTE', 'EN_COURS']
    ).exclude(id__in=commandes_vues_ids).count()
    
    nouvelles_commandes_invites = CommandeInvite.objects.filter(
        statut__in=['EN_ATTENTE', 'EN_COURS']
    ).exclude(id__in=commandes_invites_vues_ids).count()
    
    nouvelles_commandes = nouvelles_commandes_clients + nouvelles_commandes_invites
    
    # Compter les nouveaux messages - Basé sur le champ lu du modèle MessageSupport
    nouveaux_messages = MessageSupport.objects.filter(lu=False).count()
    
    # Compter les nouveaux avis (non examinés) NON VUS
    nouveaux_avis_livreur = AvisLivreur.objects.filter(
        examine=False
    ).exclude(id__in=avis_livreur_vus_ids).count()
    
    nouveaux_avis_produit = AvisProduit.objects.filter(
        examine=False
    ).exclude(id__in=avis_produit_vus_ids).count()
    
    nouveaux_avis = nouveaux_avis_livreur + nouveaux_avis_produit
    
    # Compter les nouveaux clients (inscrits dans les dernières 24h) NON VUS
    nouveaux_clients = User.objects.filter(
        date_joined__gte=date_limite,
        is_staff=False,
        is_superuser=False
    ).exclude(id__in=clients_vus_ids).count()
    
    # Compter les tailles en rupture de stock (nouveau système avec tailles)
    tailles_rupture = ProduitTaille.objects.filter(stock=0).count()
    
    # Compter les produits sans tailles en rupture de stock
    produits_sans_tailles_rupture = Produit.objects.filter(
        a_tailles=False,
        stock=0
    ).exclude(id__in=rupture_vus_ids).count()
    
    # Total ruptures = tailles en rupture + produits sans tailles en rupture
    total_rupture_stock = tailles_rupture + produits_sans_tailles_rupture
    
    # Compter les commandes en attente de livraison (EN_COURS)
    commandes_en_livraison = Commande.objects.filter(statut='EN_COURS').count()
    commandes_en_livraison += CommandeInvite.objects.filter(statut='EN_COURS').count()
    
    # Compter les commandes livrées aujourd'hui (basé sur date_commande car pas de date_livraison)
    aujourdhui = timezone.now().date()
    commandes_livrees_aujourdhui = Commande.objects.filter(
        statut='LIVREE',
        date_commande__date=aujourdhui
    ).count()
    commandes_livrees_aujourdhui += CommandeInvite.objects.filter(
        statut='LIVREE',
        date_commande__date=aujourdhui
    ).count()
    
    # Stock bas = nombre de tailles avec stock entre 1 et 4
    tailles_stock_bas = ProduitTaille.objects.filter(stock__gt=0, stock__lt=5).count()
    
    return {
        'admin_badges': {
            'commandes': nouvelles_commandes,
            'commandes_en_attente': Commande.objects.filter(statut='EN_ATTENTE').count() + CommandeInvite.objects.filter(statut='EN_ATTENTE').count(),
            'commandes_en_livraison': commandes_en_livraison,
            'commandes_livrees_aujourdhui': commandes_livrees_aujourdhui,
            'messages': nouveaux_messages,
            'avis': nouveaux_avis,
            'avis_livreur': nouveaux_avis_livreur,
            'avis_produit': nouveaux_avis_produit,
            'clients': nouveaux_clients,
            'rupture_stock': total_rupture_stock,
            'tailles_rupture': tailles_rupture,
            'stock_bas': tailles_stock_bas,
        }
    }

def livreur_notifications(request):
    """
    Context processor pour les notifications et badges du livreur
    """
    if not request.user.is_authenticated:
        return {}
    
    # Vérifier si l'utilisateur est livreur
    try:
        profile = request.user.userprofile
        if profile.role != 'LIVREUR':
            return {}
    except:
        return {}
    
    from boutique.models import Commande
    from django.db.models import Q
    
    # Nouvelles commandes EN_ATTENTE (non encore acceptées)
    nouvelles_commandes = Commande.objects.filter(
        statut='EN_ATTENTE'
    ).select_related('user').order_by('-date_commande')[:10]
    
    # Commandes EN_COURS assignées à ce livreur
    mes_commandes_en_cours = Commande.objects.filter(
        statut='EN_COURS',
        livreur=request.user
    ).count()
    
    # Créer les notifications pour la cloche
    notifications_list = []
    
    # Ajouter les nouvelles commandes comme notifications
    for cmd in nouvelles_commandes:
        notifications_list.append({
            'type': 'nouvelle_commande',
            'title': f'Nouvelle commande #{cmd.numero_commande}',
            'message': f'Client: {cmd.user.get_full_name() or cmd.user.username}',
            'date': cmd.date_commande,
            'url': f'/boutique/livreur/orders/',
            'icon': 'bi-basket-fill',
            'color': 'warning'
        })
    
    return {
        'livreur_notifications': notifications_list[:5],
        'livreur_notifications_count': len(nouvelles_commandes),
        'livreur_en_cours_count': mes_commandes_en_cours,
    }
