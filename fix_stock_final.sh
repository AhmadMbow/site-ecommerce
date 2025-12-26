#!/bin/bash

echo "=========================================="
echo "FIX FINAL GESTION STOCK - UPLOAD"
echo "=========================================="

# Créer le tar avec le fichier views.py
echo "📦 Création de l'archive..."
tar -czf fix_stock_views.tar.gz -C boutique views.py

echo "✅ Archive créée: fix_stock_views.tar.gz ($(du -h fix_stock_views.tar.gz | cut -f1))"
echo ""
echo "=========================================="
echo "COMMANDES SSH À EXÉCUTER"
echo "=========================================="
echo ""
echo "1️⃣ Upload depuis votre machine locale:"
echo "   scp fix_stock_views.tar.gz afjqtuev@sadiboushop.com:~/"
echo ""
echo "2️⃣ Connectez-vous au serveur:"
echo "   ssh afjqtuev@sadiboushop.com"
echo ""
echo "3️⃣ Sur le serveur, extraire et redémarrer:"
cat << 'EOF'
cd ~/sadiboushop.com
tar -xzf ~/fix_stock_views.tar.gz
mkdir -p tmp
touch tmp/restart.txt
echo "✅ Fichier extrait et serveur redémarré"
rm ~/fix_stock_views.tar.gz
EOF
echo ""
echo "=========================================="
echo "TEST APRÈS UPLOAD"
echo "=========================================="
echo "1. Allez sur https://sadiboushop.com/admin/products/add/"
echo "2. Vous devriez voir la grille de tailles (XS, S, M, L, XL, XXL, XXXL)"
echo "3. Entrez des stocks et sauvegardez"
echo "=========================================="
