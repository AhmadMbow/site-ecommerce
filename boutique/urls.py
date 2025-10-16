from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import AdminPasswordChangeView

urlpatterns = [
    # Public / boutique
    path('', views.index, name='home'),
    path('boutique/', views.boutique, name='boutique'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('compare/', views.compare, name='compare'),
    path('oauth-demo/', views.oauth_demo, name='oauth_demo'),
    path('a-propos/', views.about, name='about'),
    path('produit/<int:pk>/', views.produit_detail, name='produit_detail'),

    # Auth
    path('accounts/login/', views.custom_login, name='login'),
    path('login/', views.custom_login, name='login_short'),  # Alias pour /login/
    path('accounts/register/', views.register, name='register'),
    path('register/', views.register, name='register_short'),  # Alias pour /register/
    path('accounts/logout/', LogoutView.as_view(next_page='home'), name='logout'),

    # Redirections rôle
    path('dashboard/', views.dashboard, name='dashboard'),
    path('post-login/', views.post_login_redirect, name='post_login_redirect'),

    # Clients
    path('profile/', views.profile, name='profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('mes-commandes/', views.mes_commandes, name='mes_commandes'),
    path('orders/', views.mes_commandes, name='orders'),

    # Adresses (profil)
    path('profile/adresse/<int:pk>/defaut/', views.adresse_defaut, name='adresse_defaut'),
    path('profile/adresse/<int:pk>/supprimer/', views.adresse_supprimer, name='adresse_supprimer'),
    path('profile/adresse/<int:pk>/modifier/', views.adresse_modifier, name='adresse_modifier'),

    # Livreur
    path('livreur/profil/', views.livreur_profile, name='livreur_profile'),
    path('livreur/dashboard/', views.livreur_dashboard, name='livreur_dashboard'),
    path('livreur/orders/', views.livreur_orders, name='livreur_orders'),
    path('livreur/map/', views.livreur_map, name='livreur_map'),  
    path('livreur/stats/', views.livreur_stats, name='livreur_stats'),
    path('livreur/profile/', views.livreur_profile, name='livreur_profile'),
    path('livreur/order/<int:pk>/', views.livreur_order_detail, name='livreur_order_detail'),
    path('livreur/order/<int:pk>/update-status/', views.livreur_order_update_status, name='livreur_order_update_status'),
    path('produits/<int:produit_id>/noter/', views.noter_produit, name='noter_produit'),
    path('livreur/password/', views.livreur_change_password, name='livreur_change_password'),
    # Notation produits (alias pour compat JS)
    path('produit/<int:produit_id>/noter/', views.noter_produit, name='noter_produit_alias'),

    # Panier
    path('panier/', views.voir_panier, name='panier'),
    path('panier/ajouter/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/retirer/<int:item_id>/', views.retirer_du_panier, name='retirer_du_panier'),
    path('panier/modifier/', views.modifier_quantite, name='modifier_quantite'),
    path('panier/confirmer/', views.confirmer_commande, name='confirmer_commande'),

    # Admin panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/profile/', views.admin_profile, name='admin_profile'),
    path('admin-panel/change-password/', AdminPasswordChangeView.as_view(), name='admin_change_password'),
    path('admin-panel/produits/', views.admin_products, name='admin_products'),
    path('admin-panel/produits/nouveau/', views.admin_product_create, name='admin_product_create'),
    path('admin-panel/produits/<int:pk>/modifier/', views.admin_product_update, name='admin_product_update'),
    path('admin-panel/produits/<int:pk>/supprimer/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/categories/', views.admin_categories, name='admin_categories'),
    path('admin-panel/categories/nouvelle/', views.admin_category_create, name='admin_category_create'),
    path('admin-panel/categories/<int:pk>/modifier/', views.admin_category_update, name='admin_category_update'),
    path('admin-panel/categories/<int:pk>/supprimer/', views.admin_category_delete, name='admin_category_delete'),
    path('admin-panel/livreurs/', views.admin_livreurs_list, name='admin_livreurs_list'),
    path('admin-panel/livreurs/nouveau/', views.admin_livreurs_create, name='admin_livreurs_create'),
    path('admin-panel/livreurs/<int:user_id>/modifier/', views.admin_livreurs_edit, name='admin_livreurs_edit'),
    path('admin-panel/livreurs/<int:user_id>/toggle-active/', views.admin_livreurs_toggle_active, name='admin_livreurs_toggle_active'),
    path('admin-panel/clients/', views.admin_clients_list, name='admin_clients_list'),
    path('admin-panel/clients/<int:user_id>/', views.admin_client_detail, name='admin_client_detail'),
    path('admin-panel/clients/<int:user_id>/toggle-active/', views.admin_client_toggle_active, name='admin_client_toggle_active'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    # AJAX
    path('cart-count/', views.cart_count_ajax, name='cart_count_ajax'),

    # Admin Orders
    path('admin-panel/orders/', views.admin_orders_list, name='admin_orders'),
    path('admin-panel/orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/orders/<int:pk>/cancel/', views.admin_cancel_order, name='admin_cancel_order'),

    # Livreur Orders (déplacé plus haut)
    # path('livreur/orders/', views.livreur_orders_list, name='livreur_orders'),
    path('livreur/orders/<int:pk>/', views.livreur_order_detail, name='livreur_order_detail'),
    path('livreur/orders/<int:pk>/accept/', views.livreur_order_accept, name='livreur_order_accept'),
    path('livreur/order/<int:pk>/update-status/', views.livreur_order_update_status, name='livreur_order_update_status'),

    # Avis livraison 
    path('commande/confirmer/', views.confirmer_commande, name='confirmer_commande'),
    path('commande/<int:commande_id>/annuler/', views.annuler_commande, name='annuler_commande'),
    path('commande/<int:commande_id>/avis/', views.donner_avis_livreur, name='donner_avis_livreur'),
    path('calculer-shipping/', views.calculer_shipping, name='calculer_shipping'),

    path('avis-produit/<int:item_id>/', views.donner_avis_produit, name='donner_avis_produit'),
    path('commande/<int:commande_id>/avis/', views.donner_avis_livreur, name='donner_avis_livreur'),

]
