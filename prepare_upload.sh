#!/bin/bash
# Script pour préparer le déploiement sur sadiboushop.com

echo "🎯 Préparation du déploiement pour sadiboushop.com"
echo "=================================================="
echo ""

# 1. Collecter les fichiers statiques
echo "📦 Étape 1/4: Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput --settings=ecommerce.settings_production
if [ $? -eq 0 ]; then
    echo "✅ Fichiers statiques collectés"
else
    echo "❌ Erreur lors de la collecte des fichiers statiques"
    exit 1
fi
echo ""

# 2. Créer une archive des fichiers statiques pour upload facile
echo "📦 Étape 2/4: Création de l'archive staticfiles.tar.gz..."
if [ -d "staticfiles" ]; then
    tar -czf staticfiles.tar.gz staticfiles/
    echo "✅ Archive créée: staticfiles.tar.gz ($(du -h staticfiles.tar.gz | cut -f1))"
else
    echo "❌ Le dossier staticfiles n'existe pas"
    exit 1
fi
echo ""

# 3. Vérifier les fichiers essentiels
echo "🔍 Étape 3/4: Vérification des fichiers essentiels..."
files_to_check=(
    ".htaccess"
    "passenger_wsgi.py"
    "ecommerce/settings_production.py"
    "requirements.txt"
    "manage.py"
)

all_files_exist=true
for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file MANQUANT"
        all_files_exist=false
    fi
done
echo ""

if [ "$all_files_exist" = false ]; then
    echo "❌ Certains fichiers essentiels sont manquants"
    exit 1
fi

# 4. Créer un résumé des fichiers à uploader
echo "📋 Étape 4/4: Création de la liste des fichiers à uploader..."
cat > FILES_TO_UPLOAD.txt << 'EOF'
📤 FICHIERS À UPLOADER SUR NAMECHEAP
====================================

1. FICHIERS MODIFIÉS (obligatoire):
   ├── .htaccess
   └── staticfiles/ (TOUT LE DOSSIER)

2. ALTERNATIVE - Upload via archive:
   └── staticfiles.tar.gz (puis extraire sur le serveur)

3. STRUCTURE FINALE SUR LE SERVEUR:
   /home/afjqtuev/sadiboushop.com/
   ├── staticfiles/
   │   ├── admin/
   │   ├── css/
   │   ├── js/
   │   └── images/
   ├── .htaccess
   ├── passenger_wsgi.py
   └── ...

4. APRÈS L'UPLOAD:
   □ Vérifier permissions (755 pour dossiers, 644 pour fichiers)
   □ Redémarrer l'app dans "Setup Python App"
   □ Vider le cache du navigateur
   □ Tester: https://sadiboushop.com

EOF

cat FILES_TO_UPLOAD.txt
echo ""

# 5. Afficher un résumé
echo "✨ Préparation terminée!"
echo ""
echo "📁 Fichiers créés:"
echo "   - staticfiles/ (310 fichiers)"
echo "   - staticfiles.tar.gz (pour upload)"
echo "   - FILES_TO_UPLOAD.txt (liste des actions)"
echo ""
echo "🚀 PROCHAINES ÉTAPES:"
echo "   1. Uploadez staticfiles.tar.gz sur cPanel"
echo "   2. Extrayez l'archive sur le serveur"
echo "   3. Uploadez le .htaccess mis à jour"
echo "   4. Redémarrez l'application"
echo "   5. Testez le site"
echo ""
echo "📖 Consultez FIX_STYLES_PRODUCTION.md pour le guide détaillé"
