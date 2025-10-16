# 🧪 Guide de test - Authentification

## Test rapide (5 minutes)

### 1️⃣ Démarrer le serveur

```bash
cd /home/ahmadmbow/e-commerce/ecommerce
python3 manage.py runserver
```

---

### 2️⃣ Tester l'inscription

1. Ouvrir : http://localhost:8000/register/

2. Remplir le formulaire :
   ```
   Nom d'utilisateur : demo2024
   Email : demo@test.com
   Téléphone : 77 123 45 67
   Adresse : (laisser vide, optionnel)
   Mot de passe : Demo1234!
   Confirmer : Demo1234!
   ```

3. **Observations attendues :**
   - ✅ Indicateur de force du mot de passe s'affiche (Fort)
   - ✅ Message "Mots de passe différents" disparaît quand ils correspondent
   - ✅ Icône œil pour toggle password fonctionne
   - ✅ Design responsive et moderne

4. Cliquer "Créer mon compte"

5. **Résultat attendu :**
   - ✅ Redirection automatique vers la page boutique
   - ✅ Message "Compte créé avec succès"
   - ✅ Connecté automatiquement
   - ✅ Nom d'utilisateur visible dans navbar

---

### 3️⃣ Tester la déconnexion

1. Cliquer sur le profil dans navbar
2. Cliquer "Déconnexion"
3. **Résultat** : ✅ Déconnecté, redirection vers page logged_out

---

### 4️⃣ Tester la connexion

1. Aller sur : http://localhost:8000/login/

2. Entrer :
   ```
   Nom d'utilisateur : demo2024
   Mot de passe : Demo1234!
   ```

3. Cocher "Se souvenir de moi" (optionnel)

4. Cliquer "Se connecter"

5. **Résultat attendu :**
   - ✅ Connexion réussie
   - ✅ Redirection vers boutique
   - ✅ Profil accessible

---

### 5️⃣ Tester les validations

#### Test A : Username déjà pris
1. Se déconnecter
2. Essayer de créer un compte avec username : `demo2024`
3. **Résultat** : ❌ Erreur "A user with that username already exists."

#### Test B : Email déjà pris
1. Essayer username différent mais email : `demo@test.com`
2. **Résultat** : ❌ Erreur "Un compte existe déjà avec cet e-mail."

#### Test C : Passwords différents
1. Entrer password1 : `Test1234!`
2. Entrer password2 : `Test5678!`
3. **Résultat** : ❌ Message "Mots de passe différents", bouton désactivé

#### Test D : Password trop court
1. Entrer password : `Test1`
2. **Résultat** : ❌ Indicateur "Faible", alerte si soumission

#### Test E : Mauvais login
1. Connexion avec mauvais password
2. **Résultat** : ❌ Erreur "Invalid username or password"

---

### 6️⃣ Tester le responsive

1. Ouvrir DevTools (F12)
2. Mode responsive
3. Tester différentes tailles :

   **Mobile (320px)** :
   - ✅ Une seule colonne
   - ✅ Brand info masqué
   - ✅ Form pleine largeur
   - ✅ Inputs lisibles

   **Tablet (768px)** :
   - ✅ Split-screen visible
   - ✅ Brand info à gauche
   - ✅ Form à droite

   **Desktop (1200px)** :
   - ✅ Split-screen complet
   - ✅ Features list visible
   - ✅ Design optimal

---

### 7️⃣ Vérifier dans l'admin

1. Créer un superuser si nécessaire :
   ```bash
   python3 manage.py createsuperuser
   ```

2. Aller sur : http://localhost:8000/admin/

3. Naviguer vers **Users**

4. Vérifier que `demo2024` existe

5. Cliquer dessus et vérifier :
   - ✅ Email : demo@test.com
   - ✅ Username : demo2024
   - ✅ Staff status : Non (utilisateur normal)

6. Naviguer vers **User profiles**

7. Vérifier le profil de `demo2024` :
   - ✅ Phone : 77 123 45 67
   - ✅ Address : (vide si non rempli)
   - ✅ Role : client (par défaut)

---

## ✅ Checklist de validation

### Fonctionnalités
- [ ] Inscription fonctionne
- [ ] Login fonctionne
- [ ] Logout fonctionne
- [ ] Auto-login après inscription
- [ ] UserProfile créé automatiquement
- [ ] Validation username unique
- [ ] Validation email unique
- [ ] Passwords match check

### Design
- [ ] Gradient violet visible
- [ ] Split-screen sur desktop
- [ ] Icons FontAwesome affichés
- [ ] Toggle password fonctionne
- [ ] Password strength indicator
- [ ] Animations smooth
- [ ] Responsive mobile OK
- [ ] Responsive tablet OK

### Messages
- [ ] Erreurs affichées en rouge
- [ ] Success messages visibles
- [ ] Hints informatifs présents
- [ ] Aucune console error (F12)

---

## 🐛 Problèmes possibles

### Erreur : "SocialApp matching query does not exist"
**Solution** : OAuth retiré des templates, cette erreur ne devrait plus apparaître

### Erreur : Template not found
**Solution** : Vérifier que `/templates/registration/` contient bien login.html et register.html

### Erreur : "phone" field required
**Solution** : Template `register.html` inclut maintenant le champ téléphone

### Erreur : FontAwesome icons ne s'affichent pas
**Solution** : Vérifier que `base.html` charge FontAwesome :
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
```

---

## 🎯 Résultats attendus

Après tous les tests :
- ✅ 1 compte créé : `demo2024`
- ✅ 1 UserProfile associé avec téléphone
- ✅ Login/logout fonctionnels
- ✅ Validations opérationnelles
- ✅ Design professionnel et responsive
- ✅ Aucune erreur console

**Si tous les tests passent = Authentification validée ! 🎉**
