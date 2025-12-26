# 🚀 QUICK REFERENCE - E-Commerce

## 📋 Commandes Rapides

### Démarrer le serveur
```bash
cd /home/ahmadmbow/e-commerce/ecommerce
python3 manage.py runserver
```

### Tester l'admin panel
```bash
./test_admin_panel.sh
```

## 🔗 URLs Essentielles

```
LIVREUR:
  Dashboard:  http://127.0.0.1:8000/boutique/livreur/dashboard/
  Commandes:  http://127.0.0.1:8000/boutique/livreur/orders/
  Détail:     http://127.0.0.1:8000/boutique/livreur/order/<id>/?type=user|guest

ADMIN:
  Commandes:  http://127.0.0.1:8000/boutique/admin-panel/orders/
  Détail:     http://127.0.0.1:8000/boutique/admin-panel/orders/<id>/?type=user|guest
```

## 📊 Données Actuelles

```
Commandes utilisateurs: 69 (CMD-1 à CMD-69)
Commandes invités:       3 (INV-1 à INV-3)
Total:                  72
```

## 🎯 Numéros de Commande

| Type | Modèle | Numéro | Property |
|------|--------|--------|----------|
| Utilisateur | Commande | CMD-{id} | type_commande = "user" |
| Invité | CommandeInvite | INV-{id} | type_commande = "guest" |

## 💰 Frais de Livraison

```python
FRAIS_LIVRAISON = 2000  # FCFA - FIXE
```

## 🛠️ Fonctions Clés (boutique/views.py)

```python
# Ligne 158
_livreur_orders_queryset()  # Retourne list[Commande + CommandeInvite]

# Ligne 179
_livreur_stats(orders)      # Calcule stats sur liste

# Ligne 1305
livreur_orders()            # Liste + filtres + recherche

# Ligne 1370
livreur_order_detail()      # Détails avec type detection

# Ligne 1875
admin_orders_list()         # Admin: liste combinée

# Ligne 1925
admin_order_detail()        # Admin: détails avec type
```

## 📱 Template Tags Utiles

```django
{{ order.numero_commande }}    <!-- CMD-X ou INV-X -->
{{ order.type_commande }}      <!-- user ou guest -->

{% if order.type_commande == 'user' %}
  {{ order.user.username }}
{% else %}
  {{ order.prenom }} {{ order.nom }}
{% endif %}

<a href="tel:{{ order.telephone }}">Appeler</a>
<a href="mailto:{{ order.email }}">Email</a>
```

## 🎨 Classes CSS

```css
.status-en_attente    /* Jaune/Orange */
.status-en_cours      /* Bleu */
.status-livree        /* Vert */
.status-annulee       /* Rouge */
```

## 🔍 Filtrage/Recherche

### Livreur
```python
# Par statut
?status=EN_ATTENTE|EN_COURS|LIVREE|ANNULEE

# Par recherche
?q=nom_client
```

### Admin
```python
# Pareil + recherche sur email
?q=email@example.com
```

## ⚡ Responsive Breakpoints

```css
/* Mobile: 0-639px */
.stats-banner { grid: 1 column; }

/* Tablet: 640-1023px */
.stats-banner { grid: 2 columns; }

/* Desktop: 1024px+ */
.stats-banner { grid: 4 columns; }
```

## 🧪 Tests Python Shell

```bash
python3 manage.py shell
```

```python
from boutique.models import Commande, CommandeInvite

# Compter
Commande.objects.count()        # 69
CommandeInvite.objects.count()  # 3

# Tester propriétés
c = Commande.objects.first()
c.numero_commande  # "CMD-1"
c.type_commande    # "user"

ci = CommandeInvite.objects.first()
ci.numero_commande  # "INV-1"
ci.type_commande    # "guest"
```

## 🐛 Debug

### Menu ne s'ouvre pas
- Vérifier: `iconEl.className` (pas innerHTML)
- Vérifier: `{ passive: false }` dans addEventListener

### Commandes manquantes
- Vérifier: `_livreur_orders_queryset()` utilisé
- Vérifier: `chain()` importe de `itertools`

### Détails commande erreur
- Vérifier: paramètre `?type=user` ou `?type=guest` dans URL

### GPS encore visible
- Templates: Rechercher "latitude", "longitude", "map", "GPS"
- CSS: Rechercher ".gps", ".map"
- JS: Rechercher "Leaflet", "L.map"

## 📄 Documentation Complète

- `ADMIN_PANEL_FINAL.md` - Panel admin détaillé
- `PROJET_FINAL_COMPLET.md` - Vue d'ensemble complète
- `test_admin_panel.sh` - Script de tests

## 🎯 Statuts Commande

```python
STATUTS = [
    ('EN_ATTENTE', 'En attente'),
    ('EN_COURS', 'En cours de livraison'),
    ('LIVREE', 'Livrée'),
    ('ANNULEE', 'Annulée'),
]
```

## 📞 Contacts dans Templates

```html
<!-- Téléphone -->
{% if order.telephone %}
  <a href="tel:{{ order.telephone }}" class="phone-link">
    <i class="bi bi-phone"></i> {{ order.telephone }}
  </a>
{% endif %}

<!-- Email -->
{% if is_guest_order %}
  <a href="mailto:{{ order.email }}">{{ order.email }}</a>
{% else %}
  <a href="mailto:{{ order.user.email }}">{{ order.user.email }}</a>
{% endif %}
```

## 🔐 Permissions

```python
@login_required
@user_passes_test(lambda u: u.userprofile.role == 'LIVREUR')
def livreur_view():
    ...

@staff_required  # is_staff=True
def admin_view():
    ...
```

## ⚙️ Settings Importants

```python
# settings.py
FRAIS_LIVRAISON = 2000
```

## 🎨 Bootstrap Icons Utilisés

```html
<i class="bi bi-receipt"></i>        <!-- Commande -->
<i class="bi bi-person"></i>         <!-- Client -->
<i class="bi bi-phone"></i>          <!-- Téléphone -->
<i class="bi bi-envelope"></i>       <!-- Email -->
<i class="bi bi-geo-alt"></i>        <!-- Adresse -->
<i class="bi bi-cash"></i>           <!-- Paiement -->
<i class="bi bi-check-circle"></i>   <!-- Succès -->
<i class="bi bi-x-circle"></i>       <!-- Annuler -->
<i class="bi bi-eye"></i>            <!-- Voir -->
```

## 🚀 Production Checklist

- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS configuré
- [ ] Base de données production
- [ ] Static files collectés
- [ ] Sauvegardes automatiques
- [ ] HTTPS activé
- [ ] Email SMTP configuré
- [ ] Logs configurés

---

**🎉 Projet e-commerce complet et opérationnel !**
