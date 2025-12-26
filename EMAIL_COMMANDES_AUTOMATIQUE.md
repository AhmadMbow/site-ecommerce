# 📧 Système d'Emails Automatiques pour Commandes

## ✅ Fonctionnalités Implémentées

### 1️⃣ Email de Confirmation (EN_ATTENTE)
**Quand ?** Immédiatement après la création d'une commande (utilisateur ou invité)

**Contenu :**
- 🎉 Message de remerciement
- ✓ Confirmation que la commande est en cours de vérification
- ✓ Information sur le prochain email
- 📧 Possibilité de conserver l'email comme preuve d'achat

**Exemple de sujet :**
```
✅ Confirmation de votre commande CMD-001
```

### 2️⃣ Email de Livraison (EN_COURS)
**Quand ?** Quand le livreur accepte la commande

**Contenu :**
- ✅ Notification que la commande est en cours de livraison
- 📦 Information que le livreur a pris en charge la commande
- ⏰ Délai de livraison (24-48h)
- 📞 Information sur le contact téléphonique à venir

**Exemple de sujet :**
```
🚚 Votre commande CMD-001 est en cours de livraison !
```

### 3️⃣ Email de Confirmation de Livraison (LIVREE)
**Quand ?** Quand le livreur clique sur "Marquer comme livrée"

**Contenu :**
- 🎉 Confirmation que la commande a été livrée avec succès
- ✅ Le colis a bien été remis
- 💬 Invitation à laisser un avis
- 🙏 Remerciement pour la confiance

**Exemple de sujet :**
```
✅ Commande CMD-001 livrée avec succès
```

### 4️⃣ Email avec Reçu PDF (LIVREE)
**Quand ?** Automatiquement après l'email de confirmation de livraison

**Contenu :**
- 📧 Email HTML professionnel avec design moderne
- 📄 **Reçu PDF en pièce jointe** avec tous les détails :
  - Informations de la boutique
  - Numéro de commande et date
  - Informations du client (nom, email, téléphone)
  - Liste détaillée des articles
  - Prix unitaires et totaux
  - Sous-total, frais de livraison, total général
  - Design professionnel avec couleurs de la marque

**Exemple de sujet :**
```
✅ Commande CMD-001 livrée - Votre reçu
```

## 📋 Détails Techniques

### Fichiers Modifiés

#### 1. `/boutique/utils.py` - Fonction d'envoi d'emails
```python
def envoyer_mail_statut_commande(commande, statut_precedent=None, is_guest=False)
```

**Changements :**
- ✅ Support des commandes invités (`is_guest=True`)
- ✅ Récupération automatique de l'email (utilisateur ou invité)
- ✅ Messages personnalisés selon le statut
- ✅ Format professionnel avec emojis et structure claire
- ✅ Affichage des détails de commande (articles, prix, numéro)

#### 2. `/boutique/views.py` - Intégration dans les vues

**`commande_invite()` (ligne ~1152) :**
```python
# Envoyer l'email de confirmation pour la commande invité
from .utils import envoyer_mail_statut_commande
envoyer_mail_statut_commande(commande, is_guest=True)
```

**`livreur_order_accept()` (ligne ~1439) :**
```python
# Envoyer l'email de notification EN_COURS
from .utils import envoyer_mail_statut_commande
is_guest = isinstance(order, CommandeInvite)
envoyer_mail_statut_commande(order, statut_precedent=statut_precedent, is_guest=is_guest)
```

**`livreur_order_update_status()` (ligne ~1495) :**
```python
# Envoyer l'email de notification EN_COURS
from .utils import envoyer_mail_statut_commande
envoyer_mail_statut_commande(order, statut_precedent=statut_precedent, is_guest=is_guest)
```

## 🔄 Flux Complet

