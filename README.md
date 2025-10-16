# 🛍️ Site E-commerce Django

Site e-commerce moderne avec gestion des commandes, livreurs et panneau d'administration.

## 🚀 Installation Rapide

### Prérequis
- Python 3.8+
- pip
- virtualenv (recommandé)

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/AhmadMbow/site-ecommerce.git
cd site-ecommerce

# 2. Créer un environnement virtuel (optionnel mais recommandé)
python3 -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# venv\Scripts\activate  # Sur Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Faire les migrations
python3 manage.py migrate

# 5. Créer un superuser
python3 manage.py createsuperuser

# 6. Lancer le serveur
python3 manage.py runserver
```

Accéder au site : http://127.0.0.1:8000/

## 📦 Fonctionnalités

### 🛒 Pour les Clients
- ✅ Parcourir les produits avec filtres et recherche
- ✅ Ajouter au panier et gérer les quantités
- ✅ Comparer les produits
- ✅ Liste de souhaits (wishlist)
- ✅ Profil utilisateur avec adresses
- ✅ Suivi des commandes en temps réel
- ✅ Géolocalisation pour la livraison
- ✅ Notation et avis sur les produits

### 🚚 Pour les Livreurs
- ✅ Dashboard dédié avec statistiques
- ✅ Liste des commandes à livrer
- ✅ Carte interactive avec itinéraires
- ✅ Mise à jour du statut de livraison
- ✅ Historique des livraisons

### 👨‍💼 Pour les Administrateurs
- ✅ Panneau d'administration complet
- ✅ Gestion des produits et catégories
- ✅ Gestion des commandes
- ✅ Gestion des livreurs et clients
- ✅ Statistiques et rapports
- ✅ Gestion du stock automatique

## 🎨 Design

- **Interface moderne** avec effets glassmorphism
- **Animations fluides** et micro-interactions
- **100% Responsive** (mobile, tablette, desktop)
- **Thème** : Noir et jaune/or (#232526 et #ffc107)

## 🔐 Authentification

### URLs de connexion :
- `/login/` ou `/accounts/login/`
- `/register/` ou `/accounts/register/`

### Redirections après connexion :
| Rôle | Redirection |
|------|-------------|
| Client | `/boutique/` |
| Livreur | `/livreur/dashboard/` |
| Admin | `/admin-panel/` |

## 📁 Structure du Projet

```
ecommerce/
├── boutique/              # Application principale
│   ├── models.py          # Modèles (Produit, Commande, etc.)
│   ├── views.py           # Vues et logique métier
│   ├── urls.py            # Routes URL
│   └── forms.py           # Formulaires
├── dashboard/             # Dashboard admin
├── dashboard_livraison/   # Dashboard livreur
├── templates/             # Templates HTML
│   ├── boutique/          # Templates boutique
│   ├── registration/      # Templates auth
│   └── base.html          # Template de base
├── static/                # Fichiers statiques (CSS, JS, images)
├── media/                 # Fichiers uploadés (avatars, produits)
└── manage.py              # Commandes Django
```

## 🔧 Configuration

### Variables d'environnement (optionnel)

Créer un fichier `.env` à la racine :

```env
SECRET_KEY=votre_clé_secrète
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### APIs externes utilisées

- **Leaflet** : Cartes interactives
- **Nominatim** : Géocodage inversé (coordonnées → adresse)
- **Font Awesome** : Icônes
- **Google Fonts** : Police Poppins

## 🤝 Collaboration

Pour collaborer sur ce projet :

1. **Récupérer les derniers changements** :
   ```bash
   git pull origin main
   ```

2. **Faire vos modifications** et tester

3. **Commit et push** :
   ```bash
   git add .
   git commit -m "Description des changements"
   git push origin main
   ```

📖 **Guide complet** : Voir [GUIDE_GIT_COLLABORATION.md](GUIDE_GIT_COLLABORATION.md)

## 📝 Documentation

| Document | Description |
|----------|-------------|
| [GUIDE_GIT_COLLABORATION.md](GUIDE_GIT_COLLABORATION.md) | Guide Git pour collaborateurs |
| [CORRECTION_REDIRECTIONS_AUTH.md](CORRECTION_REDIRECTIONS_AUTH.md) | Redirections après connexion |
| [CORRECTION_URL_LOGIN.md](CORRECTION_URL_LOGIN.md) | Configuration des URLs de login |
| [AMELIORATIONS_PROFIL.md](AMELIORATIONS_PROFIL.md) | Améliorations du profil utilisateur |
| [GUIDE_VISUEL_PROFIL.md](GUIDE_VISUEL_PROFIL.md) | Guide visuel du profil |

## 🧪 Tests

```bash
# Tests Django
python3 manage.py test

# Tests spécifiques
./test_profile.sh         # Test du profil
./test_panier_similaires.sh  # Test du panier
./test_comparaison.sh     # Test de la comparaison
```

## 📊 Technologies Utilisées

### Backend
- **Django 4.x** - Framework Python
- **SQLite** - Base de données (dev)
- **Django Allauth** - Authentification
- **Pillow** - Traitement d'images

### Frontend
- **HTML5 / CSS3** - Structure et styles
- **JavaScript (Vanilla)** - Interactivité
- **Bootstrap 5** - Framework CSS
- **Leaflet** - Cartes interactives
- **Font Awesome** - Icônes

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
# Vérifier les migrations
python3 manage.py makemigrations
python3 manage.py migrate
```

### Erreur "Port already in use"
```bash
# Tuer le processus sur le port 8000
pkill -f "python3 manage.py runserver"
# Ou utiliser un autre port
python3 manage.py runserver 8080
```

### Problèmes de permissions avec media/
```bash
chmod -R 755 media/
```

## 📈 Améliorations Futures

- [ ] Paiement en ligne (Stripe, PayPal)
- [ ] Notifications push
- [ ] Chat en direct avec support
- [ ] Export des commandes en PDF
- [ ] API REST pour mobile app
- [ ] Tests automatisés complets
- [ ] Déploiement Docker

## 👨‍💻 Auteur

**Ahmad Mbow**
- GitHub: [@AhmadMbow](https://github.com/AhmadMbow)
- Projet: [site-ecommerce](https://github.com/AhmadMbow/site-ecommerce)

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- Django Documentation
- Bootstrap Team
- Leaflet.js
- Font Awesome
- Toute la communauté open source

---

**Dernière mise à jour** : 16 octobre 2025  
**Version** : 1.0  
**Status** : 🟢 En développement actif
