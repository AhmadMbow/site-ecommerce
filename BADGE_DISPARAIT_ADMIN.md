# 🔔 Système de Notification Admin - Badge Disparaît Après Clic

## 📋 Vue d'ensemble

Système intelligent qui marque automatiquement les notifications comme "vues" lorsque l'administrateur clique dessus, faisant disparaître le badge correspondant.

---

## 🎯 Fonctionnement

### **Avant** :
```
Menu Admin:
  📦 Commandes
  💬 Messages
  👥 Clients [5]  ← Badge orange avec 5 nouveaux clients
  ⭐ Avis
```

### **Après clic sur "Clients"** :
```
Menu Admin:
  📦 Commandes
  💬 Messages
  👥 Clients      ← Badge DISPARU automatiquement
  ⭐ Avis
```

---

## 🏗️ Architecture Technique

### 1. **Modèle `NotificationAdminVue`**

📁 `boutique/models.py`

```python
class NotificationAdminVue(models.Model):
    """Tracker les notifications vues par les administrateurs"""
    
    TYPE_CHOICES = [
        ('NOUVEAU_CLIENT', 'Nouveau Client'),
        ('NOUVELLE_COMMANDE', 'Nouvelle Commande'),
        ('NOUVEAU_MESSAGE', 'Nouveau Message'),
        ('NOUVEL_AVIS', 'Nouvel Avis'),
        ('RUPTURE_STOCK', 'Rupture de Stock'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_vues')
    type_notification = models.CharField(max_length=30, choices=TYPE_CHOICES)
    objet_id = models.IntegerField(help_text="ID de l'objet concerné")
    date_vue = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['admin', 'type_notification', 'objet_id']
```

**Caractéristiques** :
- ✅ Un admin peut voir une notification une seule fois (`unique_together`)
- 📅 Date de visualisation enregistrée automatiquement
- 🔢 Stocke l'ID de l'objet concerné (User, Commande, etc.)
- 👤 Chaque admin a ses propres notifications vues (indépendant des autres)

---

### 2. **Context Processor Modifié**

📁 `boutique/context_processors.py`

**Avant** (affichait tous les nouveaux clients) :
```python
nouveaux_clients = User.objects.filter(
    date_joined__gte=date_limite,
    is_staff=False,
    is_superuser=False
).count()
```

**Après** (exclut les clients déjà vus) :
```python
# Récupérer les IDs des clients déjà vus par cet admin
clients_vus_ids = NotificationAdminVue.objects.filter(
    admin=request.user,
    type_notification='NOUVEAU_CLIENT'
).values_list('objet_id', flat=True)

# Compter SEULEMENT les clients NON VUS
nouveaux_clients = User.objects.filter(
    date_joined__gte=date_limite,
    is_staff=False,
    is_superuser=False
).exclude(id__in=clients_vus_ids).count()  # ← EXCLUSION DES VUS
```

**Résultat** :
- ✅ Badge affiche uniquement les clients NON VUS par cet admin
- ✅ Chaque admin voit ses propres nouveaux clients
- ✅ Le badge disparaît quand l'admin visite la page clients

---

### 3. **Vue `admin_clients_list` Modifiée**

📁 `boutique/views.py`

```python
@admin_required
def admin_clients_list(request):
    """Liste des clients avec marquage automatique des notifications"""
    from boutique.models import NotificationAdminVue
    from datetime import timedelta
    
    clients_list = User.objects.filter(is_staff=False).order_by('-date_joined')
    
    # Date limite pour "nouveau" (dernières 24h)
    date_limite = timezone.now() - timedelta(hours=24)
    
    # Récupérer les nouveaux clients
    nouveaux_clients = clients_list.filter(date_joined__gte=date_limite)
    
    # 🔥 MARQUAGE AUTOMATIQUE AU CHARGEMENT DE LA PAGE
    for client in nouveaux_clients:
        NotificationAdminVue.objects.get_or_create(
            admin=request.user,
            type_notification='NOUVEAU_CLIENT',
            objet_id=client.id
        )
    
    # ... reste du code
```

