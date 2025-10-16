# 📦 Système de Gestion Automatique du Stock

## 🎯 Objectif
Gérer automatiquement le stock des produits lors des différentes étapes du cycle de vie d'une commande.

---

## ✅ Fonctionnalités Implémentées

### 1️⃣ **Signal de Décrémentation du Stock** (`boutique/signals.py`)

#### **Quand le stock baisse-t-il ?**
Le stock d'un produit est **automatiquement décrémenté** lorsqu'une commande passe au statut **`LIVREE`**.

```python
@receiver(pre_save, sender=Commande)
def gerer_stock_commande(sender, instance, **kwargs):
    # Décrémente le stock quand statut change vers LIVREE
    if ancien_statut != 'LIVREE' and nouveau_statut == 'LIVREE':
        for item in commande.items:
            produit.stock -= item.quantite
            produit.save()
```

#### **Fonctionnalités du Signal :**

##### ✅ **Décrémentation Automatique**
- Surveille le changement de statut de la commande
- Quand `statut` passe à `LIVREE`, décrémente le stock de chaque produit
- Utilise une transaction atomique pour garantir la cohérence

##### 🔄 **Restitution du Stock**
- Si une commande `LIVREE` est annulée (`ANNULEE`), le stock est **restitué**
- Permet de gérer les retours ou annulations après livraison

##### ⚠️ **Alertes Automatiques**
- Alerte si un produit tombe à 0 : **"Rupture de stock"**
- Alerte si stock < 5 : **"Stock faible"**
- Messages dans la console pour monitoring

##### 🛡️ **Protection contre Stock Négatif**
- Si le stock est insuffisant, il est ramené à 0 (pas de stock négatif)
- Log d'avertissement pour investigation

---

### 2️⃣ **Validation lors de l'Ajout au Panier** (`boutique/views.py`)

#### **Fonction : `ajouter_au_panier()`**

##### ✅ **Vérification du Stock Disponible**
```python
if produit.stock <= 0:
    return JsonResponse({
        'success': False,
        'message': 'Produit en rupture de stock'
    }, status=400)
```

##### ✅ **Vérification de la Quantité**
```python
if nouvelle_quantite > produit.stock:
    return JsonResponse({
        'success': False,
        'message': f'Stock insuffisant. Disponible: {produit.stock}'
    }, status=400)
```

##### ✅ **Message Intelligent**
- Si stock restant ≤ 5 après ajout :
  ```
  "Produit ajouté au panier (Plus que X disponibles)"
  ```

##### ✅ **Gestion Session & Base de Données**
- Utilisateurs connectés : vérification via `PanierItem`
- Utilisateurs anonymes : vérification via `request.session['panier']`

---

### 3️⃣ **Validation lors de la Confirmation de Commande**

#### **Fonction : `confirmer_commande()`**

##### ✅ **Vérification Pré-Commande**
Avant de créer la commande, vérifie le stock de **tous** les produits du panier :

```python
for item in panier:
    if produit.stock < quantite_demandee:
        produits_insuffisants.append(...)
```

##### ✅ **Messages d'Erreur Détaillés**
```
Stock insuffisant pour les produits suivants :
• T-shirt Rouge: demandé 5, disponible 3
• Casquette Bleue: en rupture de stock
```

##### ✅ **Redirection vers Panier**
- Si stock insuffisant, l'utilisateur est redirigé vers le panier
- Peut ajuster les quantités avant de réessayer

##### ✅ **Transaction Atomique**
```python
with transaction.atomic():
    # Créer commande
    # Créer items
    # Vider panier
```
Garantit que tout se passe ou rien ne se passe (cohérence des données).

---

## 🔄 Cycle de Vie du Stock

### **Étape 1 : Ajout au Panier**
```
Client clique "Ajouter au panier"
    ↓
Vérification : stock >= 1 ?
    ↓ OUI
Ajout au panier (PanierItem ou session)
Message : "Produit ajouté (Plus que X disponibles)"
    ↓ NON
Erreur : "Rupture de stock"
```

### **Étape 2 : Validation Panier**
```
Client clique "Confirmer la commande"
    ↓
Pour chaque produit du panier :
    Vérification : stock >= quantité_panier ?
    ↓ OUI
Création de la commande (statut: EN_ATTENTE)
    ↓ NON
Erreur + redirection vers panier
```

### **Étape 3 : Traitement Commande**
```
Admin change statut → EN_COURS
    → Pas de changement de stock

Admin change statut → LIVREE
    ↓
SIGNAL DÉCLENCHÉ
    ↓
Stock décrémenté automatiquement
Pour chaque produit :
    produit.stock -= quantite
    ↓
Alertes si stock faible/rupture
```

### **Étape 4 : Annulation (optionnel)**
```
Commande LIVREE → Admin change → ANNULEE
    ↓
SIGNAL DÉCLENCHÉ
    ↓
Stock restitué automatiquement
Pour chaque produit :
    produit.stock += quantite
```

