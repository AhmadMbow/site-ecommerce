# 📍 Analyse : Géolocalisation du panier

## 🎯 Réponse courte

**OUI**, le panier récupère la position du client, mais avec **deux méthodes de repli** :

1. **Priorité 1** : Coordonnées GPS enregistrées dans l'adresse par défaut
2. **Repli** : Géolocalisation en temps réel via le navigateur (lors de la confirmation)

---

## 🔍 Analyse détaillée du flux

### 1. Chargement de la page panier

**Fichier** : `boutique/views.py` - fonction `voir_panier()` (ligne 652-686)

```python
@login_required
def voir_panier(request):
    # ... récupération des items ...
    
    # Récupérer l'adresse par défaut avec GPS
    adresse_defaut = Adresse.objects.filter(user=request.user, is_default=True).first()
    latitude = adresse_defaut.latitude if adresse_defaut else None
    longitude = adresse_defaut.longitude if adresse_defaut else None

    context = {
        'items': items,
        'total': total,
        'shipping': shipping,
        'adresse_latitude': latitude,      # ← Coordonnées GPS
        'adresse_longitude': longitude,     # ← Coordonnées GPS
    }
    return render(request, 'boutique/panier.html', context)
```

**Ce qui se passe** :
- ✅ La vue cherche l'adresse par défaut du client (`is_default=True`)
- ✅ Si l'adresse existe et a des coordonnées GPS → les envoie au template
- ⚠️ Si pas d'adresse ou pas de coordonnées → envoie `None`

---

### 2. Affichage dans le template

**Fichier** : `templates/boutique/panier.html` (ligne 285-286)

```html
<script type="application/json" id="lat_json">{{ adresse_latitude|default:'null'|json_script }}</script>
<script type="application/json" id="lng_json">{{ adresse_longitude|default:'null'|json_script }}</script>
```

**Ce qui se passe** :
- ✅ Les coordonnées sont injectées dans des balises `<script>` JSON
- ✅ Si pas de coordonnées → `null` en JSON
- ✅ Le JavaScript peut ensuite les lire

---

### 3. Calcul automatique du shipping (JavaScript)

**Fichier** : `templates/boutique/panier.html` (ligne 471-485)

```javascript
try {
  const latValue = JSON.parse(document.getElementById('lat_json').textContent);
  const lngValue = JSON.parse(document.getElementById('lng_json').textContent);
  
  if (typeof latValue === 'number' && typeof lngValue === 'number') {
    setLocation(latValue, lngValue);  // ← Calcule le shipping automatiquement
  }
} catch(_) {}
```

**Ce qui se passe** :
- ✅ Si coordonnées GPS disponibles → calcul automatique du shipping
- ✅ Appel AJAX vers `{% url 'calculer_shipping' %}`
- ✅ Mise à jour de l'affichage des frais de livraison

---

### 4. Géolocalisation de repli (confirmation)

**Fichier** : `templates/boutique/panier.html` (ligne 487-498)

```javascript
confirmBtn.addEventListener('click', function() {
  if (shippingReady) {
    orderForm.submit();  // ← Coordonnées déjà prêtes
  } else if (navigator.geolocation) {
    // ← Demande la position en temps réel
    navigator.geolocation.getCurrentPosition(function(pos) {
      setLocation(pos.coords.latitude, pos.coords.longitude);
      setTimeout(() => orderForm.submit(), 500);
    });
  }
});
```

**Ce qui se passe** :
- ✅ Si shipping déjà calculé → soumission directe
- ⚠️ Si pas de coordonnées → demande au navigateur
- ⚠️ L'utilisateur doit autoriser l'accès à la position

---

## 📊 Modèle de données

### Modèle `Adresse` (boutique/models.py)

```python
class Adresse(models.Model):
    user = models.ForeignKey(...)
    ligne1 = models.CharField(max_length=255)
    ville = models.CharField(max_length=120)
    # ...
    is_default = models.BooleanField(default=False)
    
    # 🌍 Coordonnées GPS
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True, 
        help_text="Latitude GPS du client"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True, 
        help_text="Longitude GPS du client"
    )
```

