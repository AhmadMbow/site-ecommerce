# 🚀 COMMANDES SSH POUR EXTRACTION (si vous avez accès SSH)

## Si vous avez accès SSH à Namecheap, utilisez ces commandes :

```bash
# 1. Se connecter en SSH
ssh afjqtuev@sadiboushop.com

# 2. Aller dans le répertoire du site
cd ~/sadiboushop.com

# 3. Extraire l'archive staticfiles (si uploadée)
tar -xzf staticfiles.tar.gz

# 4. Vérifier que le dossier est créé
ls -la staticfiles/

# 5. Définir les bonnes permissions
chmod 755 staticfiles/
find staticfiles/ -type d -exec chmod 755 {} \;
find staticfiles/ -type f -exec chmod 644 {} \;

# 6. Vérifier les permissions
ls -la staticfiles/ | head

# 7. Redémarrer l'application (via cPanel ou commande Passenger)
touch tmp/restart.txt

# 8. Vérifier les logs
tail -f logs/error.log
```

## ⚠️ Si pas d'accès SSH

Utilisez **cPanel File Manager** :
1. Upload de staticfiles.tar.gz
2. Clic droit → Extract
3. Change Permissions via l'interface graphique
4. Restart via Setup Python App

## 📋 Vérification rapide

```bash
# Tester si les fichiers statiques sont accessibles
curl -I https://sadiboushop.com/static/css/bootstrap.min.css

# Doit retourner : HTTP/2 200
```

## 🔍 Debug

```bash
# Voir la structure complète
tree staticfiles/ -L 2

# Compter les fichiers
find staticfiles/ -type f | wc -l
# Devrait afficher : 310

# Vérifier l'espace disque
du -sh staticfiles/
# Environ 10M
```
