"""
Script pour configurer rapidement les applications OAuth
Usage: python3 manage.py shell < setup_oauth_apps.py
"""

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Obtenir le site par défaut
site = Site.objects.get_current()

print(f"Configuration OAuth pour le site: {site.domain}")

# ==============================
# GOOGLE OAUTH
# ==============================
print("\n📘 Configuration Google OAuth...")

google_app, created = SocialApp.objects.get_or_create(
    provider='google',
    name='Google OAuth',
    defaults={
        'client_id': 'VOTRE_GOOGLE_CLIENT_ID',
        'secret': 'VOTRE_GOOGLE_SECRET',
    }
)

if created:
    google_app.sites.add(site)
    print("✅ Application Google créée avec succès!")
    print("⚠️  N'oubliez pas de mettre à jour le Client ID et Secret dans l'admin!")
else:
    print("ℹ️  Application Google existe déjà")

print(f"   - Client ID: {google_app.client_id}")
print(f"   - Secret: {'*' * len(google_app.secret)}")

# ==============================
# FACEBOOK OAUTH
# ==============================
print("\n📘 Configuration Facebook OAuth...")

facebook_app, created = SocialApp.objects.get_or_create(
    provider='facebook',
    name='Facebook OAuth',
    defaults={
        'client_id': 'VOTRE_FACEBOOK_APP_ID',
        'secret': 'VOTRE_FACEBOOK_SECRET',
    }
)

if created:
    facebook_app.sites.add(site)
    print("✅ Application Facebook créée avec succès!")
    print("⚠️  N'oubliez pas de mettre à jour l'App ID et Secret dans l'admin!")
else:
    print("ℹ️  Application Facebook existe déjà")

print(f"   - App ID: {facebook_app.client_id}")
print(f"   - Secret: {'*' * len(facebook_app.secret)}")

# ==============================
# RÉSUMÉ
# ==============================
print("\n" + "="*60)
print("📋 RÉSUMÉ DE LA CONFIGURATION")
print("="*60)

apps = SocialApp.objects.all()
if apps.exists():
    print(f"\n✅ {apps.count()} application(s) OAuth configurée(s):")
    for app in apps:
        print(f"\n   🔹 {app.name}")
        print(f"      Provider: {app.provider}")
        print(f"      Client ID: {app.client_id[:20]}..." if len(app.client_id) > 20 else f"      Client ID: {app.client_id}")
        print(f"      Sites: {', '.join([str(s) for s in app.sites.all()])}")
else:
    print("\n⚠️  Aucune application OAuth configurée")

print("\n" + "="*60)
print("🔗 PROCHAINES ÉTAPES")
print("="*60)
print("""
1. Visitez http://127.0.0.1:8000/admin/socialaccount/socialapp/
2. Éditez chaque application
3. Remplacez les valeurs par défaut par vos vrais identifiants OAuth
4. Sauvegardez

Pour obtenir les identifiants:
- Google: https://console.cloud.google.com/
- Facebook: https://developers.facebook.com/

Consultez OAUTH_SETUP_GUIDE.md pour plus de détails.
""")

print("✨ Configuration terminée!")
