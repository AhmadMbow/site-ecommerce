from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Django-allauth
    path('accounts/', include('allauth.urls')),

    # Favicon
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),

    # Site
    path('', include('boutique.urls')),

    # Redirection si quelqu'un tape /admin/orders/
    path('admin/orders/', RedirectView.as_view(url='/admin-panel/orders/', permanent=False)),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
