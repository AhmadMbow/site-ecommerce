from django.utils import timezone
from datetime import timedelta

def admin_notifications(request):
    """
    Context processor pour les badges de notification dans le panel admin
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}
    
    from boutique.models import Commande, MessageSupport, AvisLivreur, AvisProduit, Produit
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
    
    # Compter les nouveaux clients (inscrits dans les dernières 24h)
    nouveaux_clients = User.objects.filter(
        date_joined__gte=date_limite,
        is_staff=False,
        is_superuser=False
    ).count()
    
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
