#!/bin/bash
# Script de déploiement pour sadiboushop.com

echo "🚀 Démarrage du déploiement..."

# 1. Collecter les fichiers statiques
echo "📦 Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput --settings=ecommerce.settings_production

# 2. Vérifier les migrations
echo "🔄 Vérification des migrations..."
python3 manage.py migrate --settings=ecommerce.settings_production

# 3. Créer le fichier .htaccess si nécessaire
echo "⚙️  Configuration .htaccess..."
cat > .htaccess << 'EOF'
# Configuration pour Namecheap cPanel
PassengerEnabled On
PassengerAppRoot /home/afjqtuev/sadiboushop.com
PassengerBaseURI /
PassengerPython /home/afjqtuev/virtualenv/sadiboushop/3.12/bin/python3

# Servir les fichiers statiques directement
RewriteEngine On
RewriteCond %{REQUEST_URI} ^/static/(.*)$ [OR]
RewriteCond %{REQUEST_URI} ^/media/(.*)$
RewriteRule ^.*$ - [L]

# Forcer HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
EOF

echo "✅ Déploiement terminé!"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Uploadez tous les fichiers sur le serveur"
echo "   2. Créez un environnement virtuel Python 3.12"
echo "   3. Installez les dépendances: pip install -r requirements.txt"
echo "   4. Configurez les variables d'environnement (DB, EMAIL, SECRET_KEY)"
echo "   5. Redémarrez Passenger depuis cPanel"
