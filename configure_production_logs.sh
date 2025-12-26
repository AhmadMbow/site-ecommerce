#!/bin/bash

# Script pour configurer les logs en production
echo "🔧 Configuration des logs pour la production"
echo "=============================================="
echo ""

# Déterminer le chemin du projet
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📂 Répertoire du projet: $SCRIPT_DIR"
echo ""

# Créer le dossier logs s'il n'existe pas
echo "1️⃣ Création du dossier logs..."
mkdir -p logs
chmod 755 logs

# Créer les fichiers de logs
echo "2️⃣ Création des fichiers de logs..."
touch logs/django_errors.log
touch logs/django.log
touch logs/production.log

# Donner les permissions appropriées
chmod 666 logs/django_errors.log
chmod 666 logs/django.log
chmod 666 logs/production.log

echo "✅ Fichiers de logs créés:"
ls -lh logs/

echo ""
echo "3️⃣ Test d'écriture dans les logs..."
echo "[$(date)] Test de configuration - Logs initialisés" >> logs/django_errors.log
echo "[$(date)] Test de configuration - Logs initialisés" >> logs/django.log

if [ -f logs/django_errors.log ] && [ -w logs/django_errors.log ]; then
    echo "✅ Logs configurés avec succès!"
else
    echo "❌ Erreur: Impossible d'écrire dans les logs"
fi

echo ""
echo "4️⃣ Chemin complet des logs:"
echo "   $(realpath logs/django_errors.log)"
echo ""

echo "📋 Commandes utiles pour voir les logs:"
echo "   tail -f $SCRIPT_DIR/logs/django_errors.log"
echo "   tail -f $SCRIPT_DIR/logs/django.log"
echo "   tail -100 $SCRIPT_DIR/logs/django_errors.log"
echo ""

# Créer un fichier .htaccess pour protéger le dossier logs (si Apache)
if [ ! -f logs/.htaccess ]; then
    echo "5️⃣ Protection du dossier logs..."
    cat > logs/.htaccess << 'EOF'
# Bloquer l'accès web au dossier logs
Order deny,allow
Deny from all
EOF
    echo "✅ Dossier logs protégé"
fi

echo ""
echo "✨ Configuration terminée!"
echo ""
echo "💡 Sur votre serveur de production, exécutez:"
echo "   cd ~/chemin-vers-votre-projet"
echo "   bash configure_production_logs.sh"