**Caractéristiques** :
- ✅ Champs GPS présents dans le modèle
- ✅ Nullable (`null=True`) → pas obligatoire
- ✅ Précision : 6 décimales (±10 cm)
- ⚠️ Peuvent être vides si jamais renseignés

---

## 🔄 Scénarios possibles

### Scénario A : Client avec adresse GPS ✅

```
1. Client a une adresse par défaut avec lat/lng renseignés
2. Chargement du panier
   → Vue récupère les coordonnées de l'adresse
   → JavaScript calcule automatiquement le shipping
3. Confirmation
   → Shipping déjà calculé
   → Soumission directe du formulaire
```

**Expérience** : Transparente, shipping calculé dès le chargement

---

### Scénario B : Client SANS adresse GPS ⚠️

```
1. Client a une adresse mais SANS lat/lng
2. Chargement du panier
   → Vue envoie latitude=None, longitude=None
   → Shipping affiché comme "—" (non calculé)
3. Clic sur "Confirmer"
   → Navigateur demande permission géolocalisation
   → Si autorisé : calcul du shipping puis soumission
   → Si refusé : ❌ Problème potentiel
```

**Expérience** : Popup de permission, délai supplémentaire

---

### Scénario C : Client sans adresse du tout ❌

```
1. Client n'a aucune adresse enregistrée
2. Chargement du panier
   → adresse_defaut = None
   → latitude = None, longitude = None
3. Clic sur "Confirmer"
   → Même comportement que scénario B
```

---

## ⚠️ Points d'attention identifiés

### 1. Adresse sans coordonnées GPS

**Problème** : Si un client a une adresse mais sans lat/lng :
- Shipping non calculé au chargement
- Dépend de la géolocalisation navigateur
- Permission peut être refusée

**Solution recommandée** :
```python
# Dans la vue ou lors de la création d'adresse
# Géocoder automatiquement l'adresse texte → lat/lng
# Exemple : utiliser l'API de géocodage (Google Maps, Nominatim, etc.)
```

---

### 2. Permission géolocalisation refusée

**Problème** : Si l'utilisateur refuse :
- `navigator.geolocation.getCurrentPosition()` échoue
- Pas de coordonnées → pas de shipping
- Commande pourrait être validée sans shipping

**Solution actuelle** : ❌ Pas de gestion d'erreur visible

**Amélioration recommandée** :
```javascript
navigator.geolocation.getCurrentPosition(
  function success(pos) {
    setLocation(pos.coords.latitude, pos.coords.longitude);
    setTimeout(() => orderForm.submit(), 500);
  },
  function error(err) {
    // ← AJOUTER gestion d'erreur
    alert('Veuillez activer la géolocalisation ou ajouter une adresse avec coordonnées GPS');
  }
);
```

---

### 3. Calcul du shipping

**Fichier** : `boutique/views.py` (ligne 669)

```python
distance_km = request.session.get('distance_km', 10)  # ← Valeur par défaut : 10 km
shipping = calcul_livraison(distance_km)
```

**Problème** : Distance par défaut arbitraire (10 km)

**Solution** : La fonction `calculer_shipping` (AJAX) devrait calculer la vraie distance

---

## 🧪 Tests à effectuer

### Test 1 : Client avec adresse GPS complète

```
1. Créer/modifier une adresse dans Django Admin
2. Renseigner latitude et longitude (ex: 14.693425, -17.447938 pour Dakar)
3. Marquer comme adresse par défaut
4. Se connecter et aller sur /panier/
5. ✅ Le shipping devrait être calculé automatiquement
```

### Test 2 : Client sans coordonnées GPS

```
1. Créer une adresse SANS lat/lng
2. Marquer comme adresse par défaut
3. Aller sur /panier/
4. ⚠️ Shipping devrait afficher "—"
5. Cliquer "Confirmer"
6. ⚠️ Popup de permission géolocalisation
7. Autoriser
8. ✅ Shipping calculé puis soumission
```

### Test 3 : Permission refusée

