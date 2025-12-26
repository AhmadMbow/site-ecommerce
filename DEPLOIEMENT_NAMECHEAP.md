# 🚀 Guide de Déploiement - sadiboushop.com sur Namecheap

## 📋 Prérequis

- ✅ Compte Namecheap avec hébergement (Shared Hosting ou VPS)
- ✅ Domaine sadiboushop.com configuré
- ✅ Accès cPanel
- ✅ Certificat SSL (Let's Encrypt gratuit via cPanel)

---

## 📦 Étape 1: Préparation des fichiers locaux

### 1.1 Collecter les fichiers statiques

```bash
cd /home/ahmadmbow/e-commerce/ecommerce
source venv/bin/activate
python manage.py collectstatic --settings=ecommerce.settings_production
```

### 1.2 Créer l'archive ZIP

```bash
# Créer une archive de tout le projet
cd /home/ahmadmbow/e-commerce
zip -r sadiboushop.zip ecommerce -x "ecommerce/venv/*" -x "ecommerce/.git/*" -x "ecommerce/__pycache__/*" -x "*.pyc"
```

---

## 🔧 Étape 2: Configuration cPanel Namecheap

### 2.1 Connexion à cPanel

1. Connectez-vous à votre compte Namecheap
2. Allez dans **"Hosting List"** → **"cPanel"**
3. Ou accédez directement: `https://sadiboushop.com:2083`

### 2.2 Configurer Python (Setup Python App)

1. Dans cPanel, recherchez **"Setup Python App"**
2. Cliquez sur **"Create Application"**
3. Configurez:
   - **Python version**: 3.11 (ou la plus récente disponible)
   - **Application root**: `sadiboushop` (ou le nom de votre dossier)
   - **Application URL**: Laissez vide pour le domaine principal
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`
   - **Passenger log file**: `passenger.log`

4. Cliquez **"Create"**

### 2.3 Upload des fichiers

1. Dans cPanel → **"File Manager"**
2. Naviguez vers le dossier créé (ex: `/home/USERNAME/sadiboushop`)
3. Uploadez et extrayez `sadiboushop.zip`
4. Déplacez les fichiers pour avoir cette structure:

```
/home/USERNAME/sadiboushop/
├── passenger_wsgi.py
├── manage.py
├── requirements.txt
├── .htaccess
├── ecommerce/
│   ├── settings.py
│   ├── settings_production.py
│   ├── urls.py
│   └── wsgi.py
├── boutique/
├── dashboard/
├── templates/
├── static/
├── staticfiles/
└── media/
```

---

## 🗄️ Étape 3: Configuration de la base de données MySQL

### 3.1 Créer la base de données

1. Dans cPanel → **"MySQL Databases"**
2. Créez une nouvelle base: `USERNAME_sadiboushop`
3. Créez un utilisateur: `USERNAME_shopuser`
4. Assignez l'utilisateur à la base avec **tous les privilèges**

### 3.2 Mettre à jour settings_production.py

Modifiez les informations de connexion:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'USERNAME_sadiboushop',
        'USER': 'USERNAME_shopuser',
        'PASSWORD': 'votre_mot_de_passe',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

## 📧 Étape 4: Configuration Email

### 4.1 Créer un compte email

1. Dans cPanel → **"Email Accounts"**
2. Créez: `info@sadiboushop.com`

### 4.2 Mettre à jour settings_production.py

```python
EMAIL_HOST = 'mail.sadiboushop.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'info@sadiboushop.com'
EMAIL_HOST_PASSWORD = 'votre_mot_de_passe_email'
```

---

## 🐍 Étape 5: Installation des dépendances

### 5.1 Via l'interface Python App

1. Retournez dans **"Setup Python App"**
2. Cliquez sur votre application
3. Dans la section **"Configuration files"**, ajoutez `requirements.txt`
4. Cliquez **"Run Pip Install"**

### 5.2 Via Terminal (SSH)

Si vous avez accès SSH:

```bash
# Connectez-vous via SSH
ssh username@sadiboushop.com

# Activez l'environnement virtuel
source /home/USERNAME/virtualenv/sadiboushop/3.11/bin/activate

# Installez les dépendances
cd /home/USERNAME/sadiboushop
pip install -r requirements.txt
```

---

## 🔄 Étape 6: Migration et configuration initiale

### 6.1 Via Terminal SSH

```bash
# Activez l'environnement virtuel
source /home/USERNAME/virtualenv/sadiboushop/3.11/bin/activate
cd /home/USERNAME/sadiboushop

# Appliquez les migrations
python manage.py migrate --settings=ecommerce.settings_production

# Créez le superutilisateur
python manage.py createsuperuser --settings=ecommerce.settings_production

# Collectez les fichiers statiques
python manage.py collectstatic --settings=ecommerce.settings_production --noinput
```

### 6.2 Via cPanel (si pas de SSH)

1. Dans **"Setup Python App"** → votre application
2. Utilisez la commande **"Execute python script"**:
   - `manage.py migrate --settings=ecommerce.settings_production`
   - `manage.py collectstatic --settings=ecommerce.settings_production --noinput`

---

## 🔐 Étape 7: Configuration SSL/HTTPS

### 7.1 Installer le certificat SSL

1. Dans cPanel → **"SSL/TLS"** ou **"Let's Encrypt SSL"**
2. Installez un certificat pour `sadiboushop.com` et `www.sadiboushop.com`

### 7.2 Forcer HTTPS

Le fichier `.htaccess` inclut déjà la redirection. Vérifiez qu'il est bien à la racine.

---

## 🔄 Étape 8: Configuration Passenger

### 8.1 Vérifier passenger_wsgi.py

Assurez-vous que les chemins sont corrects:

```python
import os
import sys

# Chemin vers votre application
application_path = '/home/USERNAME/sadiboushop'
sys.path.insert(0, application_path)

# Chemin vers l'environnement virtuel
venv_path = '/home/USERNAME/virtualenv/sadiboushop/3.11/lib/python3.11/site-packages'
sys.path.insert(0, venv_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings_production')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 8.2 Redémarrer l'application

Dans **"Setup Python App"** → Cliquez **"Restart"**

---

## ✅ Étape 9: Vérification finale

### 9.1 Tests à effectuer

1. **Page d'accueil**: https://sadiboushop.com
2. **Admin Django**: https://sadiboushop.com/admin/
3. **Fichiers statiques**: Vérifiez CSS et images
4. **Médias**: Testez l'upload d'images
5. **Email**: Testez l'envoi d'emails

### 9.2 En cas de problème

Vérifiez les logs:
- Passenger log: `/home/USERNAME/sadiboushop/passenger.log`
- Error log: Dans cPanel → **"Errors"**

---

## 📝 Étape 10: Maintenance

### Mise à jour du site

```bash
# 1. Faire les modifications localement
# 2. Créer une nouvelle archive
# 3. Uploader via File Manager
# 4. Redémarrer l'application Python
```

### Backup de la base de données

1. cPanel → **"Backup"** ou **"phpMyAdmin"**
2. Exportez régulièrement votre base MySQL

---

## 🆘 Dépannage courant

### Erreur 500 / Site ne charge pas

1. Vérifiez `passenger.log`
2. Vérifiez les permissions des fichiers (644 pour fichiers, 755 pour dossiers)
3. Assurez-vous que `passenger_wsgi.py` est correctement configuré

### Fichiers statiques ne s'affichent pas

1. Vérifiez `STATIC_ROOT` dans settings
2. Relancez `collectstatic`
3. Vérifiez les permissions du dossier `staticfiles`

### Erreur de base de données

1. Vérifiez les credentials MySQL
2. Assurez-vous que `mysqlclient` est installé
3. Testez la connexion via phpMyAdmin

---

## 📞 Support Namecheap

- Live Chat: https://www.namecheap.com/support/live-chat/
- Knowledgebase: https://www.namecheap.com/support/knowledgebase/

---

## 🎉 Félicitations!

Votre site **sadiboushop.com** devrait maintenant être en ligne! 🛒

---

### Fichiers créés pour le déploiement:

| Fichier | Description |
|---------|-------------|
| `settings_production.py` | Configuration Django pour la production |
| `passenger_wsgi.py` | Point d'entrée pour Passenger (cPanel) |
| `.htaccess` | Configuration Apache (redirections, sécurité) |
| `requirements.txt` | Dépendances Python |
| `.env.example` | Template des variables d'environnement |
| `DEPLOIEMENT_NAMECHEAP.md` | Ce guide |
