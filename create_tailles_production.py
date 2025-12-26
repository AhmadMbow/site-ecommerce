#!/usr/bin/env python
"""
Script pour créer les tailles dans la base de données de production
À exécuter sur le serveur via SSH
"""

import os
import sys
import django

# Configuration Django
sys.path.insert(0, '/home/afjqtuev/sadiboushop.com')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings_production')
django.setup()

from boutique.models import Taille

def create_tailles():
    """Créer les tailles standard si elles n'existent pas"""
    tailles_data = [
        {'nom': 'XS', 'ordre': 1},
        {'nom': 'S', 'ordre': 2},
        {'nom': 'M', 'ordre': 3},
        {'nom': 'L', 'ordre': 4},
        {'nom': 'XL', 'ordre': 5},
        {'nom': 'XXL', 'ordre': 6},
        {'nom': 'XXXL', 'ordre': 7},
    ]
    
    print("🔍 Vérification des tailles existantes...")
    existing = Taille.objects.count()
    print(f"   Tailles actuelles: {existing}")
    
    if existing > 0:
        print("\n📋 Tailles existantes:")
        for t in Taille.objects.all().order_by('ordre'):
            print(f"   - {t.nom} (ordre: {t.ordre})")
        print("\n⚠️  Des tailles existent déjà. Voulez-vous les recréer?")
        return
    
    print("\n✨ Création des tailles...")
    created_count = 0
    
    for taille_data in tailles_data:
        taille, created = Taille.objects.get_or_create(
            nom=taille_data['nom'],
            defaults={'ordre': taille_data['ordre']}
        )
        if created:
            print(f"   ✅ Taille '{taille.nom}' créée (ordre: {taille.ordre})")
            created_count += 1
        else:
            print(f"   ⏭️  Taille '{taille.nom}' existe déjà")
    
    print(f"\n🎉 Terminé ! {created_count} taille(s) créée(s)")
    print(f"   Total: {Taille.objects.count()} tailles disponibles")

if __name__ == '__main__':
    try:
        create_tailles()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