```
1. Adresse sans GPS
2. Cliquer "Confirmer"
3. Refuser la permission
4. ❌ Vérifier ce qui se passe (comportement à améliorer)
```

---

## 📋 URLs et vues impliquées

### Vue principale
```python
# URL: /panier/
path('panier/', views.voir_panier, name='panier'),

# Vue: boutique/views.py:652
@login_required
def voir_panier(request):
    # Récupère adresse GPS si disponible
```

### Calcul shipping AJAX
```python
# URL: /calculer-shipping/ (supposé)
path('calculer-shipping/', views.calculer_shipping, name='calculer_shipping'),

# JavaScript appelle cette URL avec lat/lng
fetch("{% url 'calculer_shipping' %}", {
  method: "POST",
  body: `latitude=${lat}&longitude=${lng}`
})
```

### Confirmation commande
```python
# URL: /confirmer-commande/
path('confirmer-commande/', views.confirmer_commande, name='confirmer_commande'),

# Reçoit les champs cachés :
# - latitude
# - longitude
# - shipping
```

---

## ✅ Recommandations

### 1. Géocoder les adresses automatiquement

Lors de la création/modification d'une adresse :

```python
from geopy.geocoders import Nominatim

def sauvegarder_adresse(adresse):
    if not adresse.latitude or not adresse.longitude:
        # Géocoder automatiquement
        geolocator = Nominatim(user_agent="maryama_shop")
        adresse_complete = f"{adresse.ligne1}, {adresse.ville}, {adresse.pays}"
        location = geolocator.geocode(adresse_complete)
        
        if location:
            adresse.latitude = location.latitude
            adresse.longitude = location.longitude
    
    adresse.save()
```

**Avantages** :
- ✅ Coordonnées automatiques
- ✅ Pas besoin de géolocalisation navigateur
- ✅ Shipping calculé dès le chargement

---

### 2. Améliorer la gestion d'erreur JavaScript

```javascript
confirmBtn.addEventListener('click', function() {
  if (shippingReady) {
    orderForm.submit();
  } else if (navigator.geolocation) {
    const statusDiv = document.getElementById('locationStatus');
    statusDiv.textContent = 'Récupération de votre position...';
    statusDiv.className = 'alert alert-info';
    statusDiv.classList.remove('d-none');
    
    navigator.geolocation.getCurrentPosition(
      function success(pos) {
        setLocation(pos.coords.latitude, pos.coords.longitude);
        statusDiv.textContent = 'Position récupérée !';
        statusDiv.className = 'alert alert-success';
        setTimeout(() => orderForm.submit(), 500);
      },
      function error(err) {
        statusDiv.textContent = 'Impossible de récupérer votre position. Veuillez ajouter une adresse avec coordonnées GPS ou autoriser la géolocalisation.';
        statusDiv.className = 'alert alert-danger';
      }
    );
  } else {
    alert('Votre navigateur ne supporte pas la géolocalisation. Veuillez ajouter une adresse avec coordonnées GPS.');
  }
});
```

---

### 3. Ajouter un formulaire d'adresse dans le panier

Si pas d'adresse GPS disponible, proposer :
- Champ de saisie d'adresse
- Bouton "Détecter ma position"
- Sauvegarde automatique pour prochaine fois

---

## 🎯 Conclusion

### ✅ Ce qui fonctionne

- Récupération des coordonnées GPS depuis l'adresse par défaut
- Calcul automatique du shipping si coordonnées disponibles
- Géolocalisation de repli via le navigateur
- Envoi des coordonnées au serveur lors de la confirmation

### ⚠️ Points à améliorer

- Gérer le cas où l'adresse n'a pas de coordonnées
- Gérer le refus de permission géolocalisation
- Géocoder automatiquement les adresses textuelles
- Afficher des messages d'état clairs à l'utilisateur
- Valider que les coordonnées sont présentes avant soumission

### 📊 État actuel

**Le système fonctionne** ✅ mais dépend de :
1. Adresse par défaut existante avec lat/lng renseignés **OU**
2. Permission géolocalisation accordée par l'utilisateur

**Pour une expérience optimale** : implémenter le géocodage automatique des adresses !
