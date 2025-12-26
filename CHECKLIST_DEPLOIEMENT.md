# ✅ CHECKLIST DÉPLOIEMENT - sadiboushop.com

## 🔧 PRÉPARATION (Fait ✅)
- [x] Fichiers statiques collectés (310 fichiers)
- [x] Archive staticfiles.tar.gz créée (10 MB)
- [x] .htaccess configuré avec règles de réécriture
- [x] settings_production.py avec STATIC_ROOT

## 📤 À FAIRE SUR CPANEL

### 1. Upload des fichiers
- [ ] Connectez-vous à cPanel (https://namecheap.com)
- [ ] Ouvrez File Manager
- [ ] Naviguez vers `/home/afjqtuev/sadiboushop.com/`
- [ ] Uploadez `staticfiles.tar.gz` (10 MB)
- [ ] Uploadez `.htaccess` (remplacez l'ancien)

### 2. Extraction de l'archive
- [ ] Clic droit sur `staticfiles.tar.gz`
- [ ] Choisir "Extract"
- [ ] Vérifier que le dossier `staticfiles/` est créé
- [ ] Supprimer `staticfiles.tar.gz` (optionnel)

### 3. Permissions
- [ ] Dossier `staticfiles/` → 755
- [ ] Tous les fichiers dans staticfiles → 644
- [ ] Fichier `.htaccess` → 644

### 4. Redémarrage
- [ ] Allez dans "Setup Python App"
- [ ] Trouvez l'application "sadiboushop"
- [ ] Cliquez sur le bouton "Restart" ↻

### 5. Test
- [ ] Videz le cache de votre navigateur (Ctrl+Shift+Delete)
- [ ] Testez: https://sadiboushop.com
- [ ] Vérifiez que les styles s'affichent correctement
- [ ] Testez en navigation privée (Ctrl+Shift+N)

## 🧪 TESTS DIRECTS

Testez ces URLs pour vérifier que les fichiers statiques sont accessibles :

```
✅ https://sadiboushop.com/static/css/bootstrap.min.css
✅ https://sadiboushop.com/static/js/main.js
✅ https://sadiboushop.com/static/images/logo.png
```

Si erreur 404 → Vérifiez l'upload du dossier staticfiles

## ⚠️ EN CAS DE PROBLÈME

### Les styles ne s'affichent toujours pas ?
1. Vérifiez les logs d'erreur (cPanel → Errors)
2. Vérifiez que staticfiles/ existe bien sur le serveur
3. Vérifiez les permissions (755/644)
4. Testez les URLs directes ci-dessus

### Erreur 500 ?
1. Vérifiez les logs Python (cPanel → Setup Python App → Log)
2. Vérifiez que passenger_wsgi.py est correct
3. Vérifiez que le venv est bien configuré

### Page blanche ?
1. Redémarrez l'application
2. Vérifiez DEBUG=False dans settings_production.py
3. Collectez à nouveau les fichiers statiques

## 📞 COMMANDES DE DIAGNOSTIC (via SSH si disponible)

```bash
# Vérifier la structure
ls -la /home/afjqtuev/sadiboushop.com/staticfiles/

# Vérifier les permissions
find staticfiles/ -type d -ls
find staticfiles/ -type f -ls | head

# Tester Apache
curl -I https://sadiboushop.com/static/css/bootstrap.min.css
```

## 🎉 SUCCÈS !

Si tout fonctionne :
- ✅ Le site affiche correctement les styles
- ✅ Les images se chargent
- ✅ Les boutons et formulaires ont le bon style
- ✅ Le site ressemble à la version locale

---

**Temps estimé:** 15-20 minutes
**Difficulté:** Facile
**Dernière mise à jour:** 10 décembre 2025
