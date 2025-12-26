#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "  📧 CONFIGURATION EMAIL - MARYAMA SHOP"
echo "════════════════════════════════════════════════════════"
echo ""

cd /home/ahmadmbow/e-commerce/ecommerce

echo "📋 Configuration actuelle (settings.py):"
echo "─────────────────────────────────────────────────────────"
python3 -c "
import sys
sys.path.insert(0, '/home/ahmadmbow/e-commerce/ecommerce')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
import django
django.setup()
from django.conf import settings

print(f'EMAIL_HOST:          {settings.EMAIL_HOST}')
print(f'EMAIL_PORT:          {settings.EMAIL_PORT}')
print(f'EMAIL_USE_TLS:       {settings.EMAIL_USE_TLS}')
print(f'EMAIL_HOST_USER:     {settings.EMAIL_HOST_USER}')
print(f'EMAIL_HOST_PASSWORD: {\"*\" * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else \"NON CONFIGURÉ\"}')
print(f'DEFAULT_FROM_EMAIL:  {settings.DEFAULT_FROM_EMAIL}')
"

echo ""
echo "─────────────────────────────────────────────────────────"
echo ""

# Vérifier si le mot de passe est configuré
if grep -q "YOUR_APP_PASSWORD_HERE" /home/ahmadmbow/e-commerce/ecommerce/ecommerce/settings.py; then
    echo "⚠️  ACTION REQUISE:"
    echo ""
    echo "Le mot de passe d'application Gmail n'est pas encore configuré."
    echo ""
    echo "📝 Suivez ces étapes:"
    echo ""
    echo "1. Allez sur: https://myaccount.google.com/apppasswords"
    echo "   (Connectez-vous avec maryamashop@gmail.com)"
    echo ""
    echo "2. Activez la validation en 2 étapes si nécessaire"
    echo ""
    echo "3. Créez un mot de passe d'application:"
    echo "   - App: Autre (nom personnalisé)"
    echo "   - Nom: Django Maryama Shop"
    echo ""
    echo "4. Copiez le mot de passe généré (16 caractères)"
    echo ""
    echo "5. Modifiez le fichier:"
    echo "   /home/ahmadmbow/e-commerce/ecommerce/ecommerce/settings.py"
    echo ""
    echo "   Ligne 119:"
    echo "   EMAIL_HOST_PASSWORD = 'VOTRE_MOT_DE_PASSE_ICI'"
    echo ""
    echo "6. Redémarrez le serveur Django"
    echo ""
else
    echo "✅ Mot de passe d'application configuré"
    echo ""
    echo "🧪 Test de connexion SMTP..."
    python3 -c "
import sys
sys.path.insert(0, '/home/ahmadmbow/e-commerce/ecommerce')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
import django
django.setup()
from django.core.mail import EmailMessage
from django.conf import settings
import smtplib

try:
    # Test de connexion
    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    server.starttls()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.quit()
    print('✅ Connexion SMTP réussie!')
    print('')
    print('📧 Les emails seront envoyés depuis: maryamashop@gmail.com')
except Exception as e:
    print(f'❌ Erreur de connexion: {e}')
    print('')
    print('Vérifiez le mot de passe d\\'application.')
"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "  📚 Documentation: CONFIG_EMAIL_MARYAMASHOP.md"
echo "════════════════════════════════════════════════════════"
