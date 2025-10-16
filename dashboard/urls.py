from django.urls import path
from . import views

urlpatterns = [
    path('livreur/', views.livreur_dashboard, name='livreur_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
]