---

## 📊 Statuts de Stock

| Stock | Badge | Couleur | Bouton Panier | Message |
|-------|-------|---------|---------------|---------|
| stock = 0 | "Rupture de stock" | 🔴 Rouge | Désactivé | "Indisponible" |
| stock < 5 | "Stock limité (X)" | 🟠 Orange | Actif | "Plus que X disponibles" |
| stock ≥ 5 | "En stock (X)" | 🟢 Vert | Actif | Normal |

---

## 🛡️ Sécurités Implémentées

### ✅ **Protection contre Survente**
- Vérification à l'ajout au panier
- Vérification à la confirmation de commande
- Impossible d'acheter plus que le stock disponible

### ✅ **Cohérence des Données**
- Transactions atomiques (tout ou rien)
- Signaux Django pour automatisation
- Pas de stock négatif

### ✅ **Traçabilité**
- Logs console pour chaque décrémentation
- Messages d'alerte pour stock faible
- Messages d'erreur détaillés pour l'utilisateur

### ✅ **Gestion des Cas Limites**
- Stock insuffisant au moment de l'ajout au panier
- Stock insuffisant au moment de la confirmation
- Annulation après livraison (restitution)
- Commandes multiples simultanées (transactions)

---

## 🧪 Scénarios de Test

### **Test 1 : Stock Suffisant**
```
Stock initial: 10
Client ajoute 3 au panier → ✅ OK
Client confirme commande → ✅ OK (statut: EN_ATTENTE)
Admin marque LIVREE → ✅ Stock devient 7
```

### **Test 2 : Stock Insuffisant (Panier)**
```
Stock initial: 2
Client ajoute 1 au panier → ✅ OK
Client ajoute encore 1 → ✅ OK (2 dans le panier)
Client ajoute encore 1 → ❌ Erreur "Stock insuffisant"
```

### **Test 3 : Stock Insuffisant (Confirmation)**
```
Stock initial: 5
Client A ajoute 5 au panier
Client B ajoute 3 au panier (simultané)
Client A confirme → ✅ OK
Client B confirme → ❌ Erreur "Stock insuffisant: demandé 3, disponible 0"
```

### **Test 4 : Annulation et Restitution**
```
Stock initial: 10
Commande de 3 produits livrée → Stock devient 7
Admin annule la commande → Stock restitué à 10
```

### **Test 5 : Rupture de Stock**
```
Stock initial: 1
Commande de 1 produit livrée → Stock devient 0
Client essaie d'ajouter au panier → ❌ Erreur "Rupture de stock"
Bouton "Ajouter" désactivé sur la boutique
```

---

## 📝 Fichiers Modifiés

### 1. **`boutique/models.py`**
- Ajout du champ `stock` au modèle `Produit`

### 2. **`boutique/signals.py`**
- Signal `gerer_stock_commande` : décrémentation/restitution automatique
- Signal `notifier_changement_stock` : alertes

### 3. **`boutique/views.py`**
- `ajouter_au_panier()` : vérification stock à l'ajout
- `confirmer_commande()` : vérification stock avant création commande

### 4. **Templates (boutique.html, produit_detail.html)**
- Affichage des indicateurs de stock
- Désactivation des boutons si rupture

---

## 🚀 Avantages du Système

### ✅ **Automatique**
- Pas d'intervention manuelle nécessaire
- Stock mis à jour lors du changement de statut

### ✅ **Fiable**
- Transactions atomiques
- Pas de stock négatif
- Vérifications multiples

### ✅ **Transparent**
- Messages clairs pour l'utilisateur
- Alertes pour l'administrateur
- Traçabilité complète

### ✅ **Flexible**
- Gère les annulations
- Supporte les restitutions
- Alertes configurables

---

## 🔮 Améliorations Futures Possibles

### 📧 **Notifications Email**
- Email à l'admin quand stock < 5
- Email au client si produit à nouveau disponible

### 📊 **Dashboard Stock**
- Vue d'ensemble des produits en rupture
- Graphiques d'évolution du stock
- Alertes de réapprovisionnement

### 🔔 **Système de Réservation**
- Réserver le stock dès l'ajout au panier (X minutes)
- Libérer si panier abandonné

### 📈 **Analytics**
- Produits les plus vendus
- Prévisions de rupture de stock
- Historique des mouvements de stock

---

## ✅ Résumé

Le système de gestion automatique du stock garantit :
- ✅ Décrémentation automatique à la livraison
- ✅ Restitution automatique en cas d'annulation
- ✅ Vérifications à chaque étape (panier, commande)
- ✅ Messages clairs et informatifs
- ✅ Protection contre la survente
- ✅ Cohérence des données garantie

**Le stock est maintenant géré automatiquement tout au long du cycle de vie de la commande !** 🎉
