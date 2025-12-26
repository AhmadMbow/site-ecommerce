# 🚀 GUIDE DE RÉSOLUTION - Problème de Style sur sadiboushop.com

## 🔍 Problème
Les styles CSS ne se chargent pas correctement sur le site en production.

## ✅ Solutions Appliquées

### 1. Configuration Django (settings_production.py)
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # ✅ Ajouté
STATICFILES_DIRS = [BASE_DIR / "static"]
```

### 2. Collecte des fichiers statiques
```bash
python3 manage.py collectstatic --noinput --settings=ecommerce.settings_production
```
✅ **Résultat:** 310 fichiers statiques collectés dans `/staticfiles`

### 3. Configuration .htaccess (Serveur Apache)
Ajout des règles de réécriture pour servir les fichiers statiques :
```apache
# Servir les fichiers statiques directement (CSS, JS, images)
RewriteCond %{REQUEST_URI} ^/static/(.*)$
RewriteRule ^static/(.*)$ staticfiles/$1 [L]

# Servir les fichiers media directement (uploads)
RewriteCond %{REQUEST_URI} ^/media/(.*)$
RewriteRule ^media/(.*)$ media/$1 [L]
```

## 📋 ÉTAPES À SUIVRE SUR LE SERVEUR

### Étape 1: Upload des fichiers
Uploadez les fichiers/dossiers suivants via cPanel File Manager ou FTP :
- ✅ `staticfiles/` (nouveau dossier créé)
- ✅ `.htaccess` (modifié)
- ✅ `ecommerce/settings_production.py`

### Étape 2: Vérifier la structure sur le serveur
Sur Namecheap, votre structure doit être :
```
/home/afjqtuev/sadiboushop.com/
├── staticfiles/          ← IMPORTANT: Doit être uploadé
│   ├── admin/
│   ├── css/
│   ├── js/
│   └── images/
├── media/
├── boutique/
├── dashboard/
├── ecommerce/
├── templates/
├── .htaccess            ← IMPORTANT: Modifié
├── passenger_wsgi.py
└── manage.py
```

### Étape 3: Vérifier les permissions
Dans cPanel File Manager :
1. Clic droit sur `staticfiles/` → Change Permissions → **755**
2. Tous les fichiers dans staticfiles → **644**

### Étape 4: Redémarrer l'application
Dans cPanel :
1. Allez dans **Setup Python App**
2. Trouvez votre application `sadiboushop`
3. Cliquez sur **Restart** (bouton circulaire)

### Étape 5: Vider le cache
1. Videz le cache de votre navigateur (Ctrl+Shift+Delete)
2. Ou testez en navigation privée (Ctrl+Shift+N)

## 🔧 Test de Diagnostic

Une fois uploadé, testez ces URLs directement :
```
https://sadiboushop.com/static/css/style.css
https://sadiboushop.com/static/js/main.js
```

Si ces URLs fonctionnent → ✅ Configuration correcte
Si erreur 404 → Vérifiez l'upload de `staticfiles/`

## ⚠️ Points de Vérification

1. **Le dossier staticfiles existe-t-il sur le serveur ?**
   - Oui → Passer à l'étape suivante
   - Non → Uploadez-le depuis votre projet local

2. **Les fichiers CSS sont-ils dans staticfiles ?**
   ```
   staticfiles/
   ├── css/
   │   ├── bootstrap.min.css
   │   ├── style.css
   │   └── ...
   ```

3. **Le .htaccess est-il bien à la racine ?**
   - Emplacement : `/home/afjqtuev/sadiboushop.com/.htaccess`

4. **L'application a-t-elle été redémarrée ?**
   - Setup Python App → Restart

## 🐛 Si le problème persiste

### Vérifier les logs d'erreur
Dans cPanel → **Errors** (section Metrics) :
```
Cherchez les erreurs 404 pour /static/...
```

### Tester avec DEBUG=True temporairement
Dans `passenger_wsgi.py`, remplacez temporairement :
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
```
Puis redémarrez et vérifiez si les styles apparaissent.

### Alternative: WhiteNoise
Si Apache ne sert pas les fichiers statiques, Django peut les servir via WhiteNoise.
Vérifiez que `whitenoise` est dans requirements.txt et installé.

## 📞 Commandes Utiles

```bash
# En local, recollectez les fichiers statiques
python3 manage.py collectstatic --noinput --settings=ecommerce.settings_production

# Vérifiez le contenu de staticfiles
ls -la staticfiles/

# Créez une archive pour upload plus facile
tar -czf staticfiles.tar.gz staticfiles/
```

## ✨ Résultat Attendu

Après ces corrections :
- ✅ Les CSS se chargent correctement
- ✅ Les images s'affichent
- ✅ Le JavaScript fonctionne
- ✅ Le site a le même aspect qu'en local

---

**Date:** 10 décembre 2025
**Site:** https://sadiboushop.com
**Problème:** Styles CSS non chargés en production
**Status:** ✅ Configuration corrigée - À déployer sur le serveur
