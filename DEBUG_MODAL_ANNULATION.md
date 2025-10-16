# 🐛 DEBUG - Modal d'Annulation de Commande

## ✅ Modifications Appliquées

### 1. **Fonction JavaScript Améliorée**
```javascript
function confirmCancelOrder(orderId, clientName) {
  console.log('confirmCancelOrder appelée avec:', orderId, clientName);
  
  // Vérifications et fallback si Bootstrap n'est pas disponible
  // Affichage manuel du modal en cas de problème
}
```

### 2. **Gestionnaire de Fermeture du Modal**
Ajouté pour fermer manuellement le modal si Bootstrap ne fonctionne pas correctement.

## 🔍 Comment Déboguer

### Dans le Navigateur (F12 - Console) :

1. **Ouvrir la console** (F12 ou Ctrl+Shift+I)

2. **Cliquer sur le bouton "Annuler"** d'une commande

3. **Vérifier les messages** :
   ```
   ✅ Devrait afficher: "confirmCancelOrder appelée avec: 48 madou"
   ❌ Si erreur: "Bootstrap Modal non disponible"
   ❌ Si erreur: "Modal element not found"
   ```

4. **Vérifier si Bootstrap est chargé** :
   ```javascript
   // Dans la console, tapez:
   typeof bootstrap
   // Devrait retourner: "object"
   
   typeof bootstrap.Modal
   // Devrait retourner: "function"
   ```

## 🛠️ Solutions aux Problèmes Courants

### Problème 1: Bootstrap n'est pas défini
**Solution** : Le fallback manuel s'active automatiquement
```javascript
// Le modal s'affiche manuellement avec:
modalElement.classList.add('show');
modalElement.style.display = 'block';
```

### Problème 2: Le modal ne se ferme pas
**Solution** : Utiliser le bouton avec l'icône X ou cliquer sur "Non, garder"

### Problème 3: L'URL du formulaire est incorrecte
**Vérifier** : L'action devrait être `/boutique/admin-panel/orders/<id>/cancel/`

## 🔧 Vérifications à Faire

### 1. Vérifier que le Modal existe dans le HTML
```javascript
// Dans la console:
document.getElementById('cancelOrderModal')
// Devrait retourner: <div class="modal fade" ...>
```

### 2. Vérifier les IDs des éléments
```javascript
document.getElementById('modalOrderId')  // ✅ Doit exister
document.getElementById('modalOrderClient')  // ✅ Doit exister
document.getElementById('cancelOrderForm')  // ✅ Doit exister
```

### 3. Vérifier les URLs dans urls.py
```python
# Devrait avoir:
path('admin-panel/orders/<int:pk>/cancel/', views.admin_cancel_order, name='admin_cancel_order')
```

### 4. Vérifier la vue dans views.py
```python
@staff_required
def admin_cancel_order(request, pk):
    order = get_object_or_404(Commande, pk=pk)
    # ... reste du code
```

## 📋 Checklist de Dépannage

- [ ] Le serveur Django est en cours d'exécution
- [ ] Aucune erreur 404 dans la console du navigateur
- [ ] Bootstrap 5 est bien chargé (vérifier dans Network)
- [ ] Le bouton "Annuler" a bien l'attribut `onclick="confirmCancelOrder(...)"`
- [ ] Le modal avec id="cancelOrderModal" existe dans le DOM
- [ ] Les éléments modalOrderId et modalOrderClient existent
- [ ] Le formulaire cancelOrderForm existe

## 🎯 Test Rapide

### Étape 1: Tester l'Ouverture du Modal Manuellement
```javascript
// Dans la console du navigateur:
confirmCancelOrder(48, 'Test Client');
```

### Étape 2: Tester le Modal avec Bootstrap Directement
```javascript
// Dans la console:
const modal = new bootstrap.Modal(document.getElementById('cancelOrderModal'));
modal.show();
```

### Étape 3: Vérifier le Formulaire
```javascript
// Dans la console:
const form = document.getElementById('cancelOrderForm');
console.log('Action du formulaire:', form.action);
```

## 🚀 Si Tout Échoue

### Solution Ultime: Recharger la Page
1. Vider le cache du navigateur (Ctrl+F5)
2. Redémarrer le serveur Django
3. Réessayer

### Alternative: Utiliser un Lien Direct
Si le modal ne fonctionne toujours pas, on peut remplacer le bouton par un lien avec confirmation JavaScript :
```html
<a href="{% url 'admin_cancel_order' o.id %}" 
   onclick="return confirm('Voulez-vous vraiment annuler cette commande ?')"
   class="btn-action-small btn-cancel">
  <i class="bi bi-x-circle"></i>
  Annuler
</a>
```

## 📝 Messages d'Erreur Possibles

| Erreur | Cause | Solution |
|--------|-------|----------|
| `bootstrap is not defined` | Bootstrap JS non chargé | Vérifier base_admin.html |
| `Modal element not found` | ID incorrect | Vérifier l'HTML du modal |
| `TypeError: Cannot read property` | Élément null | Vérifier les IDs dans le modal |
| `CSRF token missing` | Pas de {% csrf_token %} | Ajouter dans le formulaire |

## 🎨 Structure Attendue du Modal

```html
<div class="modal fade" id="cancelOrderModal" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">...</div>
      <div class="modal-body">
        <span id="modalOrderId">#0</span>
        <span id="modalOrderClient">-</span>
      </div>
      <div class="modal-footer">
        <form id="cancelOrderForm" method="post">
          {% csrf_token %}
          ...
        </form>
      </div>
    </div>
  </div>
</div>
```

## 📞 Pour Plus d'Aide

1. Ouvrir la console du navigateur (F12)
2. Cliquer sur "Annuler"
3. Copier tous les messages de la console
4. Vérifier les erreurs en rouge

---

**Date**: 14 octobre 2025
**Statut**: 🔍 En débogage
