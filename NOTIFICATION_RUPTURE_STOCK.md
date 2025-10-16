# 🔴 Notification Rupture de Stock

Date : 16 octobre 2025

## 📋 Résumé
Ajout d'une notification dans le dropdown de notifications de l'administrateur pour signaler les produits en rupture de stock (stock = 0).

## ✅ Modifications effectuées

### 1. Context Processor (`boutique/context_processors.py`)

**Ajout du compteur de produits en rupture de stock :**

```python
# Import de Produit
from boutique.models import Commande, MessageSupport, AvisLivreur, AvisProduit, Produit

# Compter les produits en rupture de stock
produits_rupture_stock = Produit.objects.filter(stock=0).count()

# Ajout dans admin_badges
'rupture_stock': produits_rupture_stock,
```

### 2. Dropdown Notifications (`templates/adminpanel/base_admin.html`)

#### Calcul du total des notifications :
```django
{% with total_notif=admin_badges.commandes|add:admin_badges.messages|add:admin_badges.avis|add:admin_badges.clients|add:admin_badges.rupture_stock %}
```

#### Nouvelle entrée dans le dropdown :
```html
{% if admin_badges.rupture_stock > 0 %}
<li>
  <a class="dropdown-item d-flex justify-content-between align-items-center" 
     href="{% url 'admin_products' %}?stock=0">
    <span><i class="fa-solid fa-box-open text-danger me-2"></i> Rupture de stock</span>
    <span class="badge bg-danger">{{ admin_badges.rupture_stock }}</span>
  </a>
</li>
{% endif %}
```

## 🎨 Design

### Icône et couleurs
- **Icône** : 📦 `fa-box-open` (boîte ouverte)
- **Couleur** : Rouge (`text-danger`)
- **Badge** : Badge rouge (`bg-danger`)
- **Position** : Après "Nouveaux messages", avant "Avis produits"

### Apparence dans le dropdown
```
🔔 Notifications (X)
├── 🛒 Nouvelles commandes [2]
├── 📧 Nouveaux messages [3]
├── 📦 Rupture de stock [5] ← NOUVEAU
├── ⭐ Avis produits [1]
├── 🚚 Avis livreurs [2]
└── 👥 Nouveaux clients [4]
```

## 🔗 Navigation

Le lien pointe vers la page des produits avec un filtre de stock :
```
/admin-panel/products/?stock=0
```

Cela affichera uniquement les produits ayant un stock égal à 0.

## 📊 Exemple de fonctionnement

### Scénario 1 : 5 produits en rupture de stock
**Dropdown affiche :**
- 📦 Rupture de stock `[5]` avec badge rouge
- Compteur total : inclut les 5 produits
- Clic → Redirige vers la liste des produits filtrée (stock=0)

### Scénario 2 : Aucun produit en rupture
**Dropdown n'affiche pas** la ligne "Rupture de stock"
- La ligne est masquée grâce à `{% if admin_badges.rupture_stock > 0 %}`

## ⚙️ Logique de comptage

```python
# Compte uniquement les produits avec stock exactement égal à 0
produits_rupture_stock = Produit.objects.filter(stock=0).count()
```

**Note :** Si vous souhaitez également alerter pour les stocks faibles (ex: stock < 5), vous pourriez ajouter :
```python
# Stock faible (optionnel)
produits_stock_faible = Produit.objects.filter(stock__gt=0, stock__lt=5).count()
```

## 🎯 Avantages

1. **Visibilité immédiate** : L'administrateur voit instantanément les produits en rupture
2. **Badge rouge urgent** : La couleur rouge attire l'attention
3. **Accès direct** : Un clic amène directement aux produits concernés
4. **Intégration naturelle** : S'intègre parfaitement dans le système de notifications existant
5. **Performance** : Un seul comptage SQL efficace

## 🔄 Mise à jour en temps réel

Le compteur est recalculé à chaque requête grâce au context processor, donc :
- ✅ Mise à jour automatique quand un produit passe à stock=0
- ✅ Disparaît automatiquement quand le stock est réapprovisionné
- ✅ Aucune action manuelle nécessaire

## 📝 Notes techniques

### Performance
- La requête `Produit.objects.filter(stock=0).count()` est optimisée (COUNT SQL)
- Index recommandé sur le champ `stock` pour de meilleures performances
- Cache possible si le nombre de produits est très élevé

### Évolutions possibles
1. **Stocks faibles** : Ajouter une notification pour stock < 5
2. **Email automatique** : Envoyer un email quand un produit tombe à 0
3. **Historique** : Logger les ruptures de stock pour analyse
4. **Prévisions** : Alerter avant la rupture basé sur le taux de vente

## 🧪 Test

Pour tester la fonctionnalité :

1. **Créer une rupture de stock** :
   ```python
   # Dans le shell Django
   from boutique.models import Produit
   produit = Produit.objects.first()
   produit.stock = 0
   produit.save()
   ```

2. **Vérifier le dropdown** :
   - Se connecter en tant qu'admin
   - Cliquer sur l'icône 🔔 dans le header
   - Vérifier la présence de "📦 Rupture de stock [1]"

3. **Tester le lien** :
   - Cliquer sur la notification
   - Vérifier la redirection vers `/admin-panel/products/?stock=0`
   - Vérifier que seuls les produits avec stock=0 sont affichés

4. **Tester la disparition** :
   ```python
   # Réapprovisionner
   produit.stock = 10
   produit.save()
   ```
   - Rafraîchir la page
   - Vérifier que la notification a disparu

## ✨ Résultat final

L'administrateur dispose maintenant d'une alerte visuelle claire et immédiate pour les produits en rupture de stock, lui permettant de réagir rapidement pour réapprovisionner et éviter les pertes de ventes ! 🎯