**Fonctionnement** :
1. ✅ Admin clique sur "Clients"
2. ✅ La vue charge la liste des clients
3. ✅ **AUTOMATIQUEMENT** : Marque tous les nouveaux clients comme vus
4. ✅ Au prochain chargement du menu : Badge = 0 → Disparaît

---

### 4. **API AJAX (optionnel)**

📁 `boutique/views.py`

```python
@login_required
@require_POST
def admin_marquer_notification_vue(request):
    """Marquer une notification comme vue (AJAX)"""
    from boutique.models import NotificationAdminVue
    import json
    
    if not request.user.is_staff:
        return JsonResponse({'success': False}, status=403)
    
    data = json.loads(request.body)
    type_notification = data.get('type')
    objet_id = data.get('id')
    
    notification, created = NotificationAdminVue.objects.get_or_create(
        admin=request.user,
        type_notification=type_notification,
        objet_id=objet_id
    )
    
    return JsonResponse({'success': True, 'created': created})
```

**Utilisation JavaScript** :
```javascript
// Marquer une notification spécifique comme vue
fetch('/api/admin/notification/marquer-vue/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
        type: 'NOUVEAU_CLIENT',
        id: 123  // ID du client
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Notification marquée comme vue');
        // Mettre à jour le badge UI
        updateBadgeCount();
    }
});
```

---

## 🔄 Flux de Données Complet

```
┌─────────────────────────────────────────────┐
│  1. NOUVEAU CLIENT S'INSCRIT                │
│     User.objects.create(...)                │
│     date_joined = 2025-10-16 14:30          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  2. CONTEXT PROCESSOR DÉTECTE               │
│     - Client inscrit < 24h                  │
│     - Pas dans NotificationAdminVue         │
│     → Badge = 1                             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  3. ADMIN VOIT LE BADGE                     │
│     Menu: 👥 Clients [1]                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼ (clic)
┌─────────────────────────────────────────────┐
│  4. VUE admin_clients_list() S'EXÉCUTE      │
│     NotificationAdminVue.objects.create(    │
│         admin=admin_user,                   │
│         type='NOUVEAU_CLIENT',              │
│         objet_id=client.id                  │
│     )                                       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  5. CONTEXT PROCESSOR RECOMPTE              │
│     - Client inscrit < 24h ✓                │
│     - MAIS dans NotificationAdminVue ✓      │
│     → Badge = 0 (client exclu)              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  6. BADGE DISPARAÎT                         │
│     Menu: 👥 Clients                        │
│     (plus de badge)                         │
└─────────────────────────────────────────────┘
```

---

## 🎨 Exemple Concret

### **Scénario 1 : Un nouvel admin**

```python
# État initial
admin1 = User.objects.get(username='admin1')
admin2 = User.objects.get(username='admin2')

# 3 nouveaux clients inscrits aujourd'hui
nouveaux_clients = [client1, client2, client3]

# admin1 se connecte
→ Badge admin1: 👥 Clients [3]

# admin2 se connecte
→ Badge admin2: 👥 Clients [3]

# admin1 clique sur "Clients"
NotificationAdminVue.objects.create(admin=admin1, type='NOUVEAU_CLIENT', objet_id=1)
NotificationAdminVue.objects.create(admin=admin1, type='NOUVEAU_CLIENT', objet_id=2)
NotificationAdminVue.objects.create(admin=admin1, type='NOUVEAU_CLIENT', objet_id=3)

→ Badge admin1: 👥 Clients [0] → Disparaît
→ Badge admin2: 👥 Clients [3] → RESTE (admin2 n'a pas encore vu)
```

---

### **Scénario 2 : Nouveaux clients arrivent**

```python
# État : admin a déjà vu 3 clients
NotificationAdminVue.objects.filter(admin=admin, type='NOUVEAU_CLIENT').count()
# → 3

# 2 nouveaux clients s'inscrivent
client4 = User.objects.create(username='client4')
client5 = User.objects.create(username='client5')

# admin rafraîchit la page
→ Badge: 👥 Clients [2]  # Seulement les 2 nouveaux

# admin clique sur "Clients"
→ Badge: 👥 Clients [0] → Disparaît

# Base de données :
NotificationAdminVue.objects.filter(admin=admin, type='NOUVEAU_CLIENT').count()
# → 5 (3 anciens + 2 nouveaux)
```

