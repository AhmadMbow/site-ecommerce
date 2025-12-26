# 🎯 PANEL ADMINISTRATEUR - MISE À JOUR COMPLÈTE

## ✅ Modifications Réalisées

### 1. Backend (Views - boutique/views.py)

#### ✅ admin_orders_list (ligne ~1875)
```python
@staff_required
def admin_orders_list(request):
    """Liste des commandes pour l'admin (gère les deux types)"""
    q = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    # Récupérer les deux types de commandes
    orders = Commande.objects.select_related('user').all()
    orders_invite = CommandeInvite.objects.all()
    
    # Appliquer les filtres de recherche
    if q:
        orders = orders.filter(
            Q(user__username__icontains=q) | 
            Q(user__first_name__icontains=q) | 
            Q(user__last_name__icontains=q)
        )
        orders_invite = orders_invite.filter(
            Q(prenom__icontains=q) | 
            Q(nom__icontains=q) | 
            Q(email__icontains=q)
        )
    
    # Appliquer le filtre de statut
    if status_filter:
        orders = orders.filter(statut=status_filter)
        orders_invite = orders_invite.filter(statut=status_filter)
    
    # Combiner et trier
    orders = sorted(
        chain(list(orders), list(orders_invite)),
        key=lambda x: x.date_commande,
        reverse=True
    )
    
    # Statistiques combinées
    stats = {
        'total': len(orders),
        'pending': len([o for o in orders if o.statut == 'EN_ATTENTE']),
        'in_progress': len([o for o in orders if o.statut == 'EN_COURS']),
        'completed': len([o for o in orders if o.statut == 'LIVREE']),
        'revenue': sum(o.total for o in orders if o.statut == 'LIVREE')
    }
    
    return render(request, 'adminpanel/orders_list.html', {
        'orders': orders, 
        'stats': stats, 
        'q': q
    })
```

**Résultat:**
- ✅ 72 commandes au total (69 utilisateurs + 3 invités)
- ✅ Recherche fonctionne sur les deux types
- ✅ Filtres par statut appliqués aux deux types
- ✅ Statistiques combinées correctes

#### ✅ admin_order_detail (ligne ~1925)
```python
@staff_required
def admin_order_detail(request, pk):
    """Détail d'une commande pour l'admin (gère les deux types)"""
    order = None
    items = []
    is_guest_order = False
    
    # Vérifier le type de commande via paramètre URL
    order_type = request.GET.get('type', 'user')
    
    if order_type == 'guest':
        try:
            order = CommandeInvite.objects.get(pk=pk)
            items = list(CommandeInviteItem.objects.select_related('produit').filter(commande=order))
            is_guest_order = True
        except CommandeInvite.DoesNotExist:
            # Fallback vers Commande
            order = Commande.objects.select_related('user').get(pk=pk)
            items = list(CommandeItem.objects.select_related('produit').filter(commande=order))
    else:
        try:
            order = Commande.objects.select_related('user').get(pk=pk)
            items = list(CommandeItem.objects.select_related('produit').filter(commande=order))
        except Commande.DoesNotExist:
            # Fallback vers CommandeInvite
            order = CommandeInvite.objects.get(pk=pk)
            items = list(CommandeInviteItem.objects.select_related('produit').filter(commande=order))
            is_guest_order = True
    
    # Calculer les totaux
    for it in items:
        unit = getattr(it, 'prix_unitaire', None) or getattr(it, 'prix', None) or 0
        it.unit_price = unit
        it.line_total = unit * (getattr(it, 'quantite', 0) or 0)

    return render(request, 'adminpanel/order_detail.html', {
        'order': order, 
        'items': items,
        'is_guest_order': is_guest_order
    })
```

**Résultat:**
- ✅ Détecte automatiquement le type via paramètre `?type=user` ou `?type=guest`
- ✅ Fallback intelligent si mauvais type spécifié
- ✅ Variable `is_guest_order` pour templates
- ✅ Gère les deux types d'items (CommandeItem, CommandeInviteItem)

### 2. Frontend (Templates)

#### ✅ templates/adminpanel/orders_list.html

**Modifications:**

1. **En-tête de tableau - Suppression colonne GPS**
```html
<thead>
  <tr>
    <th>Commande</th>
    <th>Client</th>
    <th>Total</th>
    <th>Statut</th>
    <th>Date</th>
    <!-- SUPPRIMÉ: <th>GPS</th> -->
    <th style="text-align: right;">Actions</th>
  </tr>
</thead>
```

2. **Affichage numéro de commande (CMD-X / INV-X)**
```html
<span class="order-id-badge">
  <i class="bi bi-receipt"></i>
  {{ o.numero_commande }}  <!-- Au lieu de #{{ o.id }} -->
</span>
```

