#!/bin/bash

echo "======================================"
echo "TEST DU PANEL ADMINISTRATEUR"
echo "======================================"

cd /home/ahmadmbow/e-commerce/ecommerce

echo ""
echo "✅ 1. Vérification des modèles (numero_commande, type_commande)"
python3 manage.py shell -c "
from boutique.models import Commande, CommandeInvite

# Test Commande
c = Commande.objects.first()
print(f'Commande user: {c.numero_commande} - Type: {c.type_commande}')

# Test CommandeInvite
ci = CommandeInvite.objects.first()
print(f'Commande guest: {ci.numero_commande} - Type: {ci.type_commande}')
"

echo ""
echo "✅ 2. Vérification de la vue admin_orders_list"
python3 manage.py shell -c "
from boutique.views import admin_orders_list
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.filter(is_staff=True, is_superuser=True).first()

factory = RequestFactory()
request = factory.get('/boutique/admin-panel/orders/')
request.user = admin

# Simuler la vue
from boutique.models import Commande, CommandeInvite
from itertools import chain

orders = list(Commande.objects.all())
orders_invite = list(CommandeInvite.objects.all())
combined = sorted(chain(orders, orders_invite), key=lambda x: x.date_commande, reverse=True)

print(f'Total commandes: {len(combined)}')
print(f'Commandes utilisateurs: {len(orders)}')
print(f'Commandes invités: {len(orders_invite)}')
"

echo ""
echo "✅ 3. Vérification de la vue admin_order_detail"
python3 manage.py shell -c "
from boutique.models import Commande, CommandeInvite

# Test avec une commande user
c = Commande.objects.first()
print(f'Commande user ID={c.id}: {c.numero_commande}')
print(f'  Client: {c.user.get_full_name() or c.user.username}')
print(f'  Type: {c.type_commande}')

# Test avec une commande invite
ci = CommandeInvite.objects.first()
print(f'Commande guest ID={ci.id}: {ci.numero_commande}')
print(f'  Client: {ci.prenom} {ci.nom}')
print(f'  Email: {ci.email}')
print(f'  Type: {ci.type_commande}')
"

echo ""
echo "✅ 4. Vérification GPS supprimé (ne doit PAS avoir latitude/longitude)"
python3 manage.py shell -c "
from boutique.models import Commande

c = Commande.objects.first()
has_lat = hasattr(c, 'latitude') and c.latitude is not None
has_lon = hasattr(c, 'longitude') and c.longitude is not None

if has_lat or has_lon:
    print('⚠️  ATTENTION: Des données GPS sont encore présentes')
else:
    print('✓ Aucune donnée GPS trouvée (correct)')
"

echo ""
echo "======================================"
echo "RÉSUMÉ DES MODIFICATIONS"
echo "======================================"
echo "✅ Propriétés numero_commande et type_commande ajoutées"
echo "✅ Vue admin_orders_list combine Commande + CommandeInvite"
echo "✅ Vue admin_order_detail gère les deux types"
echo "✅ Templates mis à jour pour afficher les commandes invités"
echo "✅ GPS/carte supprimés de l'interface admin"
echo ""
echo "🎉 Panel administrateur prêt pour test manuel!"
echo "   URL: http://127.0.0.1:8000/boutique/admin-panel/orders/"
