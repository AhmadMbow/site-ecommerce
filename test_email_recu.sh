#!/bin/bash

# Script de test pour l'envoi d'email avec reçu PDF

echo "=========================================="
echo "🧪 TEST ENVOI EMAIL + REÇU PDF"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd /home/ahmadmbow/e-commerce/ecommerce

echo "📋 Vérification des dépendances..."

# Test 1: ReportLab installé
if python3 -c "import reportlab" 2>/dev/null; then
    echo -e "${GREEN}✅ ReportLab installé${NC}"
else
    echo -e "${RED}❌ ReportLab manquant${NC}"
    exit 1
fi

# Test 2: Template email existe
if [ -f "templates/emails/commande_livree.html" ]; then
    echo -e "${GREEN}✅ Template email trouvé${NC}"
else
    echo -e "${RED}❌ Template email manquant${NC}"
    exit 1
fi

# Test 3: Fonctions dans utils.py
if grep -q "def generate_receipt_pdf" boutique/utils.py && \
   grep -q "def send_delivery_email_with_receipt" boutique/utils.py; then
    echo -e "${GREEN}✅ Fonctions trouvées dans utils.py${NC}"
else
    echo -e "${RED}❌ Fonctions manquantes${NC}"
    exit 1
fi

# Test 4: Vue modifiée
if grep -q "send_delivery_email_with_receipt" boutique/views.py; then
    echo -e "${GREEN}✅ Vue livreur_order_update_status modifiée${NC}"
else
    echo -e "${RED}❌ Vue non modifiée${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "📄 Test de génération PDF"
echo "=========================================="

python3 manage.py shell << 'EOF'
from boutique.models import Commande
from boutique.utils import generate_receipt_pdf

commande = Commande.objects.filter(statut='LIVREE').order_by('-id').first()

if commande:
    print(f"\n✅ Commande trouvée: #{commande.id}")
    print(f"   Client: {commande.user.username}")
    print(f"   Email: {commande.user.email}")
    print(f"   Total: {commande.total} F CFA")
    print(f"   Articles: {commande.items.count()}")
    
    try:
        pdf_content = generate_receipt_pdf(commande)
        print(f"\n✅ PDF généré: {len(pdf_content):,} bytes ({len(pdf_content)/1024:.1f} KB)")
        
        with open('test_recu.pdf', 'wb') as f:
            f.write(pdf_content)
        print(f"✅ PDF sauvegardé: test_recu.pdf")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
else:
    print("\n❌ Aucune commande LIVREE trouvée")
    print("   Créez une commande de test d'abord")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ PDF généré avec succès !${NC}"
    echo ""
    echo "📂 Fichier créé: test_recu.pdf"
    echo "   Vous pouvez l'ouvrir avec: xdg-open test_recu.pdf"
else
    echo -e "\n${RED}❌ Échec de la génération PDF${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "📧 Test d'envoi Email (optionnel)"
echo "=========================================="
echo ""
echo -e "${YELLOW}⚠️  Pour tester l'envoi réel d'email:${NC}"
echo ""
echo "python3 manage.py shell"
echo ">>> from boutique.models import Commande"
echo ">>> from boutique.utils import send_delivery_email_with_receipt"
echo ">>> commande = Commande.objects.filter(statut='LIVREE').first()"
echo ">>> success = send_delivery_email_with_receipt(commande)"
echo ">>> print(f'Email envoyé: {success}')"
echo ""
echo -e "${GREEN}✨ Ou marquez une commande comme livrée via l'interface livreur${NC}"
echo ""

echo "=========================================="
echo "✅ TOUS LES TESTS RÉUSSIS !"
echo "=========================================="
echo ""
echo "📝 Résumé:"
echo "  ✅ ReportLab installé"
echo "  ✅ Template email créé"
echo "  ✅ Fonctions dans utils.py"
echo "  ✅ Vue modifiée"
echo "  ✅ PDF généré et testé"
echo ""
echo "🚀 Prêt pour la production !"
echo ""