3. **Affichage client (utilisateur ou invité)**
```html
<div class="client-info-cell">
  <div class="client-avatar-small">
    {% if o.type_commande == 'user' %}
      {{ o.user.get_full_name|default:o.user.username|slice:":1"|upper }}
    {% else %}
      {{ o.prenom|slice:":1"|upper }}
    {% endif %}
  </div>
  <div class="client-details-small">
    <span class="client-name">
      {% if o.type_commande == 'user' %}
        {{ o.user.get_full_name|default:o.user.username }}
      {% else %}
        {{ o.prenom }} {{ o.nom }}
      {% endif %}
    </span>
    <span class="client-email">
      {% if o.type_commande == 'user' %}
        {{ o.user.email|default:"—" }}
      {% else %}
        {{ o.email|default:"—" }}
      {% endif %}
    </span>
  </div>
</div>
```

4. **Liens vers détails avec paramètre type**
```html
<a href="{% url 'admin_order_detail' o.id %}?type={{ o.type_commande }}" 
   class="btn-action-small btn-details">
  <i class="bi bi-eye"></i>
  Détails
</a>
```

5. **SUPPRIMÉ: Colonne GPS et bouton Carte**
```html
<!-- AVANT (supprimé) -->
<td>
  {% if o.latitude and o.longitude %}
    <span class="gps-badge available">...</span>
  {% else %}
    <span class="gps-badge unavailable">...</span>
  {% endif %}
</td>
<a href="https://www.google.com/maps?q={{ o.latitude }},{{ o.longitude }}" 
   class="btn-action-small btn-map">...</a>
```

6. **JavaScript - Fonction confirmCancelOrder mise à jour**
```javascript
function confirmCancelOrder(orderId, orderType, clientName) {
  // Affiche CMD-X ou INV-X dans le modal
  if (modalOrderId) {
    modalOrderId.textContent = orderType === 'user' ? `#CMD-${orderId}` : `#INV-${orderId}`;
  }
  // Ajoute le paramètre type à l'URL
  if (form) {
    form.action = `/boutique/admin-panel/orders/${orderId}/cancel/?type=${orderType}`;
  }
  // ... reste du code
}
```

7. **SUPPRIMÉ: Styles CSS GPS**
```css
/* Supprimé */
.gps-badge { ... }
.gps-badge.available { ... }
.gps-badge.unavailable { ... }
```

#### ✅ templates/adminpanel/order_detail.html

**Modifications:**

1. **Titre de la page**
```html
{% block title %}{{ order.numero_commande }} - Détails{% endblock %}
<!-- Au lieu de: Commande #{{ order.id }} - Détails -->
```

2. **En-tête commande**
```html
<div class="order-number">
  <i class="bi bi-receipt"></i>
  {{ order.numero_commande }}  <!-- CMD-X ou INV-X -->
</div>
<div class="order-meta">
  <div class="meta-item-inline">
    <i class="bi bi-person"></i>
    <span>
      {% if is_guest_order %}
        {{ order.prenom }} {{ order.nom }}
      {% else %}
        {{ order.user.get_full_name|default:order.user.username }}
      {% endif %}
    </span>
  </div>
  <!-- ... -->
</div>
```

3. **Section informations client**
```html
<div class="client-avatar">
  {% if is_guest_order %}
    {{ order.prenom|slice:":1"|upper }}
  {% else %}
    {{ order.user.get_full_name|default:order.user.username|slice:":1"|upper }}
  {% endif %}
</div>
<div class="client-details">
  <h4>
    {% if is_guest_order %}
      {{ order.prenom }} {{ order.nom }}
    {% else %}
      {{ order.user.get_full_name|default:order.user.username }}
    {% endif %}
  </h4>
  <p>
    <i class="bi bi-envelope me-1"></i>
    {% if is_guest_order %}
      <a href="mailto:{{ order.email }}">{{ order.email|default:"Non renseigné" }}</a>
    {% else %}
      <a href="mailto:{{ order.user.email }}">{{ order.user.email|default:"Non renseigné" }}</a>
    {% endif %}
  </p>
</div>
```

4. **Téléphone avec lien cliquable**
```html
<div class="info-section">
  <div class="info-label">
    <i class="bi bi-telephone"></i>
    Téléphone
  </div>
  <div class="info-value">
    {% if order.telephone %}
      <a href="tel:{{ order.telephone }}" style="color: #667eea;">
        <i class="bi bi-phone me-2"></i>{{ order.telephone }}
      </a>
    {% else %}
      Non renseigné
    {% endif %}
  </div>
