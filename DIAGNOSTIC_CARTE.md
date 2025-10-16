# 🔍 Diagnostic Carte Leaflet - Problème d'Affichage

## 🚨 Symptôme
La carte se charge mais n'apparaît pas à l'écran.

---

## ✅ Solutions Appliquées

### 1. **CSS Renforcé** 
```css
#deliveryMap {
  width: 100% !important;
  height: 100% !important;
  position: relative;
  z-index: 1;
  background: #e5e7eb; /* Fond visible */
}

.map-wrapper {
  height: calc(100vh - 200px);
  min-height: 500px;
  background: #f0f0f0; /* Fond container */
}
```

### 2. **Logs de Débogage Ajoutés**
```javascript
console.log('🚀 DOM chargé, initialisation...');
console.log('📦 Leaflet disponible:', typeof L !== 'undefined');
console.log('📍 Container existe:', !!document.getElementById('deliveryMap'));
console.log('✅ Carte Leaflet créée');
```

---

## 🔧 Étapes de Diagnostic

### **Étape 1: Vérifier la Console du Navigateur**

Ouvrez la console (F12) et cherchez :

✅ **Succès** :
```
🚀 DOM chargé, initialisation...
📦 Leaflet disponible: true
📍 Container existe: true
🗺️ Initialisation de la carte...
✅ Container trouvé: <div id="deliveryMap"></div>
✅ Carte Leaflet créée
✅ Tuiles OSM ajoutées
```

❌ **Problèmes possibles** :
```
❌ Container #deliveryMap introuvable !
❌ Erreur création carte: [détails]
❌ Leaflet is not defined
```

---

### **Étape 2: Inspecter le DOM**

Ouvrez l'inspecteur (F12 → Elements) et vérifiez :

1. **Container existe** :
   ```html
   <div id="deliveryMap" style="..."></div>
   ```

2. **Hauteur calculée** :
   - Vérifier que `height: XXXpx` (pas 0px)
   - Minimum 500px

3. **Tuiles Leaflet chargées** :
   ```html
   <div class="leaflet-container">
     <div class="leaflet-pane">...</div>
   </div>
   ```

---

### **Étape 3: Vérifier les Erreurs Réseau**

Dans l'onglet **Network** (F12), cherchez :

❌ **Erreurs 404** :
- `leaflet.css` - Feuille de style Leaflet
- `leaflet.js` - Bibliothèque Leaflet
- `https://{s}.tile.openstreetmap.org/...` - Tuiles de carte

✅ **Attendu** :
- Tous les fichiers en **200 OK**
- Tuiles PNG chargées

---

### **Étape 4: Problèmes CSS Communs**

#### **A. Hauteur 0px**
**Cause** : Parent sans hauteur définie

**Solution** :
```css
.map-wrapper {
  height: calc(100vh - 200px) !important;
  min-height: 500px !important;
}
```

#### **B. Z-index caché**
**Cause** : Élément au-dessus de la carte

**Solution** :
```css
#deliveryMap {
  z-index: 1 !important;
  position: relative !important;
}
```

#### **C. Overflow hidden**
**Cause** : Container coupe la carte

**Solution** :
```css
.map-wrapper {
  overflow: hidden; /* OK pour arrondir les coins */
}
#deliveryMap {
  overflow: visible; /* Carte doit déborder si besoin */
}
```

---

### **Étape 5: JavaScript après chargement**

Vérifier que `initMap()` s'exécute **après** :
- ✅ DOM chargé (`DOMContentLoaded`)
- ✅ Leaflet chargé (avant fermeture `</body>`)

**Ordre correct** :
```html
<script src="leaflet.js"></script>
<script src="leaflet.markercluster.js"></script>
<script>
  document.addEventListener('DOMContentLoaded', () => {
    initMap(); // ✅ Bon timing
  });
</script>
```

---

## 🎯 Test Rapide

Ouvrez la console et testez manuellement :

```javascript
// 1. Vérifier Leaflet
console.log(L); // Doit afficher l'objet Leaflet

// 2. Vérifier container
const el = document.getElementById('deliveryMap');
console.log(el); // Doit afficher <div>
console.log(getComputedStyle(el).height); // Doit être > 0px

// 3. Créer carte test
const testMap = L.map('deliveryMap').setView([14.6928, -17.4467], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(testMap);
// La carte devrait apparaître !
```

---

## 🐛 Problèmes Fréquents

### **1. Leaflet CSS manquant**
**Symptôme** : Carte présente mais mal affichée (tuiles décalées)

**Solution** :
```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
```

### **2. Container dans un élément display:none**
**Symptôme** : Carte ne se charge que si on resize la fenêtre

**Solution** :
```javascript
// Après affichage du container
map.invalidateSize();
```

### **3. Conflits CSS Bootstrap/AdminLTE**
**Symptôme** : Hauteur écrasée par framework CSS

**Solution** :
```css
#deliveryMap {
  height: 100% !important; /* Force la hauteur */
}
```

### **4. Script chargé trop tôt**
**Symptôme** : `Cannot read property 'map' of undefined`

**Solution** :
```javascript
// Attendre Leaflet
if (typeof L !== 'undefined') {
  initMap();
} else {
  console.error('Leaflet pas encore chargé');
}
```

---

## 📸 Captures de Référence

### **Console attendue** :
```
🚀 DOM chargé, initialisation...
📦 Leaflet disponible: true
📍 Container existe: true
🗺️ Initialisation de la carte...
✅ Container trouvé: <div id="deliveryMap">
✅ Carte Leaflet créée
✅ Tuiles OSM ajoutées
✅ Cluster ajouté
✅ 15 marqueurs chargés
```

### **DOM attendu** :
```html
<div class="map-wrapper" style="height: 600px;">
  <div id="deliveryMap" style="position: relative; height: 100%;">
    <div class="leaflet-container" style="...">
      <div class="leaflet-pane leaflet-map-pane">
        <div class="leaflet-pane leaflet-tile-pane">
          <img src="https://a.tile.openstreetmap.org/12/2046/2044.png">
        </div>
      </div>
    </div>
  </div>
</div>
```

---

## ✅ Checklist de Vérification

- [ ] Console : Aucune erreur JavaScript
- [ ] Console : Logs "✅ Carte Leaflet créée"
- [ ] Network : leaflet.css chargé (200 OK)
- [ ] Network : leaflet.js chargé (200 OK)
- [ ] Network : Tuiles PNG chargées (200 OK)
- [ ] Inspecteur : `<div class="leaflet-container">` existe
- [ ] Inspecteur : Height > 0px sur #deliveryMap
- [ ] Inspecteur : Background gris visible sur .map-wrapper
- [ ] Carte visible : Tuiles OSM affichées
- [ ] Zoom : Boutons +/- fonctionnels

---

## 🆘 Si Rien ne Fonctionne

### **Version Simplifiée de Test**

Créez un fichier `test_map.html` :

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    #map { height: 500px; }
  </style>
</head>
<body>
  <div id="map"></div>
  
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map('map').setView([14.6928, -17.4467], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    console.log('✅ Carte test OK');
  </script>
</body>
</html>
```

Si cette version fonctionne → Le problème vient du template Django.
Si elle ne fonctionne pas → Problème réseau ou navigateur.

---

Date: 7 octobre 2025
Status: 🔧 En diagnostic
