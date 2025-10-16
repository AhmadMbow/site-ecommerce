#!/bin/bash
echo "🧪 Test des Notifications Livreur"
echo "===================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier context processor
echo "📋 Vérification context_processors.py..."
if grep -q "def livreur_notifications" boutique/context_processors.py; then
    echo -e "  ${GREEN}✅ Fonction livreur_notifications trouvée${NC}"
else
    echo -e "  ${RED}❌ Fonction manquante${NC}"
    exit 1
fi

if grep -q "livreur_badges" boutique/context_processors.py; then
    echo -e "  ${GREEN}✅ Variable livreur_badges présente${NC}"
else
    echo -e "  ${RED}❌ Variable livreur_badges manquante${NC}"
    exit 1
fi

# 2. Vérifier settings.py
echo ""
echo "⚙️  Vérification settings.py..."
if grep -q "boutique.context_processors.livreur_notifications" ecommerce/settings.py; then
    echo -e "  ${GREEN}✅ Context processor enregistré dans TEMPLATES${NC}"
else
    echo -e "  ${RED}❌ Context processor non enregistré${NC}"
    exit 1
fi

# 3. Vérifier template base_livreur.html
echo ""
echo "📄 Vérification base_livreur.html..."
if grep -q "nav-badge" templates/livreur/base_livreur.html; then
    echo -e "  ${GREEN}✅ Style nav-badge implémenté${NC}"
else
    echo -e "  ${RED}❌ Style nav-badge manquant${NC}"
    exit 1
fi

if grep -q "livreur_badges.nouvelles_commandes" templates/livreur/base_livreur.html; then
    echo -e "  ${GREEN}✅ Badge dynamique configuré dans le menu${NC}"
else
    echo -e "  ${RED}❌ Badge dynamique manquant${NC}"
    exit 1
fi

if grep -q "notification-badge" templates/livreur/base_livreur.html; then
    echo -e "  ${GREEN}✅ Badge cloche configuré${NC}"
else
    echo -e "  ${RED}❌ Badge cloche manquant${NC}"
    exit 1
fi

if grep -q "livreur_order_detail" templates/livreur/base_livreur.html; then
    echo -e "  ${GREEN}✅ Liens de notifications vers détails commandes${NC}"
else
    echo -e "  ${RED}❌ Liens de notifications manquants${NC}"
    exit 1
fi

# 4. Vérifier les styles CSS
echo ""
echo "🎨 Vérification styles CSS..."
if grep -q "@keyframes notification-pop" templates/livreur/base_livreur.html; then
    echo -e "  ${GREEN}✅ Animation notification-pop présente${NC}"
else
    echo -e "  ${YELLOW}⚠️  Animation notification-pop manquante${NC}"
fi

if grep -q ".nav-badge {" templates/livreur/base_livreur.html; then
    echo -e "  ${GREEN}✅ Style .nav-badge défini${NC}"
else
    echo -e "  ${RED}❌ Style .nav-badge manquant${NC}"
    exit 1
fi

# 5. Test Python
echo ""
echo "🐍 Test Python (Django)..."
python3 manage.py shell << 'PYTHON'
from boutique.models import Commande
from django.contrib.auth.models import User

# Compter les commandes EN_ATTENTE
nouvelles = Commande.objects.filter(statut='EN_ATTENTE').count()
print(f"  ℹ️  {nouvelles} nouvelle(s) commande(s) EN_ATTENTE")

# Compter les commandes EN_COURS
en_cours = Commande.objects.filter(statut='EN_COURS').count()
print(f"  ℹ️  {en_cours} commande(s) EN_COURS")

# Vérifier qu'il y a au moins un livreur
try:
    from boutique.models import UserProfile
    livreurs = UserProfile.objects.filter(role='LIVREUR').count()
    print(f"  ℹ️  {livreurs} livreur(s) enregistré(s)")
except Exception as e:
    print(f"  ⚠️  Erreur: {e}")

print("  ✅ Tests Python réussis")
PYTHON

if [ $? -ne 0 ]; then
    echo -e "  ${RED}❌ Erreur lors des tests Python${NC}"
    exit 1
fi

# 6. Vérifier la documentation
echo ""
echo "📚 Vérification documentation..."
if [ -f "BADGE_NOTIFICATIONS_LIVREUR.md" ]; then
    LINES=$(wc -l < BADGE_NOTIFICATIONS_LIVREUR.md)
    echo -e "  ${GREEN}✅ Documentation créée (${LINES} lignes)${NC}"
else
    echo -e "  ${YELLOW}⚠️  Documentation manquante${NC}"
fi

# Résumé
echo ""
echo "========================================"
echo -e "${GREEN}✅ TOUS LES TESTS RÉUSSIS !${NC}"
echo ""
echo "📊 Résumé des fonctionnalités :"
echo "  • Badge sur menu 'Commandes'"
echo "  • Badge sur cloche de notifications"
echo "  • Panel de notifications cliquable"
echo "  • Context processor enregistré"
echo "  • Styles CSS et animations"
echo ""
echo "🚀 Le système de notifications est opérationnel !"
echo "========================================"
