from django.utils import timezone
from datetime import timedelta

def admin_notifications(request):
    """
    Context processor pour les badges de notification dans le panel admin
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}
    
    from boutique.models import Commande, MessageSupport, AvisLivreur, AvisProduit, Produit, NotificationAdminVue
    from django.contrib.auth.models import User
    
    # Date limite pour "nouveau" (dernières 24h)
    date_limite = timezone.now() - timedelta(hours=24)
    
    # Compter les nouvelles commandes (statut EN_ATTENTE ou EN_COURS)
    nouvelles_commandes = Commande.objects.filter(
        statut__in=['EN_ATTENTE', 'EN_COURS']
    ).count()
    
    # Compter les nouveaux messages (non lus par l'admin)
    nouveaux_messages = MessageSupport.objects.filter(
        lu=False
    ).count()
    
    # Compter les nouveaux avis (non examinés)
    nouveaux_avis_livreur = AvisLivreur.objects.filter(
        examine=False
    ).count()
    
    nouveaux_avis_produit = AvisProduit.objects.filter(
        examine=False
    ).count()
    
    nouveaux_avis = nouveaux_avis_livreur + nouveaux_avis_produit
    
    # Récupérer les IDs des clients déjà vus par cet admin
    clients_vus_ids = NotificationAdminVue.objects.filter(
        admin=request.user,
        type_notification='NOUVEAU_CLIENT'
    ).values_list('objet_id', flat=True)
    
    # Compter les nouveaux clients (inscrits dans les dernières 24h) NON VUS
    nouveaux_clients = User.objects.filter(
        date_joined__gte=date_limite,
        is_staff=False,
        is_superuser=False
    ).exclude(id__in=clients_vus_ids).count()
    
    # Compter les produits en rupture de stock
    produits_rupture_stock = Produit.objects.filter(stock=0).count()
    
    return {
        'admin_badges': {
            'commandes': nouvelles_commandes,
            'messages': nouveaux_messages,
            'avis': nouveaux_avis,
            'avis_livreur': nouveaux_avis_livreur,
            'avis_produit': nouveaux_avis_produit,
            'clients': nouveaux_clients,
            'rupture_stock': produits_rupture_stock,
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
            'icon': 'fa-box',
            'text': f"Nouvelle commande #{cmd.id} - {cmd.user.get_full_name() or cmd.user.username}",
            'time': cmd.date_commande.strftime('%H:%M'),
            'url': f'/livreur/orders/{cmd.id}/',
            'type': 'new_order',
            'order_id': cmd.id
        })
    
    return {
        'livreur_badges': {
            'nouvelles_commandes': nouvelles_commandes.count(),
            'commandes_en_cours': mes_commandes_en_cours,
        },
        'notifications': notifications_list,
        'nouvelles_commandes_count': nouvelles_commandes.count()
    }
