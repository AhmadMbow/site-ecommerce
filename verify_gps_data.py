#!/usr/bin/env python
"""
Script de vérification des données GPS des commandes
Exécutez avec: python verify_gps_data.py
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from boutique.models import Commande
from django.contrib.auth.models import User

def verify_gps_data():
    """Vérifie les données GPS de toutes les commandes"""
    
    print("=" * 80)
    print("🔍 VÉRIFICATION DES DONNÉES GPS DES COMMANDES")
    print("=" * 80)
    print()
    
    # Statistiques globales
    total_commandes = Commande.objects.count()
    commandes_avec_gps = Commande.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).count()
    commandes_avec_adresse = Commande.objects.filter(
        adresse_gps__isnull=False
    ).exclude(adresse_gps='').count()
    
    print(f"📊 STATISTIQUES GLOBALES")
    print(f"  • Total de commandes: {total_commandes}")
    print(f"  • Commandes avec coordonnées GPS: {commandes_avec_gps} ({commandes_avec_gps/total_commandes*100:.1f}%)")
    print(f"  • Commandes avec adresse textuelle: {commandes_avec_adresse} ({commandes_avec_adresse/total_commandes*100:.1f}%)")
    print()
    
    # Détail par statut
    print("📈 DÉTAIL PAR STATUT")
    statuts = ['EN_ATTENTE', 'EN_COURS', 'LIVREE', 'ANNULEE']
    for statut in statuts:
        count = Commande.objects.filter(statut=statut).count()
        with_gps = Commande.objects.filter(
            statut=statut,
            latitude__isnull=False,
            longitude__isnull=False
        ).count()
        if count > 0:
            print(f"  {statut:15} : {count:3} commandes ({with_gps:3} avec GPS, {with_gps/count*100:.0f}%)")
    print()
    
    # Liste détaillée
    print("=" * 80)
    print("📋 LISTE DÉTAILLÉE DES COMMANDES")
    print("=" * 80)
    print()
    
    commandes = Commande.objects.all().order_by('-date_commande')[:20]
    
    if not commandes:
        print("❌ Aucune commande trouvée dans la base de données")
        return
    
    for i, commande in enumerate(commandes, 1):
        print(f"{'─' * 80}")
        print(f"📦 Commande #{commande.id} (#{i})")
        print(f"{'─' * 80}")
        print(f"  👤 Client       : {commande.user.username} ({commande.user.get_full_name()})")
        print(f"  📅 Date         : {commande.date_commande.strftime('%d/%m/%Y %H:%M')}")
        print(f"  💰 Total        : {commande.total} €")
        print(f"  📊 Statut       : {commande.statut}")
        
        if commande.livreur:
            print(f"  🚚 Livreur      : {commande.livreur.username}")
        else:
            print(f"  🚚 Livreur      : Non assigné")
        
        print()
        print(f"  🗺️  DONNÉES GPS :")
        
        # Vérification GPS
        has_latitude = commande.latitude is not None
        has_longitude = commande.longitude is not None
        has_adresse = commande.adresse_gps and commande.adresse_gps.strip()
        
        if has_latitude and has_longitude:
            print(f"    ✅ Latitude    : {commande.latitude}")
            print(f"    ✅ Longitude   : {commande.longitude}")
            print(f"    🔗 Google Maps : https://www.google.com/maps?q={commande.latitude},{commande.longitude}")
        else:
            print(f"    ❌ Latitude    : {'NULL' if not has_latitude else commande.latitude}")
            print(f"    ❌ Longitude   : {'NULL' if not has_longitude else commande.longitude}")
        
        if has_adresse:
            print(f"    ✅ Adresse GPS : {commande.adresse_gps}")
        else:
            print(f"    ❌ Adresse GPS : Vide ou NULL")
        
        # Adresse de profil comme fallback
        if commande.user.userprofile and commande.user.userprofile.address:
            print(f"    📍 Profil      : {commande.user.userprofile.address}")
        
        # Résumé
        print()
        if has_latitude and has_longitude:
            print(f"  ✅ STATUS : Coordonnées GPS OK - Marqueur sera affiché sur la carte")
        elif has_adresse:
            print(f"  ⚠️  STATUS : Adresse textuelle seulement - Géocodage nécessaire pour la carte")
        elif commande.user.userprofile and commande.user.userprofile.address:
            print(f"  ⚠️  STATUS : Fallback sur l'adresse du profil")
        else:
            print(f"  ❌ STATUS : Aucune information de localisation disponible")
        
        print()
    
    # Recommandations
    print("=" * 80)
    print("💡 RECOMMANDATIONS")
    print("=" * 80)
    print()
    
    if commandes_avec_gps < total_commandes:
        manquantes = total_commandes - commandes_avec_gps
        print(f"⚠️  {manquantes} commande(s) sans coordonnées GPS")
        print()
        print("Solutions possibles :")
        print("  1. Vérifier que le formulaire de panier capture bien la géolocalisation")
        print("  2. Vérifier que les champs latitude/longitude sont bien envoyés au backend")
        print("  3. Implémenter un système de géocodage pour convertir les adresses textuelles")
        print()
    
    if commandes_avec_gps == total_commandes:
        print("✅ Toutes les commandes ont des coordonnées GPS !")
        print()
    
    print("📝 Pour tester dans Django shell :")
    print("  python manage.py shell")
    print("  >>> from boutique.models import Commande")
    print("  >>> cmd = Commande.objects.get(id=53)  # Remplacer par votre ID")
    print("  >>> print(f'Latitude: {cmd.latitude}, Longitude: {cmd.longitude}')")
    print()

def check_template_files():
    """Vérifie que les templates utilisent les bons champs"""
    
    print("=" * 80)
    print("🔍 VÉRIFICATION DES TEMPLATES")
    print("=" * 80)
    print()
    
    templates_to_check = [
        'templates/livreur/map.html',
        'templates/livreur/orders.html',
    ]
    
    for template_path in templates_to_check:
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), template_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"📄 {template_path}")
            
            # Vérifier les mauvais patterns
            bad_patterns = ['order.adresse.latitude', 'order.adresse.longitude']
            good_patterns = ['order.latitude', 'order.longitude']
            
            has_bad = any(pattern in content for pattern in bad_patterns)
            has_good = any(pattern in content for pattern in good_patterns)
            
            if has_bad:
                print(f"  ❌ ERREUR : Utilise encore 'order.adresse.latitude/longitude'")
                for pattern in bad_patterns:
                    count = content.count(pattern)
                    if count > 0:
                        print(f"     - '{pattern}' trouvé {count} fois")
            elif has_good:
                print(f"  ✅ OK : Utilise correctement 'order.latitude/longitude'")
            else:
                print(f"  ⚠️  ATTENTION : Aucune référence aux champs GPS trouvée")
            
            print()
        else:
            print(f"❌ Fichier non trouvé : {template_path}")
            print()

if __name__ == '__main__':
    try:
        verify_gps_data()
        check_template_files()
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
