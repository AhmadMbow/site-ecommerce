#!/bin/bash

# Script de test pour diagnostiquer les erreurs de commande

echo "🔍 Test de la fonctionnalité de commande"
echo "========================================"
echo ""

cd "$(dirname "$0")"

echo "1️⃣ Vérification du modèle Commande..."
python3 manage.py shell << EOF
from boutique.models import Commande, Adresse, PanierItem
from django.contrib.auth.models import User

# Vérifier les champs du modèle Commande
print("\n📋 Champs du modèle Commande:")
for field in Commande._meta.get_fields():
    print(f"  - {field.name}: {field.__class__.__name__}")

# Vérifier s'il y a des utilisateurs
print(f"\n👥 Nombre d'utilisateurs: {User.objects.count()}")

# Vérifier s'il y a des paniers actifs
print(f"\n🛒 Paniers actifs: {PanierItem.objects.count()}")

# Vérifier s'il y a des adresses
print(f"\n📍 Adresses enregistrées: {Adresse.objects.count()}")

# Vérifier les commandes existantes
print(f"\n📦 Commandes existantes: {Commande.objects.count()}")

EOF

echo ""
echo "2️⃣ Vérification des logs d'erreur..."
if [ -f logs/django_errors.log ]; then
    echo "📄 Dernières erreurs dans django_errors.log:"
    tail -20 logs/django_errors.log
else
    echo "⚠️  Aucun fichier de log trouvé"
fi

echo ""
echo "3️⃣ Test terminé!"
echo ""
echo "💡 Pour tester une commande complète, connectez-vous sur http://127.0.0.1:8000"
echo "   et essayez de passer une commande. Les logs seront dans logs/django_errors.log"
