"""
Utilitaires pour les emails avec template SadibouShop
"""
from django.conf import settings


def get_email_logo_base64():
    """
    Retourne le logo SadibouShop en base64 pour les emails.
    Le logo est encodé directement pour éviter les problèmes de chargement d'images.
    """
    # Logo SVG simplifié encodé en base64 pour les emails
    # Note: Les clients email ne supportent pas tous le SVG, donc on utilise une version inline
    return None  # On utilisera une approche différente


def get_email_header_html(title=""):
    """
    Génère le header HTML pour les emails avec le logo SadibouShop.
    Utilise un design compatible avec tous les clients email.
    """
    return f'''
    <!-- Header avec Logo -->
    <tr>
        <td style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 25px 30px; text-align: center;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                    <td align="center">
                        <!-- Logo texte stylisé -->
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto;">
                            <tr>
                                <td style="padding-right: 12px; vertical-align: middle;">
                                    <!-- Icône cintre stylisée -->
                                    <div style="width: 45px; height: 45px; background: linear-gradient(135deg, #ffc107 0%, #e6ac00 100%); border-radius: 10px; display: inline-block; text-align: center; line-height: 45px;">
                                        <span style="font-size: 24px; color: #1a1a1a;">👔</span>
                                    </div>
                                </td>
                                <td style="vertical-align: middle;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 0.5px;">
                                        SADIBOU<span style="color: #ffc107;">SHOP</span>
                                    </h1>
                                    <p style="color: #888888; margin: 2px 0 0 0; font-size: 10px; letter-spacing: 2px; text-transform: uppercase;">
                                        Mode & Tendances
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    '''


def get_email_footer_html():
    """
    Génère le footer HTML pour les emails SadibouShop.
    """
    return f'''
    <!-- Footer -->
    <tr>
        <td style="background-color: #1a1a1a; padding: 25px 30px; text-align: center;">
            <p style="color: #ffc107; font-size: 16px; font-weight: 700; margin: 0 0 5px 0;">
                SADIBOU<span style="color: #ffffff;">SHOP</span>
            </p>
            <p style="color: #888888; font-size: 11px; margin: 0 0 15px 0; letter-spacing: 1px;">
                MODE & TENDANCES
            </p>
            <p style="color: #666666; font-size: 12px; line-height: 1.6; margin: 0;">
                Votre boutique de mode en ligne<br>
                Contact: {settings.DEFAULT_FROM_EMAIL}
            </p>
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #333;">
                <p style="color: #555555; font-size: 10px; margin: 0;">
                    © 2024 SadibouShop. Tous droits réservés.
                </p>
            </div>
        </td>
    </tr>
    '''


def get_email_template(subject, content_html, show_cta=True, cta_text="Visiter notre boutique", cta_url="https://sadiboushop.com"):
    """
    Génère un template email complet avec header, contenu et footer.
    
    Args:
        subject: Sujet de l'email
        content_html: Contenu HTML de l'email (le corps du message)
        show_cta: Afficher ou non le bouton d'action
        cta_text: Texte du bouton d'action
        cta_url: URL du bouton d'action
    
    Returns:
        str: Template HTML complet
    """
    cta_html = ""
    if show_cta:
        cta_html = f'''
        <!-- CTA Button -->
        <tr>
            <td style="padding: 25px 30px; text-align: center;">
                <a href="{cta_url}" style="display: inline-block; background: linear-gradient(135deg, #ffc107 0%, #e6ac00 100%); color: #1a1a1a; text-decoration: none; padding: 14px 40px; border-radius: 8px; font-weight: 700; font-size: 15px; box-shadow: 0 4px 15px rgba(255,193,7,0.3);">
                    {cta_text}
                </a>
            </td>
        </tr>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, Helvetica, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    {get_email_header_html(subject)}
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 35px 30px;">
                            {content_html}
                        </td>
                    </tr>
                    
                    {cta_html}
                    
                    {get_email_footer_html()}
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
