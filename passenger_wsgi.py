"""
Passenger WSGI Configuration for Namecheap/cPanel
Site: sadiboushop.com
"""

import os
import sys

# Chemin vers le répertoire de l'application
application_path = os.path.dirname(os.path.abspath(__file__))

# Ajouter le chemin de l'application au PYTHONPATH
if application_path not in sys.path:
    sys.path.insert(0, application_path)

# Chemin absolu vers le venv (doit correspondre à PassengerPython dans .htaccess)
venv_path = '/home/afjqtuev/virtualenv/sadiboushop/3.12/lib/python3.12/site-packages'
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings_production')

# Import de l'application WSGI Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()