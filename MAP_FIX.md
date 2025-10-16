# 🗺️ Correction Map.html - Structure des Données

## ❌ Problème Initial

```python
# AVANT (ERREUR)
orders = _livreur_orders_queryset(request.user).select_related('adresse')
orders_with_coords = [
    o for o in orders
    if getattr(o, 'adresse', None) and getattr(o.adresse, 'latitude', None)
]
```

**Erreur**: `FieldError: Invalid field name(s) given in select_related: 'adresse'`

Le modèle `Commande` n'a **pas** de relation `adresse`, les coordonnées GPS sont directement sur le modèle.

---

## ✅ Solution Appliquée

### 1. **Correction de la Vue** (`boutique/views.py`)

```python
# APRÈS (CORRECT)
@login_required
def livreur_map(request):
    """Carte des livraisons"""
    # Récupérer toutes les commandes avec user pour le nom du client
    orders = _livreur_orders_queryset(request.user).select_related('user', 'user__userprofile')

    # Liste des commandes ayant des coordonnées GPS
    orders_with_coords = [
        o for o in orders
        if o.latitude is not None and o.longitude is not None
    ]

    stats = _livreur_stats(orders)
    
    context = {
        'orders': orders,
        'orders_with_coords': orders_with_coords,
        'stats': stats,
        'active_tab': 'map'
    }
    return render(request, 'livreur/map.html', context)
```

### 2. **Correction du Template** (`templates/livreur/map.html`)

```javascript
// AVANT
{
  id: {{ order.id }},
  lat: {{ order.adresse.latitude }},        // ❌ Erreur
  lng: {{ order.adresse.longitude }},       // ❌ Erreur
  client: '{{ order.adresse.nom_complet }}', // ❌ Erreur
  phone: '{{ order.adresse.telephone }}',    // ❌ Erreur
  adresse: '{{ order.adresse.adresse_complete }}' // ❌ Erreur
}

// APRÈS
{
  id: {{ order.id }},
  lat: {{ order.latitude }},                 // ✅ Champ direct
  lng: {{ order.longitude }},                // ✅ Champ direct
  client: '{{ order.user.get_full_name|default:order.user.username }}', // ✅ Via user
  phone: '{{ order.user.userprofile.phone }}', // ✅ Via userprofile
  adresse: '{{ order.adresse_gps }}'         // ✅ Champ direct
}
```

---

## 📊 Structure du Modèle Commande

```python
class Commande(models.Model):
    user = models.ForeignKey(User, ...)           # Client
    livreur = models.ForeignKey(User, ...)        # Livreur
    
    # Coordonnées GPS (champs directs)
    latitude = models.DecimalField(...)           # ✅ Direct
    longitude = models.DecimalField(...)          # ✅ Direct
    adresse_gps = models.CharField(...)           # ✅ Direct
    
    statut = models.CharField(...)
    total = models.DecimalField(...)
    date_commande = models.DateTimeField(...)
```

**Important**: Pas de relation `adresse` ! Les données GPS sont directement sur `Commande`.

---

## 🎯 Résultat

✅ **Page `/livreur/map/` fonctionne**
✅ **Carte interactive avec marqueurs**
✅ **Filtres par statut**
✅ **Géolocalisation**
✅ **Clustering des marqueurs**

---

## 🔍 Vérification

```bash
python3 manage.py check
# System check identified 3 issues (0 silenced)
# ✅ 0 erreurs (seulement warnings allauth)
```

---

## 📝 Champs Disponibles

| Source | Champ | Utilisation |
|--------|-------|-------------|
| `order.latitude` | Decimal | Coordonnée GPS latitude |
| `order.longitude` | Decimal | Coordonnée GPS longitude |
| `order.adresse_gps` | String | Adresse textuelle |
| `order.user.username` | String | Nom d'utilisateur |
| `order.user.get_full_name()` | String | Prénom + Nom |
| `order.user.userprofile.phone` | String | Téléphone |
| `order.statut` | String | EN_ATTENTE/EN_COURS/LIVREE |

---

## ⚠️ À Retenir

1. **Toujours vérifier la structure du modèle** avant d'utiliser `select_related()`
2. **Les coordonnées GPS sont sur Commande**, pas sur une relation externe
3. **Les infos client viennent de `order.user`**, pas de `order.adresse`
4. **Utiliser `userprofile.phone`** pour le téléphone du client

---

Date: 7 octobre 2025
Status: ✅ Résolu
