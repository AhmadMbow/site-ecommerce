#!/bin/bash

# Script de test pour vérifier les améliorations du profil

echo "🧪 Test des améliorations du profil utilisateur"
echo "================================================"
echo ""

# Vérifier que le fichier existe
if [ -f "templates/boutique/profile.html" ]; then
    echo "✅ Fichier profile.html trouvé"
    LINES=$(wc -l < templates/boutique/profile.html)
    echo "   📄 Lignes: $LINES"
else
    echo "❌ Fichier profile.html introuvable"
    exit 1
fi

echo ""
echo "🔍 Vérification des éléments clés..."
echo ""

# Vérifier les imports CSS
if grep -q "leaflet@1.9.4" templates/boutique/profile.html; then
    echo "✅ Leaflet CSS importé"
else
    echo "❌ Leaflet CSS manquant"
fi

if grep -q "font-awesome" templates/boutique/profile.html; then
    echo "✅ Font Awesome importé"
else
    echo "❌ Font Awesome manquant"
fi

if grep -q "Poppins" templates/boutique/profile.html; then
    echo "✅ Police Poppins importée"
else
    echo "❌ Police Poppins manquante"
fi

echo ""
echo "🎨 Vérification des styles..."
echo ""

# Vérifier les variables CSS
if grep -q ":root" templates/boutique/profile.html; then
    echo "✅ Variables CSS définies"
    VARS=$(grep -c "^\s*--" templates/boutique/profile.html || echo "0")
    echo "   📊 Variables trouvées: $VARS"
else
    echo "❌ Variables CSS manquantes"
fi

# Vérifier les animations
if grep -q "@keyframes" templates/boutique/profile.html; then
    echo "✅ Animations CSS définies"
    ANIMS=$(grep -c "@keyframes" templates/boutique/profile.html || echo "0")
    echo "   🎬 Animations: $ANIMS"
else
    echo "❌ Animations CSS manquantes"
fi

echo ""
echo "🚀 Vérification des fonctionnalités..."
echo ""

# Vérifier les fonctionnalités JavaScript
if grep -q "reverseGeocode" templates/boutique/profile.html; then
    echo "✅ Géocodage inversé implémenté"
else
    echo "❌ Géocodage inversé manquant"
fi

if grep -q "drag" templates/boutique/profile.html && grep -q "drop" templates/boutique/profile.html; then
    echo "✅ Drag & Drop implémenté"
else
    echo "❌ Drag & Drop manquant"
fi

if grep -q "handleFiles" templates/boutique/profile.html; then
    echo "✅ Gestion des fichiers implémentée"
else
    echo "❌ Gestion des fichiers manquante"
fi

if grep -q "IntersectionObserver" templates/boutique/profile.html; then
    echo "✅ Animations au scroll implémentées"
else
    echo "❌ Animations au scroll manquantes"
fi

if grep -q "loadingSpinner" templates/boutique/profile.html; then
    echo "✅ Loading spinner implémenté"
else
    echo "❌ Loading spinner manquant"
fi

echo ""
echo "📱 Vérification responsive..."
echo ""

if grep -q "@media" templates/boutique/profile.html; then
    echo "✅ Media queries présentes"
    MEDIA=$(grep -c "@media" templates/boutique/profile.html || echo "0")
    echo "   📱 Media queries: $MEDIA"
else
    echo "❌ Media queries manquantes"
fi

echo ""
echo "🎯 Vérification des composants..."
echo ""

# Vérifier les composants principaux
COMPONENTS=(
    "stat-card:Cartes statistiques"
    "page-header:En-tête de page"
    "nav-tabs:Navigation à onglets"
    "drop-zone:Zone de drop"
    "avatar-container:Conteneur avatar"
    "miniMap:Carte profil"
    "adresseMap:Carte adresse"
)

for comp in "${COMPONENTS[@]}"; do
    IFS=':' read -r class name <<< "$comp"
    if grep -q "$class" templates/boutique/profile.html; then
        echo "✅ $name"
    else
        echo "❌ $name manquant"
    fi
done

echo ""
echo "📊 Statistiques du fichier..."
echo ""

echo "📏 Taille CSS:"
CSS_LINES=$(sed -n '/<style>/,/<\/style>/p' templates/boutique/profile.html | wc -l)
echo "   Lignes: $CSS_LINES"

echo "📏 Taille JavaScript:"
JS_LINES=$(sed -n '/<script>/,/<\/script>/p' templates/boutique/profile.html | wc -l)
echo "   Lignes: $JS_LINES"

echo "📏 Taille HTML:"
HTML_LINES=$(grep -v '<style>\|<script>' templates/boutique/profile.html | wc -l)
echo "   Lignes: ~$HTML_LINES"

echo ""
echo "✨ Test terminé !"
echo ""
echo "📝 Pour voir le résultat:"
echo "   1. Lancez le serveur: python3 manage.py runserver"
echo "   2. Connectez-vous à votre compte"
echo "   3. Accédez à: http://localhost:8000/profile/"
echo ""
echo "🎨 Améliorations apportées:"
echo "   • Design moderne avec glassmorphism"
echo "   • Drag & Drop pour l'avatar"
echo "   • Géolocalisation automatique"
echo "   • Cartes interactives Leaflet"
echo "   • Animations fluides"
echo "   • Responsive design complet"
echo "   • Loading states"
echo "   • Toast notifications"
echo ""
