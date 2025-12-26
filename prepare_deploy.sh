#!/bin/bash
# =============================================================================
# Script de préparation pour le déploiement sur Namecheap
# Site: sadiboushop.com
# =============================================================================

echo "🚀 Préparation du déploiement pour sadiboushop.com"
echo "=================================================="

# Répertoire du projet
PROJECT_DIR="/home/ahmadmbow/e-commerce/ecommerce"
cd "$PROJECT_DIR"

# Activation de l'environnement virtuel
echo ""
echo "📦 Activation de l'environnement virtuel..."
source venv/bin/activate

# Installation des dépendances de production
echo ""
echo "📥 Installation des dépendances de production..."
pip install whitenoise python-dotenv gunicorn

# Mise à jour de requirements.txt
echo ""
echo "📝 Mise à jour de requirements.txt..."
pip freeze > requirements_full.txt

# Collecte des fichiers statiques
echo ""
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --settings=ecommerce.settings_production --noinput 2>/dev/null || {
    echo "⚠️  Collectstatic avec erreur (normal si DB non configurée)"
}

# Vérification de la configuration
echo ""
echo "✅ Vérification de la configuration Django..."
python manage.py check --settings=ecommerce.settings_production 2>/dev/null || {
    echo "⚠️  Check avec avertissements (normal pour la DB)"
}

# Création de l'archive ZIP
echo ""
echo "📦 Création de l'archive pour upload..."
cd /home/ahmadmbow/e-commerce

# Liste des fichiers/dossiers à exclure
EXCLUDES=(
    "ecommerce/venv/*"
    "ecommerce/.git/*"
    "ecommerce/__pycache__/*"
    "ecommerce/*/__pycache__/*"
    "ecommerce/*/*/__pycache__/*"
    "*.pyc"
    "*.pyo"
    "ecommerce/db.sqlite3"
    "ecommerce/*.md"
    "ecommerce/*.sh"
    "ecommerce/*.py"
    "ecommerce/AdminLTE-master/*"
    "ecommerce/startbootstrap-shop-homepage-gh-pages/*"
)

# Construire la commande d'exclusion
EXCLUDE_CMD=""
for pattern in "${EXCLUDES[@]}"; do
    EXCLUDE_CMD="$EXCLUDE_CMD -x \"$pattern\""
done

# Créer l'archive
rm -f sadiboushop_deploy.zip
eval "zip -r sadiboushop_deploy.zip ecommerce $EXCLUDE_CMD"

echo ""
echo "=================================================="
echo "✅ Préparation terminée!"
echo ""
echo "📁 Archive créée: /home/ahmadmbow/e-commerce/sadiboushop_deploy.zip"
echo ""
echo "📋 Prochaines étapes:"
echo "   1. Connectez-vous à cPanel Namecheap"
echo "   2. Allez dans 'Setup Python App' et créez l'application"
echo "   3. Uploadez sadiboushop_deploy.zip via File Manager"
echo "   4. Configurez la base de données MySQL"
echo "   5. Suivez le guide DEPLOIEMENT_NAMECHEAP.md"
echo ""
echo "🔗 Guide complet: $PROJECT_DIR/DEPLOIEMENT_NAMECHEAP.md"