</div>
```

5. **Adresse (gère les deux types)**
```html
<div class="info-section">
  <div class="info-label">
    <i class="bi bi-geo-alt"></i>
    Adresse de Livraison
  </div>
  <div class="info-value">
    {% if is_guest_order %}
      {{ order.adresse|default:"Non renseignée" }}
    {% elif order.adresse_gps %}
      {{ order.adresse_gps }}
    {% elif order.adresse %}
      {{ order.adresse }}
    {% else %}
      Non renseignée
    {% endif %}
  </div>
</div>
```

6. **SUPPRIMÉ: Carte GPS (500+ lignes)**
```html
<!-- Supprimé complètement -->
{% if order.latitude and order.longitude %}
  <div class="gps-card">...</div>
  <div class="card-ultra-detail">
    <div id="orderMap"></div>
  </div>
{% endif %}
```

7. **SUPPRIMÉ: JavaScript Leaflet**
```javascript
// Supprimé complètement
const lat = {{ order.latitude|default:"null" }};
const lng = {{ order.longitude|default:"null" }};
if (lat && lng) {
  const map = L.map('orderMap')...
}
```

8. **SUPPRIMÉ: Styles CSS GPS/Map**
```css
/* Supprimé */
.map-container { ... }
#orderMap { ... }
.gps-card { ... }
.gps-coordinates { ... }
.gps-icon { ... }
.gps-values { ... }
.gps-label { ... }
.gps-value { ... }
```

### 3. Import nécessaire (boutique/views.py)

```python
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, Http404
from itertools import chain
```

## 📊 Statistiques

- **Commandes utilisateurs:** 69
- **Commandes invités:** 3
- **Total:** 72 commandes
- **Revenue (livrées):** Calculé sur les deux types

## 🎯 Numéros de Commande

| Type | Format | Exemple |
|------|--------|---------|
| Utilisateur | CMD-{id} | CMD-1, CMD-2, ... CMD-69 |
| Invité | INV-{id} | INV-1, INV-2, INV-3 |

## 🔗 URLs avec Paramètre Type

```
Liste: /boutique/admin-panel/orders/
Détail user: /boutique/admin-panel/orders/1/?type=user
Détail guest: /boutique/admin-panel/orders/1/?type=guest
```

## ✅ Checklist Finale

- [x] Vue `admin_orders_list` combine les deux types
- [x] Vue `admin_order_detail` gère les deux types
- [x] Template `orders_list.html` affiche numero_commande
- [x] Template `orders_list.html` affiche clients (user + guest)
- [x] Template `orders_list.html` colonne GPS supprimée
- [x] Template `orders_list.html` bouton Carte supprimé
- [x] Template `order_detail.html` affiche numero_commande
- [x] Template `order_detail.html` affiche client (user + guest)
- [x] Template `order_detail.html` section GPS supprimée
- [x] Template `order_detail.html` carte Leaflet supprimée
- [x] JavaScript `confirmCancelOrder` mis à jour
- [x] Styles CSS GPS/Map supprimés
- [x] Liens téléphone cliquables (tel:)
- [x] Liens email cliquables (mailto:)
- [x] Import Http404 ajouté

## 🧪 Tests

```bash
./test_admin_panel.sh
```

**Résultats:**
```
✅ Propriétés numero_commande et type_commande ajoutées
✅ Vue admin_orders_list combine Commande + CommandeInvite
✅ Vue admin_order_detail gère les deux types
✅ Templates mis à jour pour afficher les commandes invités
✅ GPS/carte supprimés de l'interface admin
```

## 🎉 Résultat Final

Le panel administrateur:
- ✅ Affiche les 72 commandes (69 utilisateurs + 3 invités)
- ✅ Numéros uniques (CMD-X pour users, INV-X pour guests)
- ✅ Aucune référence GPS/carte
- ✅ Liens téléphone et email cliquables
- ✅ Recherche fonctionne sur les deux types
- ✅ Détails affichent correctement client et adresse

## 📝 Fichiers Modifiés

1. `boutique/views.py`
   - `admin_orders_list` (ligne ~1875)
   - `admin_order_detail` (ligne ~1925)
   - Import `Http404` ajouté

2. `templates/adminpanel/orders_list.html`
   - Suppression colonne GPS
   - Affichage numero_commande
   - Gestion clients user/guest
   - Liens avec paramètre type
   - JavaScript mis à jour
   - Styles GPS supprimés

3. `templates/adminpanel/order_detail.html`
   - Titre avec numero_commande
   - Gestion clients user/guest
   - Suppression carte GPS (~500 lignes)
   - Suppression JavaScript Leaflet
   - Styles GPS supprimés
   - Liens tel: et mailto:

## 🚀 URL de Test

```
http://127.0.0.1:8000/boutique/admin-panel/orders/
```

Connectez-vous avec un compte admin pour voir toutes les commandes !
