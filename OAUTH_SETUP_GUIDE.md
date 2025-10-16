# Guide de Configuration OAuth - Google & Facebook

## Configuration complétée ✅

### Ce qui a été fait :

1. **Installation de django-allauth** ✅
   - Package installé avec succès
   - Migrations appliquées

2. **Configuration Django** ✅
   - `INSTALLED_APPS` mis à jour
   - `MIDDLEWARE` configuré
   - `AUTHENTICATION_BACKENDS` ajoutés
   - `SOCIALACCOUNT_PROVIDERS` configurés

3. **URLs configurées** ✅
   - `/accounts/` : Routes allauth
   - `/accounts/google/login/` : Connexion Google
   - `/accounts/facebook/login/` : Connexion Facebook

4. **Interface utilisateur** ✅
   - Boutons OAuth sur page de connexion
   - Design professionnel et moderne
   - Icônes Google et Facebook

---

## Configuration des API OAuth (À faire)

### 📘 GOOGLE OAUTH

#### Étape 1 : Créer un projet Google Cloud

1. Allez sur https://console.cloud.google.com/
2. Créez un nouveau projet ou sélectionnez-en un existant
3. Nom du projet : "Maryama Shop" (ou autre)

#### Étape 2 : Activer l'API Google+

1. Dans le menu, allez dans "APIs & Services" > "Library"
2. Recherchez "Google+ API"
3. Cliquez sur "ENABLE"

#### Étape 3 : Créer des identifiants OAuth

1. Allez dans "APIs & Services" > "Credentials"
2. Cliquez sur "Create Credentials" > "OAuth client ID"
3. Type d'application : "Web application"
4. Nom : "Maryama Shop OAuth"
5. **Origines JavaScript autorisées** :
   ```
   http://127.0.0.1:8000
   http://localhost:8000
   ```
6. **URI de redirection autorisées** :
   ```
   http://127.0.0.1:8000/accounts/google/login/callback/
   http://localhost:8000/accounts/google/login/callback/
   ```
7. Cliquez sur "Create"
8. **Copiez le Client ID et le Client Secret**

#### Étape 4 : Configurer dans Django Admin

1. Allez sur http://127.0.0.1:8000/admin/
2. Connectez-vous avec vos identifiants admin
3. Allez dans **"Social applications"** > **"Add"**
4. Remplissez :
   - **Provider** : Google
   - **Name** : Google OAuth
   - **Client id** : Collez votre Client ID
   - **Secret key** : Collez votre Client Secret
   - **Sites** : Sélectionnez "example.com" (ou votre site)
5. Sauvegardez

---

### 📘 FACEBOOK OAUTH

#### Étape 1 : Créer une application Facebook

1. Allez sur https://developers.facebook.com/
2. Cliquez sur "My Apps" > "Create App"
3. Type : "Consumer"
4. Nom : "Maryama Shop"
5. Email de contact : votre email
6. Créez l'app

#### Étape 2 : Configurer Facebook Login

1. Dans le dashboard de votre app, cliquez sur "Add Product"
2. Cherchez "Facebook Login" et cliquez sur "Set Up"
3. Choisissez "Web"
4. URL du site : `http://127.0.0.1:8000`

#### Étape 3 : Configurer les URLs de redirection

1. Dans le menu gauche : "Facebook Login" > "Settings"
2. **Valid OAuth Redirect URIs** :
   ```
   http://127.0.0.1:8000/accounts/facebook/login/callback/
   http://localhost:8000/accounts/facebook/login/callback/
   ```
3. Sauvegardez

#### Étape 4 : Récupérer les identifiants

1. Allez dans "Settings" > "Basic"
2. Copiez :
   - **App ID**
   - **App Secret** (cliquez sur "Show" pour le voir)

#### Étape 5 : Configurer dans Django Admin

1. Allez sur http://127.0.0.1:8000/admin/
2. Allez dans **"Social applications"** > **"Add"**
3. Remplissez :
   - **Provider** : Facebook
   - **Name** : Facebook OAuth
   - **Client id** : Collez votre App ID
   - **Secret key** : Collez votre App Secret
   - **Sites** : Sélectionnez "example.com"
4. Sauvegardez

---

## Test de l'implémentation

### Sans configuration OAuth (Mode Démo)

Actuellement, les boutons OAuth sont visibles mais renverront une erreur jusqu'à configuration complète.

**Message d'erreur attendu** :
```
SocialApp matching query does not exist.
```

### Après configuration OAuth

1. Cliquez sur "Google" ou "Facebook"
2. Vous serez redirigé vers la page de connexion du provider
3. Autorisez l'application
4. Vous serez redirigé vers votre site, connecté automatiquement
5. Un profil utilisateur sera créé avec les infos du provider

---

## Configuration Alternative : Fichier .env (Recommandé)

Créez un fichier `.env` à la racine du projet :

```env
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=votre_client_id_google
GOOGLE_OAUTH_SECRET=votre_secret_google

# Facebook OAuth
FACEBOOK_APP_ID=votre_app_id_facebook
FACEBOOK_APP_SECRET=votre_secret_facebook
```

Puis dans `settings.py`, remplacez :

```python
import os
from dotenv import load_dotenv

load_dotenv()

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_OAUTH_SECRET'),
            'key': ''
        }
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'APP': {
            'client_id': os.getenv('FACEBOOK_APP_ID'),
            'secret': os.getenv('FACEBOOK_APP_SECRET'),
            'key': ''
        }
    }
}
```

---

## URLs OAuth disponibles

- **Google Login** : http://127.0.0.1:8000/accounts/google/login/
- **Facebook Login** : http://127.0.0.1:8000/accounts/facebook/login/
- **Liste des providers** : http://127.0.0.1:8000/accounts/social/connections/

---

## Gestion des utilisateurs OAuth

Les utilisateurs connectés via OAuth :
- Ont un compte Django créé automatiquement
- Email vérifié automatiquement
- Peuvent se connecter avec username/password s'ils en définissent un
- Peuvent lier plusieurs comptes sociaux

---

## Commandes utiles

```bash
# Créer un superuser pour accéder à l'admin
python3 manage.py createsuperuser

# Vérifier la configuration
python3 manage.py check

# Lancer le serveur
python3 manage.py runserver
```

---

## Dépannage

### Erreur : "SocialApp matching query does not exist"
**Solution** : Configurez les applications sociales dans Django Admin

### Erreur : "redirect_uri_mismatch"
**Solution** : Vérifiez que les URLs de redirection sont identiques dans :
- Google Cloud Console / Facebook Developers
- Django Admin

### Erreur : "Invalid client"
**Solution** : Vérifiez que Client ID et Secret sont corrects

---

## Sécurité

⚠️ **Important** :
- Ne commitez JAMAIS vos clés OAuth sur Git
- Utilisez des variables d'environnement
- Activez HTTPS en production
- Configurez les domaines autorisés

---

## Prochaines étapes

1. ✅ Configurer Google OAuth (obtenir Client ID/Secret)
2. ✅ Configurer Facebook OAuth (obtenir App ID/Secret)
3. ✅ Ajouter les applications dans Django Admin
4. ✅ Tester la connexion
5. 🔄 Personnaliser le template de connexion sociale (optionnel)
6. 🔄 Ajouter d'autres providers (Twitter, GitHub, etc.)

---

## Ressources

- Django-allauth docs : https://docs.allauth.org/
- Google OAuth : https://console.cloud.google.com/
- Facebook Developers : https://developers.facebook.com/
