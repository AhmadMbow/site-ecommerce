# 📧 Configuration Email - maryamashop@gmail.com

## ✅ Email configuré

L'application est maintenant configurée pour utiliser: **maryamashop@gmail.com**

## 🔐 Générer un Mot de Passe d'Application Gmail

### Étape 1: Activer la validation en 2 étapes
1. Allez sur: https://myaccount.google.com/
2. Connectez-vous avec **maryamashop@gmail.com**
3. Dans le menu de gauche, cliquez sur **"Sécurité"**
4. Trouvez **"Validation en deux étapes"**
5. **Activez-la** si elle n'est pas déjà activée

### Étape 2: Créer un mot de passe d'application
1. Retournez dans **"Sécurité"**
2. Trouvez **"Mots de passe des applications"** (App passwords)
   - Si vous ne le voyez pas, assurez-vous que la validation en 2 étapes est activée
3. Cliquez sur **"Mots de passe des applications"**
4. Sélectionnez:
   - **App:** Autre (nom personnalisé)
   - **Nom:** "Maryama E-Commerce" ou "Django App"
5. Cliquez sur **"Générer"**
6. **Copiez le mot de passe** de 16 caractères (ex: `abcd efgh ijkl mnop`)

### Étape 3: Configurer dans Django
1. Ouvrez le fichier: `/home/ahmadmbow/e-commerce/ecommerce/ecommerce/settings.py`
2. Trouvez la ligne:
   ```python
   EMAIL_HOST_PASSWORD = 'YOUR_APP_PASSWORD_HERE'
   ```
3. Remplacez `YOUR_APP_PASSWORD_HERE` par le mot de passe généré (sans espaces):
   ```python
   EMAIL_HOST_PASSWORD = 'abcdefghijklmnop'
   ```

## 📝 Configuration Actuelle

```python
# ecommerce/settings.py (lignes 114-120)

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'maryamashop@gmail.com'
EMAIL_HOST_PASSWORD = 'YOUR_APP_PASSWORD_HERE'  # ← À REMPLACER
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

## 🧪 Tester l'envoi d'email

Une fois le mot de passe configuré, testez avec:

```bash
cd /home/ahmadmbow/e-commerce/ecommerce
python3 manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email Maryama Shop',
    'Ceci est un email de test depuis l\'application e-commerce.',
    settings.DEFAULT_FROM_EMAIL,
    ['votre_email_test@example.com'],  # Remplacez par votre email
    fail_silently=False,
)

# Si ça fonctionne, vous verrez: 1
# Sinon, une erreur s'affichera
```

## 🔍 Si ça ne fonctionne pas

### Erreur: "Username and Password not accepted"
- Vérifiez que la validation en 2 étapes est activée
- Générez un nouveau mot de passe d'application
- Assurez-vous de copier le mot de passe sans espaces

### Erreur: "SMTPAuthenticationError"
- Le mot de passe d'application est incorrect
- Générez un nouveau mot de passe

### Erreur: "Connection refused"
- Vérifiez votre connexion internet
- Assurez-vous que le port 587 n'est pas bloqué

## 📮 Emails envoyés automatiquement

L'application envoie des emails dans ces cas:
1. ✅ **Commande confirmée** - Client reçoit un email de confirmation
2. 📦 **Commande en cours de livraison** - Notification au client
3. ✅ **Commande livrée** - Email de confirmation de livraison
4. ❌ **Commande annulée** - Notification d'annulation

**Tous ces emails proviendront de:** maryamashop@gmail.com

## 🌐 Alternative: Configuration Namecheap

Si vous souhaitez utiliser un email professionnel hébergé sur Namecheap:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.privateemail.com'  # Serveur Namecheap
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@votredomaine.com'
EMAIL_HOST_PASSWORD = 'votre_mot_de_passe_email'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

**Note:** Pour Namecheap Private Email, utilisez:
- **Serveur SMTP:** mail.privateemail.com
- **Port:** 587 (TLS) ou 465 (SSL)
- **Nom d'utilisateur:** Votre adresse email complète
- **Mot de passe:** Le mot de passe de votre compte email

## ✅ Vérification finale

Après configuration:

```bash
cd /home/ahmadmbow/e-commerce/ecommerce
python3 manage.py runserver
```

Passez une commande test et vérifiez que l'email arrive bien depuis **maryamashop@gmail.com**.

---

**Configuration effectuée le:** 4 décembre 2025
**Email configuré:** maryamashop@gmail.com
**Prochaine étape:** Générer le mot de passe d'application Gmail
