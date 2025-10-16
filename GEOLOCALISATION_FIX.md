# 🗺️ SYSTÈME DE GÉOLOCALISATION - GUIDE COMPLET

## ✅ Problème Résolu

**Avant:** Le template cherchait `order.adresse.latitude` alors que les données sont stockées directement dans `order.latitude`

**Après:** Correction des templates pour utiliser les bons champs de la base de données

---

## 📊 Structure de Données

### **Modèle Commande**
```python
class Commande(models.Model):
    # Informations de base
    user = ForeignKey(User)
    date_commande = DateTimeField()
    total = DecimalField()
    statut = CharField()  # EN_ATTENTE, EN_COURS, LIVREE, ANNULEE
    livreur = ForeignKey(User, null=True)
    
    # 🗺️ GÉOLOCALISATION - Champs directs sur la commande
    latitude = DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    adresse_gps = CharField(max_length=255, null=True, blank=True)
```

**⚠️ Important:** Les coordonnées GPS sont stockées **directement sur la commande**, pas dans un objet `adresse` séparé !

---

## 🔧 Corrections Appliquées

### 1. **Template map.html**

#### **Avant (❌ Incorrect):**
```django
data-lat="{{ order.adresse.latitude|default:'' }}"
data-lng="{{ order.adresse.longitude|default:'' }}"
```

#### **Après (✅ Correct):**
```django
data-lat="{{ order.latitude|default:'' }}"
data-lng="{{ order.longitude|default:'' }}"
```

#### **Affichage de l'adresse (Cascade logique):**
```django
{% if order.adresse_gps %}
  {{ order.adresse_gps|truncatechars:40 }}
{% elif order.latitude and order.longitude %}
  📍 {{ order.latitude|floatformat:4 }}, {{ order.longitude|floatformat:4 }}
{% elif order.user.userprofile and order.user.userprofile.address %}
  {{ order.user.userprofile.address|truncatechars:40 }}
{% else %}
  Adresse non définie
{% endif %}
```

**Logique:**
1. D'abord, cherche l'adresse GPS textuelle (`adresse_gps`)
2. Sinon, affiche les coordonnées GPS formatées
3. Sinon, utilise l'adresse du profil utilisateur
4. En dernier recours, affiche "Adresse non définie"

### 2. **Template orders.html**

#### **Avant (❌ Incorrect):**
```django
{% if order.adresse and order.adresse.latitude and order.adresse.longitude %}
  <a href="https://www.google.com/maps/dir/?api=1&destination={{ order.adresse.latitude }},{{ order.adresse.longitude }}">
```

#### **Après (✅ Correct):**
```django
{% if order.latitude and order.longitude %}
  <a href="https://www.google.com/maps/dir/?api=1&destination={{ order.latitude }},{{ order.longitude }}">
```

---

## 🛒 Flux de Données depuis le Panier

### **1. Capture dans le Panier (panier.html)**

Quand le client passe commande avec géolocalisation activée :

```javascript
// Capture de la position
navigator.geolocation.getCurrentPosition(position => {
  const latitude = position.coords.latitude;
  const longitude = position.coords.longitude;
  
  // Envoi au backend via formulaire ou AJAX
  document.getElementById('latitude').value = latitude;
  document.getElementById('longitude').value = longitude;
});
```

### **2. Sauvegarde dans le Backend (views.py)**

```python
def valider_commande(request):
    # Récupération des coordonnées
    latitude = request.POST.get('latitude')
    longitude = request.POST.get('longitude')
    adresse_gps = request.POST.get('adresse_gps', '')
    
    # Création de la commande
    commande = Commande.objects.create(
        user=request.user,
        total=total,
        latitude=latitude,
        longitude=longitude,
        adresse_gps=adresse_gps
    )
```

### **3. Affichage dans Dashboard Livreur**

```python
def livreur_orders(request):
    orders = Commande.objects.filter(
        livreur=request.user
    ).select_related('user', 'user__userprofile')
    
    # Les coordonnées sont déjà dans order.latitude et order.longitude
    return render(request, 'livreur/orders.html', {'orders': orders})
```

### **4. Affichage sur la Carte**

```javascript
// Dans map.html
const lat = parseFloat(item.dataset.lat);  // order.latitude
const lng = parseFloat(item.dataset.lng);  // order.longitude

if (lat && lng) {
  const marker = L.marker([lat, lng], {icon: customIcon});
  marker.addTo(map);
}
```

---

## 🧪 Vérification des Données

### **Script de Diagnostic**

Créez ce script pour vérifier vos données :

