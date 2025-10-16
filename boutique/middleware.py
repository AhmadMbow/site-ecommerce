from django.shortcuts import redirect
from django.urls import reverse

class RoleBasedRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # chemins tolérés (ne pas rediriger)
        prefix_whitelist = ('/static/', '/media/', '/admin/')  # admin = Django admin
        # noms d’URL tolérés
        name_whitelist = {'login', 'post_login_redirect', 'admin_logout', 'logout', 'admin_change_password'}

        try:
            allowed_named_paths = {reverse(name) for name in name_whitelist}
        except Exception:
            allowed_named_paths = set()

        if request.user.is_authenticated:
            # ne pas interférer avec les URLs autorisées
            if request.path in allowed_named_paths or any(request.path.startswith(p) for p in prefix_whitelist):
                return self.get_response(request)

            if request.user.is_staff:
                if not request.path.startswith('/admin-panel/'):
                    return redirect('admin_dashboard')
            else:
                # Empêche les non-staff d'accéder à l'admin panel
                if request.path.startswith('/admin-panel/'):
                    return redirect('boutique')

                # Redirection automatique des livreurs vers leur dashboard depuis les pages publiques
                profile = getattr(request.user, 'userprofile', None)
                role = getattr(profile, 'role', '') or ''
                if role.upper() == 'LIVREUR':
                    # éviter boucles: ne pas rediriger si déjà sur une URL livreur
                    if not request.path.startswith('/livreur/'):
                        if request.path in ('/', '/boutique/', '/a-propos/'):
                            return redirect('livreur_dashboard')

        return self.get_response(request)