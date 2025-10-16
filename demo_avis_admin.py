#!/usr/bin/env python3
"""
Script de démonstration de la nouvelle fonctionnalité de gestion des avis
"""

import os
import sys
import django

# Configuration Django
os.chdir('/home/ahmadmbow/gittest/site-ecommerce')
sys.path.insert(0, '/home/ahmadmbow/gittest/site-ecommerce')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from boutique.models import AvisLivreur, AvisProduit, User
from django.db.models import Avg

def afficher_stats_avis():
    """Afficher les statistiques des avis"""
    print("🌟 STATISTIQUES DES AVIS - InnovaTech E-commerce")
    print("=" * 60)
    
    # Avis produits
    avis_produits = AvisProduit.objects.all()
    nb_avis_produits = avis_produits.count()
    if nb_avis_produits > 0:
        note_moyenne_produits = avis_produits.aggregate(Avg('note'))['note__avg']
        avis_positifs_produits = avis_produits.filter(note__gte=4).count()
        
        print(f"\n📦 AVIS PRODUITS:")
        print(f"   • Total: {nb_avis_produits} avis")
        print(f"   • Note moyenne: {note_moyenne_produits:.1f}/5")
        print(f"   • Avis positifs (4-5★): {avis_positifs_produits}")
        
        print(f"\n   📝 Derniers avis produits:")
        for avis in avis_produits.order_by('-date_avis')[:3]:
            print(f"   • {avis.client.username} → {avis.produit.nom} ({avis.note}★)")
            if avis.commentaire:
                commentaire = avis.commentaire[:50] + "..." if len(avis.commentaire) > 50 else avis.commentaire
                print(f"     💬 \"{commentaire}\"")
    
    # Avis livreurs
    avis_livreurs = AvisLivreur.objects.all()
    nb_avis_livreurs = avis_livreurs.count()
    if nb_avis_livreurs > 0:
        note_moyenne_livreurs = avis_livreurs.aggregate(Avg('note'))['note__avg']
        avis_positifs_livreurs = avis_livreurs.filter(note__gte=4).count()
        
        print(f"\n🚚 AVIS LIVREURS:")
        print(f"   • Total: {nb_avis_livreurs} avis")
        print(f"   • Note moyenne: {note_moyenne_livreurs:.1f}/5")
        print(f"   • Avis positifs (4-5★): {avis_positifs_livreurs}")
        
        print(f"\n   📝 Derniers avis livreurs:")
        for avis in avis_livreurs.order_by('-date_avis')[:3]:
            livreur_name = avis.livreur.get_full_name() or avis.livreur.username
            print(f"   • {avis.client.username} → {livreur_name} ({avis.note}★)")
            if avis.commentaire:
                commentaire = avis.commentaire[:50] + "..." if len(avis.commentaire) > 50 else avis.commentaire
                print(f"     💬 \"{commentaire}\"")
    
    print(f"\n✅ FONCTIONNALITÉ IMPLÉMENTÉE:")
    print(f"   • Page admin des avis: /admin-panel/avis/")
    print(f"   • Filtrage par type (produits/livreurs)")
    print(f"   • Recherche dans les avis")
    print(f"   • Filtrage par note (1-5 étoiles)")
    print(f"   • Suppression des avis")
    print(f"   • Statistiques en temps réel")
    print(f"   • Interface responsive et moderne")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    afficher_stats_avis()