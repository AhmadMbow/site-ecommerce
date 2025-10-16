from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Commande, CommandeItem
from django.db import transaction


@receiver(pre_save, sender=Commande)
def gerer_stock_commande(sender, instance, **kwargs):
    """
    Signal qui gère automatiquement le stock des produits lors du changement de statut d'une commande.
    - Décrémente le stock quand une commande passe à LIVREE
    - Restitue le stock si une commande LIVREE est annulée
    """
    
    # Si c'est une nouvelle commande (pas encore sauvegardée), on ignore
    if not instance.pk:
        return
    
    try:
        # Récupérer l'ancien état de la commande
        ancienne_commande = Commande.objects.get(pk=instance.pk)
        ancien_statut = ancienne_commande.statut
        nouveau_statut = instance.statut
        
        # Si le statut change vers LIVREE, on décrémente le stock
        if ancien_statut != 'LIVREE' and nouveau_statut == 'LIVREE':
            with transaction.atomic():
                items = instance.items.select_related('produit').all()
                for item in items:
                    produit = item.produit
                    quantite = item.quantite
                    
                    # Décrémenter le stock
                    if produit.stock >= quantite:
                        produit.stock -= quantite
                        produit.save(update_fields=['stock'])
                        print(f"✅ Stock décrémenté: {produit.nom} - {quantite} unités (Nouveau stock: {produit.stock})")
                    else:
                        print(f"⚠️ Stock insuffisant pour {produit.nom}: demandé {quantite}, disponible {produit.stock}")
                        # On décrémente quand même jusqu'à 0
                        produit.stock = 0
                        produit.save(update_fields=['stock'])
        
        # Si une commande LIVREE est annulée, on restitue le stock
        elif ancien_statut == 'LIVREE' and nouveau_statut == 'ANNULEE':
            with transaction.atomic():
                items = instance.items.select_related('produit').all()
                for item in items:
                    produit = item.produit
                    quantite = item.quantite
                    
                    # Restituer le stock
                    produit.stock += quantite
                    produit.save(update_fields=['stock'])
                    print(f"🔄 Stock restitué: {produit.nom} + {quantite} unités (Nouveau stock: {produit.stock})")
        
        # Si une commande EN_ATTENTE ou EN_COURS est annulée, on ne touche pas au stock
        # car le stock n'a pas encore été décrémenté
        
    except Commande.DoesNotExist:
        pass


@receiver(post_save, sender=Commande)
def notifier_changement_stock(sender, instance, created, **kwargs):
    """
    Signal pour notifier les changements de stock (peut être utilisé pour envoyer des emails, etc.)
    """
    if not created and instance.statut == 'LIVREE':
        # Vérifier si des produits sont en rupture de stock
        items = instance.items.select_related('produit').all()
        for item in items:
            if item.produit.stock == 0:
                print(f"⚠️ ALERTE: {item.produit.nom} est maintenant en rupture de stock!")
            elif item.produit.stock < 5:
                print(f"⚠️ ATTENTION: Stock faible pour {item.produit.nom} ({item.produit.stock} restants)")
