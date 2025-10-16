#!/bin/bash

echo "🎨 VÉRIFICATION DES COULEURS NOIR & JAUNE"
echo "=========================================="
echo ""

FILE="templates/boutique/profile.html"

# Compter les couleurs
echo "📊 Statistiques des couleurs :"
echo ""

# Jaune/Or (#ffc107)
YELLOW_COUNT=$(grep -o "#ffc107\|#ffb300" "$FILE" | wc -l)
echo "   🟡 Jaune/Or (#ffc107, #ffb300): $YELLOW_COUNT occurrences"

# Noir (#232526, #1a1c1d)
BLACK_COUNT=$(grep -o "#232526\|#1a1c1d\|#3a3d40" "$FILE" | wc -l)
echo "   ⚫ Noir (#232526, #1a1c1d, #3a3d40): $BLACK_COUNT occurrences"

# Vérifier les anciennes couleurs (violet/rose)
OLD_COLORS=$(grep -o "#667eea\|#f093fb\|#764ba2" "$FILE" | wc -l)
echo "   ❌ Anciennes couleurs (violet/rose): $OLD_COLORS occurrences"

echo ""
echo "✅ ÉLÉMENTS PRINCIPAUX :"
echo ""

# Vérifier les composants clés
if grep -q "background: linear-gradient(135deg, #232526" "$FILE"; then
    echo "   ✅ Header: Fond noir avec dégradé"
fi

if grep -q "border.*rgba(255, 193, 7" "$FILE"; then
    echo "   ✅ Cards: Bordures jaunes"
fi

if grep -q "color: #ffc107" "$FILE"; then
    echo "   ✅ Titres: Couleur jaune"
fi

if grep -q "background: linear-gradient.*#ffc107" "$FILE"; then
    echo "   ✅ Boutons: Dégradé jaune"
fi

if grep -q "border: 4px solid #ffc107" "$FILE"; then
    echo "   ✅ Avatar: Bordure jaune"
fi

if grep -q "background: rgba(26, 28, 29" "$FILE"; then
    echo "   ✅ Cards: Fond noir translucide"
fi

echo ""
echo "🎯 RÉSUMÉ :"
echo ""
if [ $OLD_COLORS -eq 0 ]; then
    echo "   ✅ Toutes les anciennes couleurs ont été remplacées"
else
    echo "   ⚠️  Il reste $OLD_COLORS anciennes couleurs à remplacer"
fi

if [ $YELLOW_COUNT -gt 30 ] && [ $BLACK_COUNT -gt 30 ]; then
    echo "   ✅ Profil aux couleurs de la boutique (noir & jaune)"
    echo ""
    echo "🎉 TRANSFORMATION RÉUSSIE !"
else
    echo "   ⚠️  Certaines couleurs n'ont pas été appliquées"
fi

echo ""
