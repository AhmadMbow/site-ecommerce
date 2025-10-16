# 🤝 Guide de Collaboration Git - E-commerce

## 🎯 Pour les Collaborateurs

### 1️⃣ Première Installation (Nouveau Collaborateur)

```bash
# Cloner le dépôt
git clone https://github.com/AhmadMbow/site-ecommerce.git

# Entrer dans le projet
cd site-ecommerce

# Installer les dépendances Python
pip install -r requirements.txt

# Faire les migrations Django
python3 manage.py migrate

# Créer un superuser (optionnel)
python3 manage.py createsuperuser

# Lancer le serveur
python3 manage.py runserver
```

### 2️⃣ Récupérer les Mises à Jour (Collaborateur Existant)

```bash
# Se placer dans le projet
cd /chemin/vers/site-ecommerce

# Récupérer les derniers changements
git pull origin main

# Si des migrations Django ont été ajoutées
python3 manage.py migrate

# Relancer le serveur
python3 manage.py runserver
```

---

## 👨‍💻 Pour le Propriétaire (Toi)

### Envoyer tes Changements sur GitHub

```bash
# 1. Voir les fichiers modifiés
git status

# 2. Ajouter les fichiers
git add .
# OU ajouter des fichiers spécifiques
git add fichier1.py fichier2.py

# 3. Créer un commit
git commit -m "Description des changements"

# 4. Envoyer sur GitHub
git push origin main
```

---

## 🔄 Workflow de Collaboration Complet

### Scénario : Toi (Ahmad) et un Collaborateur (Marie)

#### 📤 Ahmad fait des changements :
```bash
# Ahmad modifie des fichiers
git add .
git commit -m "✨ Ajout fonctionnalité X"
git push origin main
```

#### 📥 Marie récupère les changements :
```bash
# Marie veut travailler
git pull origin main
# ✅ Elle a maintenant les derniers changements d'Ahmad
```

#### 📤 Marie fait ses propres changements :
```bash
# Marie modifie des fichiers
git add .
git commit -m "🐛 Correction bug Y"
git push origin main
```

#### 📥 Ahmad récupère les changements de Marie :
```bash
# Ahmad veut voir le travail de Marie
git pull origin main
# ✅ Il a maintenant les changements de Marie
```

---

## 🚨 Gestion des Conflits

### Si Git détecte un conflit lors du `git pull` :

```bash
# 1. Git vous dira quels fichiers sont en conflit
Auto-merging fichier.py
CONFLICT (content): Merge conflict in fichier.py

# 2. Ouvrir le fichier en conflit
# Vous verrez quelque chose comme :
<<<<<<< HEAD
votre code
=======
code du collaborateur
>>>>>>> origin/main

# 3. Éditer le fichier pour garder la bonne version
# Supprimer les marqueurs <<<<<<, =======, >>>>>>>

# 4. Marquer le conflit comme résolu
git add fichier.py

# 5. Finaliser la fusion
git commit -m "🔀 Résolution conflit fichier.py"

# 6. Envoyer la résolution
git push origin main
```

---

## 📋 Commandes Git Essentielles

| Commande | Description |
|----------|-------------|
| `git status` | Voir les fichiers modifiés |
| `git pull origin main` | Récupérer les changements de GitHub |
| `git add .` | Ajouter tous les fichiers modifiés |
| `git add fichier.py` | Ajouter un fichier spécifique |
| `git commit -m "message"` | Créer un commit avec un message |
| `git push origin main` | Envoyer les commits sur GitHub |
| `git log` | Voir l'historique des commits |
| `git diff` | Voir les différences non commitées |
| `git branch` | Voir les branches disponibles |
| `git checkout -b nouvelle-branche` | Créer une nouvelle branche |

---

## 🌿 Travail avec des Branches (Recommandé)

### Pourquoi utiliser des branches ?
- Travailler sur des fonctionnalités sans casser `main`
- Plusieurs personnes peuvent travailler en parallèle
- Facilite la revue de code

### Workflow avec branches :

```bash
# 1. Créer une branche pour une nouvelle fonctionnalité
git checkout -b feature/nouvelle-fonctionnalite

# 2. Faire vos modifications
git add .
git commit -m "✨ Ajout nouvelle fonctionnalité"

# 3. Envoyer la branche sur GitHub
git push origin feature/nouvelle-fonctionnalite

# 4. Sur GitHub, créer une Pull Request (PR)
# Cela permet aux autres de voir et valider vos changements

# 5. Une fois validé, fusionner dans main
# (Sur GitHub via l'interface ou en ligne de commande)

# 6. Revenir sur main et mettre à jour
git checkout main
git pull origin main

# 7. Supprimer la branche locale (optionnel)
git branch -d feature/nouvelle-fonctionnalite
```

---

## 🔐 Configuration Git (Première fois)

Si vous n'avez jamais configuré Git sur votre machine :

```bash
# Configurer votre nom
git config --global user.name "Votre Nom"

# Configurer votre email
git config --global user.email "votre.email@example.com"

# Vérifier la configuration
git config --list
```

---

## 📦 Fichiers à NE PAS Commit

Assurez-vous d'avoir un `.gitignore` qui exclut :

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
*.egg-info/
dist/
build/

# Django
*.log
db.sqlite3
media/
staticfiles/

# Environment
.env
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## ⚡ Raccourcis Utiles

### Créer des alias Git :

```bash
# Ajouter des raccourcis
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.cm commit
git config --global alias.br branch

# Maintenant vous pouvez utiliser :
git st  # au lieu de git status
git co main  # au lieu de git checkout main
git cm -m "message"  # au lieu de git commit -m "message"
```

---

## 🆘 Commandes d'Urgence

### Annuler le dernier commit (non pushé) :
```bash
git reset --soft HEAD~1
```

### Annuler toutes les modifications locales :
```bash
git reset --hard origin/main
```

### Voir ce qui a changé :
```bash
git diff
```

### Voir l'historique :
```bash
git log --oneline --graph --all
```

---

## 📞 Contact et Support

Si vous avez des questions :
1. Vérifiez d'abord la documentation GitHub
2. Utilisez `git --help <commande>` pour l'aide
3. Contactez le chef de projet (Ahmad)

---

## 🎓 Ressources Supplémentaires

- [Documentation Git officielle](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

---

**Dernière mise à jour** : 16 octobre 2025  
**Projet** : Site E-commerce Django  
**Dépôt** : https://github.com/AhmadMbow/site-ecommerce