---

## 📊 Base de Données

### **Table `boutique_notificationadminvue`**

```sql
id | admin_id | type_notification | objet_id | date_vue
---+----------+------------------+----------+----------------------
1  | 1        | NOUVEAU_CLIENT   | 10       | 2025-10-16 14:30:00
2  | 1        | NOUVEAU_CLIENT   | 11       | 2025-10-16 14:30:00
3  | 1        | NOUVEAU_CLIENT   | 12       | 2025-10-16 14:30:00
4  | 2        | NOUVEAU_CLIENT   | 10       | 2025-10-16 15:00:00
5  | 1        | NOUVEAU_MESSAGE  | 5        | 2025-10-16 16:00:00
```

**Requête pour compter les clients non vus** :
```sql
-- Clients inscrits dans les dernières 24h
SELECT id FROM auth_user 
WHERE date_joined >= NOW() - INTERVAL 24 HOUR
AND is_staff = 0

-- SAUF ceux déjà vus par admin_id=1
EXCEPT

SELECT objet_id FROM boutique_notificationadminvue
WHERE admin_id = 1 
AND type_notification = 'NOUVEAU_CLIENT'
```

---

## ⚙️ Configuration

### **Modifier la durée "nouveau"**

Par défaut : 24 heures

📁 `boutique/context_processors.py` (ligne 14)
```python
date_limite = timezone.now() - timedelta(hours=24)  # ← Modifier ici
```

**Exemples** :
```python
timedelta(hours=12)   # 12 heures
timedelta(hours=48)   # 2 jours
timedelta(days=7)     # 1 semaine
```

---

### **Ajouter d'autres types de notifications**

1. **Ajouter le type dans le modèle** :
```python
TYPE_CHOICES = [
    ('NOUVEAU_CLIENT', 'Nouveau Client'),
    ('URGENCE_COMMANDE', 'Commande Urgente'),  # ← NOUVEAU
]
```

2. **Créer la migration** :
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Modifier le context processor** :
```python
# Compter les commandes urgentes non vues
urgences_vues_ids = NotificationAdminVue.objects.filter(
    admin=request.user,
    type_notification='URGENCE_COMMANDE'
).values_list('objet_id', flat=True)

commandes_urgentes = Commande.objects.filter(
    statut='URGENT'
).exclude(id__in=urgences_vues_ids).count()
```

4. **Marquer comme vu dans la vue** :
```python
def admin_commandes_urgentes(request):
    commandes = Commande.objects.filter(statut='URGENT')
    
    for cmd in commandes:
        NotificationAdminVue.objects.get_or_create(
            admin=request.user,
            type_notification='URGENCE_COMMANDE',
            objet_id=cmd.id
        )
    # ...
```

---

## 🧪 Tests

### Test Manuel

```bash
# 1. Créer un nouveau client
python manage.py shell
>>> from django.contrib.auth.models import User
>>> client = User.objects.create_user('nouveau_client', 'client@test.com', 'password123')
>>> exit()

# 2. Se connecter comme admin
# Navigateur : /admin-panel/

# 3. Vérifier le badge
# ✓ Badge "Clients" affiche [1]

# 4. Cliquer sur "Clients"
# ✓ Page clients s'affiche
# ✓ Nouveau client visible dans la liste

# 5. Retourner au dashboard
# ✓ Badge "Clients" a DISPARU

# 6. Vérifier la base de données
python manage.py shell
>>> from boutique.models import NotificationAdminVue
>>> NotificationAdminVue.objects.filter(type_notification='NOUVEAU_CLIENT').count()
1  # ← Notification enregistrée
```

---

### Test Automatique

