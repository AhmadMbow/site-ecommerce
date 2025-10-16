# Configuration Google Maps pour DashLivr

## 🗺️ Obtenir une Clé API Google Maps

### Étape 1 : Créer un compte Google Cloud
1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Connectez-vous avec votre compte Google
3. Créez un nouveau projet ou sélectionnez-en un existant

### Étape 2 : Activer l'API Google Maps
1. Dans le menu de navigation, allez à **APIs & Services** > **Library**
2. Recherchez et activez ces APIs :
   - **Maps JavaScript API**
   - **Geocoding API**
   - **Directions API**
3. Cliquez sur "Enable" pour chaque API

### Étape 3 : Créer une Clé API
1. Allez dans **APIs & Services** > **Credentials**
2. Cliquez sur **Create Credentials** > **API Key**
3. Copiez votre clé API

### Étape 4 : Sécuriser votre Clé API
1. Cliquez sur l'icône de modification de votre clé
2. Dans **Application restrictions**, sélectionnez "HTTP referrers"
3. Ajoutez ces URLs autorisées :
   ```
   http://localhost:8001/*
   http://127.0.0.1:8001/*
   https://votredomaine.com/*
   ```
4. Dans **API restrictions**, sélectionnez "Restrict key"
5. Cochez uniquement les APIs activées précédemment
6. Cliquez sur **Save**

### Étape 5 : Intégrer la Clé dans votre Application

#### Option 1 : Variables d'environnement (Recommandé)
Créez un fichier `.env` à la racine du projet :
```bash
GOOGLE_MAPS_API_KEY=votre_clé_api_ici
```

Installez python-decouple :
```bash
pip install python-decouple
```

Dans `settings.py` :
```python
from decouple import config

GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')
```

Dans `dashboard/views.py` :
```python
from django.conf import settings

def dashboard(request):
    context = {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        # ... autres données
    }
    return render(request, 'livreur/dashboard.html', context)
```

Dans `dashboard.html`, remplacez la ligne :
```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY&callback=initMap" async defer></script>
```

Par :
```html
<script src="https://maps.googleapis.com/maps/api/js?key={{ google_maps_api_key }}&callback=initMap" async defer></script>
```

#### Option 2 : Directement dans le template (Développement uniquement)
Remplacez `YOUR_GOOGLE_MAPS_API_KEY` par votre vraie clé dans `dashboard.html` ligne 494.

⚠️ **ATTENTION** : Ne committez JAMAIS votre clé API dans Git !

## 🎨 Nouvelles Fonctionnalités du Dashboard

### 1. Cartes de Statistiques Animées
- 4 cartes hero avec gradients colorés
- Animations au survol
- Indicateurs de tendance
- Effets de lumière dynamiques

### 2. Carte Google Maps en Direct
- Affichage en temps réel des livraisons
- Marqueurs colorés par statut :
  - 🟡 Jaune : En attente
  - 🔵 Bleu : En cours (avec animation bounce)
  - 🟢 Vert : Livrée
- InfoWindows avec détails des commandes
- Styles de carte personnalisés

### 3. Actions Rapides
- Boutons avec icônes animées
- Effets hover élégants
- Accès rapide aux fonctions principales

### 4. Graphique de Performance
- Barres animées pour les 7 derniers jours
- Valeurs affichées au survol
- Design moderne avec gradients

### 5. Liste de Commandes Améliorée
- Cartes avec bordure colorée
- Badges de statut stylisés
- Informations organisées en grille
- Boutons d'action contextuels
- Animations au survol

### 6. Auto-refresh
- Mise à jour automatique toutes les 30 secondes
- Animation des changements de valeurs
- Pas de rechargement de page

### 7. Animations
- Apparition progressive au scroll
- Transitions fluides
- Effets de profondeur

## 🎯 Prochaines Améliorations Suggérées

1. **Géolocalisation en temps réel**
   - Suivre la position du livreur
   - Calculer les itinéraires optimaux
   - Estimer les temps de livraison

2. **Notifications Push**
   - Alertes pour nouvelles commandes
   - Notifications de mise à jour de statut

3. **Mode Sombre**
   - Thème sombre pour la nuit

4. **Graphiques Interactifs**
   - Chart.js pour des graphiques plus détaillés
   - Statistiques personnalisables

5. **Export de Données**
   - Télécharger les rapports en PDF/Excel
   - Générer des factures

## 📱 Responsive Design

Le dashboard est entièrement responsive :
- Desktop : Vue complète avec toutes les fonctionnalités
- Tablet : Layout adapté
- Mobile : Navigation optimisée, carte réduite

## 🔧 Personnalisation

### Changer les Couleurs
Dans le CSS, modifiez les variables :
```css
:root {
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-success: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  /* ... */
}
```

### Ajouter des Marqueurs Personnalisés
Dans `addDeliveryMarkers()`, modifiez les icônes :
```javascript
icon: {
  url: '/static/images/custom-marker.png',
  scaledSize: new google.maps.Size(40, 40)
}
```

## 🐛 Dépannage

### La carte ne s'affiche pas
1. Vérifiez que votre clé API est valide
2. Assurez-vous que les APIs sont activées
3. Vérifiez les restrictions d'URL
4. Regardez la console du navigateur pour les erreurs

### Les marqueurs ne s'affichent pas
1. Vérifiez que `initMap()` est bien appelée
2. Assurez-vous que les coordonnées sont valides
3. Vérifiez que la fonction `addDeliveryMarkers()` est exécutée

### Performance lente
1. Limitez le nombre de marqueurs affichés
2. Utilisez le clustering pour regrouper les marqueurs proches
3. Optimisez le rafraîchissement automatique

## 📚 Ressources

- [Documentation Google Maps JavaScript API](https://developers.google.com/maps/documentation/javascript)
- [Exemples de Code](https://developers.google.com/maps/documentation/javascript/examples)
- [Styling Guide](https://mapstyle.withgoogle.com/)

## 💰 Tarification

Google Maps offre :
- **200$ de crédit gratuit par mois**
- Cela équivaut à environ **28,000 chargements de carte gratuits/mois**
- Au-delà : 7$ par 1000 chargements

Pour un usage normal, vous resterez dans les limites gratuites.
