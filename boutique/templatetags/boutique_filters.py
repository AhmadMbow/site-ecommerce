"""
Filtres personnalisés pour les templates de la boutique
"""
from django import template

register = template.Library()


@register.filter
def sub(value, arg):
    """Soustrait arg de value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def mul(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divise value par arg"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Calcule le pourcentage de value par rapport à total"""
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0


@register.filter
def economie(prix_normal, prix_promo):
    """Calcule l'économie réalisée"""
    try:
        return float(prix_normal) - float(prix_promo)
    except (ValueError, TypeError):
        return 0