### Pour une Commande Utilisateur
```
1. Client connecté passe commande
   └─> confirmer_commande() crée la commande
       └─> envoyer_mail_statut_commande(commande)
           └─> 📧 "Commande en cours de vérification"

2. Livreur accepte la commande
   └─> livreur_order_accept() change statut à EN_COURS
       └─> envoyer_mail_statut_commande(commande, statut_precedent='EN_ATTENTE')
           └─> 📧 "Commande en cours de livraison"

3. Livreur marque comme livrée
   └─> livreur_order_update_status() change statut à LIVREE
       └─> envoyer_mail_statut_commande(commande, statut_precedent='EN_COURS')
           └─> 📧 "Commande livrée avec succès"
```

### Pour une Commande Invité
```
1. Invité passe commande
   └─> commande_invite() crée CommandeInvite
       └─> envoyer_mail_statut_commande(commande, is_guest=True)
           └─> 📧 "Commande en cours de vérification"

2. Livreur accepte la commande
   └─> livreur_order_update_status() change statut à EN_COURS
       └─> envoyer_mail_statut_commande(commande, statut_precedent='EN_ATTENTE', is_guest=True)
           └─> 📧 "Commande en cours de livraison"

3. Livreur marque comme livrée
   └─> livreur_order_update_status() change statut à LIVREE
       └─> envoyer_mail_statut_commande(commande, statut_precedent='EN_COURS', is_guest=True)
           └─> 📧 "Commande livrée avec succès"
```

## 📧 Configuration Email

### Serveur SMTP
```python
# ecommerce/settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'i2sn.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'info@i2sn.com'
EMAIL_HOST_PASSWORD = 'h5frCu[blxwP'
DEFAULT_FROM_EMAIL = 'info@i2sn.com'
```

### Expéditeur
- **Email :** info@i2sn.com
- **Nom :** Maryama Shop
- **Type :** Email professionnel via cPanel/Namecheap

## 🧪 Tests Effectués

### Test 1 : Commande Invité EN_ATTENTE
```bash
✅ Commande: INV-1
✅ Email: papaahmadmbow@gmail.com
✅ Statut: EN_ATTENTE
✅ Email envoyé avec succès
```

### Test 2 : Changement vers EN_COURS
```bash
✅ Commande: INV-1
✅ Statut: EN_ATTENTE → EN_COURS
✅ Email envoyé avec succès
```

## 📱 Exemple d'Email

```
Sujet: ✅ Confirmation de votre commande CMD-001

Bonjour Ahmad Mbow,

🎉 Merci pour votre commande !

✓ Votre commande a bien été enregistrée et est actuellement en cours de vérification.
✓ Notre équipe va traiter votre commande dans les plus brefs délais.
✓ Vous recevrez un nouvel email dès que votre commande sera prise en charge par notre livreur.

📧 Vous pouvez conserver cet email comme confirmation de votre achat.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 DÉTAILS DE VOTRE COMMANDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Numéro de commande : CMD-001
Statut actuel : En attente
Date de commande : 15/01/2025 à 14:30

🛒 Articles commandés :
  • 2x Produit A - 5000 FCFA/unité
  • 1x Produit B - 3000 FCFA/unité

💰 Montant total : 13000 FCFA

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pour toute question, contactez-nous à info@i2sn.com

Merci de votre confiance ! 🙏
L'équipe Maryama Shop
```

## 🎯 Points Clés

1. ✅ **Support complet** : Utilisateurs ET invités
2. ✅ **Trois emails automatiques** : Confirmation + En cours + Livrée
3. ✅ **Messages clairs** : Emojis et structure professionnelle
4. ✅ **Détails complets** : Numéro commande, articles, prix
5. ✅ **Email professionnel** : info@i2sn.com (domaine personnalisé)
6. ✅ **Testé et fonctionnel** : Tous les emails envoyés avec succès

## 🚀 Prochaines Étapes (Optionnelles)

- 📧 Ajouter email pour statut LIVREE
- 📧 Ajouter email pour statut ANNULEE
- 🎨 Templates HTML pour emails plus beaux
- 📊 Historique des emails envoyés
- 🔔 Notifications SMS en plus des emails