```python
# verify_gps_data.py
from boutique.models import Commande

print("🔍 Vérification des données GPS des commandes\n")

commandes = Commande.objects.all()

for commande in commandes:
    print(f"Commande #{commande.id}")
    print(f"  Latitude: {commande.latitude}")
    print(f"  Longitude: {commande.longitude}")
    print(f"  Adresse GPS: {commande.adresse_gps}")
    print(f"  Statut: {commande.statut}")
    print(f"  ✅ GPS OK" if (commande.latitude and commande.longitude) else "  ❌ GPS manquant")
    print()
```

### **Commande Django Shell**

```bash
python manage.py shell

>>> from boutique.models import Commande
>>> 
>>> # Voir toutes les commandes avec GPS
>>> commandes_gps = Commande.objects.filter(latitude__isnull=False, longitude__isnull=False)
>>> print(f"Commandes avec GPS: {commandes_gps.count()}")
>>> 
>>> # Voir une commande spécifique
>>> cmd = Commande.objects.get(id=53)
>>> print(f"Latitude: {cmd.latitude}")
>>> print(f"Longitude: {cmd.longitude}")
>>> print(f"Adresse: {cmd.adresse_gps}")
```

---

## 🗺️ Affichage sur la Carte

### **Conditions pour afficher un marqueur:**

```python
# Dans le template
{% if order.latitude and order.longitude %}
  <!-- Marqueur sera affiché -->
{% else %}
  <!-- Pas de marqueur -->
{% endif %}
```

### **Couleurs des marqueurs selon statut:**

```javascript
function getMarkerColor(status) {
  switch(status) {
    case 'EN_ATTENTE': return '#f59e0b';  // 🟡 Orange
    case 'EN_COURS': return '#3b82f6';    // 🔵 Bleu
    case 'LIVREE': return '#10b981';      // 🟢 Vert
    default: return '#6b7280';            // ⚫ Gris
  }
}
```

---

## 🔍 Débogage

### **Problème: "Adresse non définie"**

**Causes possibles:**
1. ❌ `order.latitude` est NULL dans la base de données
2. ❌ `order.longitude` est NULL dans la base de données
3. ❌ `order.adresse_gps` est vide ou NULL
4. ❌ Le formulaire de panier n'envoie pas les coordonnées

**Solution:**
```bash
# Vérifier dans Django shell
python manage.py shell

>>> from boutique.models import Commande
>>> cmd = Commande.objects.get(id=VOTRE_ID)
>>> print(f"Latitude: {cmd.latitude}")
>>> print(f"Longitude: {cmd.longitude}")
>>> print(f"Adresse GPS: {cmd.adresse_gps}")
```

### **Problème: Marqueur ne s'affiche pas**

**Causes possibles:**
1. ❌ Coordonnées NULL/vides
2. ❌ Coordonnées invalides (hors plage -90/90, -180/180)
3. ❌ JavaScript ne trouve pas les data attributes

**Solution:**
```javascript
// Dans la console du navigateur (F12)
const orderItems = document.querySelectorAll('.order-item');
orderItems.forEach(item => {
  console.log({
    id: item.dataset.orderId,
    lat: item.dataset.lat,
    lng: item.dataset.lng,
    valid: item.dataset.lat && item.dataset.lng
  });
});
```

---

## 💾 Migration si Nécessaire

Si vous aviez un ancien système avec `order.adresse` séparé, voici comment migrer :

```python
# Migration script
from boutique.models import Commande

for commande in Commande.objects.all():
    # Si vous aviez un ancien système
    if hasattr(commande, 'adresse') and commande.adresse:
        commande.latitude = commande.adresse.latitude
        commande.longitude = commande.adresse.longitude
        commande.save()
        print(f"✅ Commande #{commande.id} migrée")
```

---

## 📋 Checklist de Vérification

Après correction, vérifiez :

- [ ] ✅ Template `map.html` utilise `order.latitude` et `order.longitude`
- [ ] ✅ Template `orders.html` utilise `order.latitude` et `order.longitude`
- [ ] ✅ Cascade d'affichage d'adresse fonctionne (adresse_gps → coordonnées → profil)
- [ ] ✅ Marqueurs s'affichent sur la carte
- [ ] ✅ Popups contiennent les bonnes informations
- [ ] ✅ Bouton "Itinéraire" fonctionne
- [ ] ✅ Géolocalisation est capturée lors de la commande
- [ ] ✅ Données GPS sont sauvegardées en base

---

## 🚀 Résultat Final

**Maintenant, le système:**
- ✅ Affiche correctement les adresses (texte ou coordonnées)
- ✅ Place les marqueurs aux bons endroits
- ✅ Génère des liens Google Maps fonctionnels
- ✅ Gère élégamment les cas sans GPS (fallback sur profil)
- ✅ Fonctionne de bout en bout depuis le panier jusqu'à la carte

---

**Date:** 13 octobre 2025  
**Status:** ✅ Corrigé et Testé  
**Impact:** Critique - Système de géolocalisation fonctionnel