```python
# tests.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from boutique.models import NotificationAdminVue
from datetime import timedelta
from django.utils import timezone

class NotificationAdminVueTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
        self.client_test = Client()
        self.client_test.login(username='admin', password='admin123')
    
    def test_nouveau_client_badge(self):
        """Test que le badge apparaît pour un nouveau client"""
        # Créer un nouveau client
        nouveau_client = User.objects.create_user('client1', 'client1@test.com', 'pass123')
        
        # Récupérer le context processor
        response = self.client_test.get('/admin-panel/')
        self.assertEqual(response.context['admin_badges']['clients'], 1)
    
    def test_badge_disparait_apres_visite(self):
        """Test que le badge disparaît après la visite"""
        # Créer un nouveau client
        nouveau_client = User.objects.create_user('client2', 'client2@test.com', 'pass123')
        
        # Badge avant visite
        response = self.client_test.get('/admin-panel/')
        self.assertEqual(response.context['admin_badges']['clients'], 1)
        
        # Visiter la page clients
        self.client_test.get('/admin-panel/clients/')
        
        # Badge après visite
        response = self.client_test.get('/admin-panel/')
        self.assertEqual(response.context['admin_badges']['clients'], 0)
    
    def test_notifications_independantes_par_admin(self):
        """Test que chaque admin a ses propres notifications"""
        # Créer 2 admins
        admin2 = User.objects.create_superuser('admin2', 'admin2@test.com', 'admin123')
        
        # Créer un nouveau client
        nouveau_client = User.objects.create_user('client3', 'client3@test.com', 'pass123')
        
        # admin1 visite la page clients
        self.client_test.get('/admin-panel/clients/')
        
        # Badge admin1 = 0
        response = self.client_test.get('/admin-panel/')
        self.assertEqual(response.context['admin_badges']['clients'], 0)
        
        # Badge admin2 = 1 (n'a pas encore vu)
        self.client_test.logout()
        self.client_test.login(username='admin2', password='admin123')
        response = self.client_test.get('/admin-panel/')
        self.assertEqual(response.context['admin_badges']['clients'], 1)
```

**Exécuter les tests** :
```bash
python manage.py test boutique.tests.NotificationAdminVueTest
```

---

## 🚀 Améliorations Futures

### 1. **Nettoyage Automatique**

Supprimer les vieilles notifications après X jours :

```python
# management/commands/nettoyer_notifications.py
from django.core.management.base import BaseCommand
from boutique.models import NotificationAdminVue
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        date_limite = timezone.now() - timedelta(days=30)
        deleted = NotificationAdminVue.objects.filter(
            date_vue__lt=date_limite
        ).delete()
        self.stdout.write(f"✅ {deleted[0]} notifications supprimées")
```

**Cron job** (exécuter tous les jours) :
```bash
0 2 * * * cd /path/to/project && python manage.py nettoyer_notifications
```

---

### 2. **Dashboard Statistiques**

Ajouter un dashboard pour voir les tendances :

```python
def admin_stats_notifications(request):
    stats = {
        'total_vues': NotificationAdminVue.objects.count(),
        'par_type': NotificationAdminVue.objects.values('type_notification').annotate(
            count=Count('id')
        ),
        'par_admin': NotificationAdminVue.objects.values('admin__username').annotate(
            count=Count('id')
        ),
        'derniers_7_jours': NotificationAdminVue.objects.filter(
            date_vue__gte=timezone.now() - timedelta(days=7)
        ).values('date_vue__date').annotate(
            count=Count('id')
        ).order_by('date_vue__date')
    }
    return render(request, 'adminpanel/stats_notifications.html', stats)
```

---

### 3. **Notifications Push**

Envoyer une notification navigateur :

```javascript
// Demander la permission
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// Envoyer une notification
function sendNotification(title, message) {
    if (Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/static/img/logo.png',
            badge: '/static/img/badge.png'
        });
    }
}

// Utilisation
sendNotification('Nouveau client', '3 nouveaux clients se sont inscrits');
```

---

## 📝 Résumé

✅ **Modèle `NotificationAdminVue`** créé  
✅ **Context processor** modifié pour exclure les vus  
✅ **Vue `admin_clients_list`** marque automatiquement comme vu  
✅ **Badge disparaît** après clic  
✅ **Notifications indépendantes** par admin  
✅ **Migration** appliquée  
✅ **Tests** validés  

🎉 **Le système fonctionne parfaitement !**

Le badge des nouveaux clients disparaît maintenant automatiquement quand l'administrateur clique sur "Clients".
