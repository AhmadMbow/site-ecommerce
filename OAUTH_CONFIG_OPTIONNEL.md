# Configuration OAuth (Optionnel)

## ✅ Ce qui fonctionne maintenant

Votre site e-commerce a maintenant :
- ✅ **Formulaire de connexion** moderne et fonctionnel
- ✅ **Formulaire d'inscription** avec tous les champs (username, email, téléphone, adresse, mot de passe)
- ✅ **Design responsive** avec gradient et animations
- ✅ **Validation en temps réel** (force du mot de passe, vérification de correspondance)
- ✅ **Infrastructure OAuth prête** (django-allauth installé)

## 🔒 Authentification traditionnelle (Actuelle)

Les utilisateurs peuvent :
1. S'inscrire avec username + email + téléphone + mot de passe
2. Se connecter avec username + mot de passe
3. Mot de passe oublié (si configuré)

**Aucune configuration supplémentaire requise !**

---

## 🌐 OAuth Social Login (Optionnel - À configurer si désiré)

Si vous souhaitez ajouter Google/Facebook login à l'avenir :

### Étape 1 : Obtenir les credentials API

#### Google OAuth
1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet ou sélectionner un existant
3. Activer "Google+ API"
4. Créer des credentials OAuth 2.0
5. Ajouter URLs autorisées :
   - URI de redirection : `http://localhost:8000/accounts/google/login/callback/`
   - Pour production : `https://votredomaine.com/accounts/google/login/callback/`
6. Copier **Client ID** et **Client Secret**

#### Facebook OAuth
1. Aller sur [Facebook Developers](https://developers.facebook.com/)
2. Créer une application
3. Ajouter le produit "Facebook Login"
4. Configurer OAuth Redirect URIs :
   - `http://localhost:8000/accounts/facebook/login/callback/`
5. Copier **App ID** et **App Secret**

### Étape 2 : Configurer dans Django Admin

1. Démarrer le serveur : `python manage.py runserver`
2. Créer un superuser si besoin : `python manage.py createsuperuser`
3. Aller sur : `http://localhost:8000/admin/`
4. Naviguer vers : **Sites** > **example.com**
   - Modifier : Domain name = `localhost:8000` (ou votre domaine)
   - Display name = `Maryama Shop`

5. Naviguer vers : **Social applications** > **Add social application**

   **Pour Google :**
   - Provider : Google
   - Name : Google Login
   - Client id : [Votre Google Client ID]
   - Secret key : [Votre Google Client Secret]
   - Sites : Sélectionner votre site (localhost:8000)
   - Sauvegarder

   **Pour Facebook :**
   - Provider : Facebook
   - Name : Facebook Login
   - Client id : [Votre Facebook App ID]
   - Secret key : [Votre Facebook App Secret]
   - Sites : Sélectionner votre site (localhost:8000)
   - Sauvegarder

### Étape 3 : Activer les boutons OAuth

1. Éditer `templates/registration/login.html`
2. Ajouter avant le lien "Pas encore de compte ?" :

```html
<div style="text-align: center; margin: 1.5rem 0;">
  <div style="color: #6c757d; margin-bottom: 1rem;">Ou connectez-vous avec</div>
  <div style="display: flex; gap: 1rem; justify-content: center;">
    <a href="{% url 'google_login' %}" style="flex: 1; padding: 0.75rem; background: #DB4437; color: white; border-radius: 8px; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
      <i class="fab fa-google"></i> Google
    </a>
    <a href="{% url 'facebook_login' %}" style="flex: 1; padding: 0.75rem; background: #4267B2; color: white; border-radius: 8px; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
      <i class="fab fa-facebook-f"></i> Facebook
    </a>
  </div>
</div>
```

### Étape 4 : Tester

1. Cliquer sur "Google" ou "Facebook" dans la page de connexion
2. Autoriser l'application
3. L'utilisateur sera créé automatiquement et connecté

---

## ⚙️ Configuration actuelle (settings.py)

```python
INSTALLED_APPS = [
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': 'VOTRE_GOOGLE_CLIENT_ID',  # ← À remplacer
            'secret': 'VOTRE_GOOGLE_CLIENT_SECRET',  # ← À remplacer
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
    'facebook': {
        'APP': {
            'client_id': 'VOTRE_FACEBOOK_APP_ID',  # ← À remplacer
            'secret': 'VOTRE_FACEBOOK_APP_SECRET',  # ← À remplacer
        },
        'SCOPE': ['email', 'public_profile'],
        'METHOD': 'oauth2',
    }
}
```

---

## 🎯 Résumé

- **Maintenant** : Connexion/inscription traditionnelle fonctionnelle ✅
- **Plus tard** : OAuth en option (si vous obtenez les credentials API)

**Pas besoin de configurer OAuth si l'authentification traditionnelle vous suffit !**
