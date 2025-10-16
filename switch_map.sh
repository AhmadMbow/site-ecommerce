#!/bin/bash

# Script pour basculer entre Google Maps et Leaflet dans le dashboard livreur

TEMPLATE_DIR="/home/ahmadmbow/e-commerce/ecommerce/templates/livreur"

echo "🗺️  DashLivr - Sélecteur de Carte"
echo "=================================="
echo ""
echo "1) Google Maps (nécessite clé API)"
echo "2) Leaflet/OpenStreetMap (gratuit)"
echo "3) Voir la version actuelle"
echo "4) Quitter"
echo ""
read -p "Votre choix (1-4): " choice

case $choice in
  1)
    if [ -f "$TEMPLATE_DIR/dashboard_google.html" ]; then
      cp "$TEMPLATE_DIR/dashboard.html" "$TEMPLATE_DIR/dashboard_leaflet.html"
      cp "$TEMPLATE_DIR/dashboard_google.html" "$TEMPLATE_DIR/dashboard.html"
      echo "✅ Basculé vers Google Maps"
      echo "⚠️  N'oubliez pas de configurer votre clé API (voir GOOGLE_MAPS_SETUP.md)"
    else
      echo "❌ Fichier dashboard_google.html introuvable"
    fi
    ;;
  2)
    if [ -f "$TEMPLATE_DIR/dashboard_leaflet.html" ]; then
      cp "$TEMPLATE_DIR/dashboard.html" "$TEMPLATE_DIR/dashboard_google.html"
      cp "$TEMPLATE_DIR/dashboard_leaflet.html" "$TEMPLATE_DIR/dashboard.html"
      echo "✅ Basculé vers Leaflet (gratuit)"
      echo "ℹ️  Aucune configuration nécessaire !"
    else
      echo "❌ Fichier dashboard_leaflet.html introuvable"
    fi
    ;;
  3)
    if grep -q "google.maps" "$TEMPLATE_DIR/dashboard.html"; then
      echo "📍 Version actuelle: Google Maps"
    elif grep -q "leaflet" "$TEMPLATE_DIR/dashboard.html"; then
      echo "📍 Version actuelle: Leaflet/OpenStreetMap"
    else
      echo "❓ Version inconnue"
    fi
    ;;
  4)
    echo "👋 Au revoir!"
    exit 0
    ;;
  *)
    echo "❌ Choix invalide"
    exit 1
    ;;
esac
