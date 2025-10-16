# Dans un fichier comme votre_app/utils.py

from django.core.mail import send_mail
from django.conf import settings

def envoyer_mail_statut_commande(commande, statut_precedent=None):
    """
    Envoie un email au client concernant le statut de sa commande.
    """
    # Assurez-vous que l'utilisateur a un email pour l'envoi
    if not commande.user.email:
        print(f"Erreur: L'utilisateur {commande.user.username} n'a pas d'email.")
        return

    # 1. Définition du contenu spécifique au statut
    if commande.statut == 'EN_COURS':
        sujet = f"Mise à jour : Votre commande #{commande.id} est en cours de livraison !"
        message_statut = f"""
**Votre commande est en cours !**
Vous serez contacté pour la livraison qui se fera dans les **prochains 2 jours**.
Le livreur est en route. Vous pouvez suivre sa position en temps réel (si l'interface le permet).
"""
    elif commande.statut == 'LIVREE':
        sujet = f"Commande #{commande.id} livrée avec succès"
        message_statut = "Votre commande a été **livrée** ! Nous espérons que tout vous plaît."
    elif commande.statut == 'ANNULEE':
        sujet = f"Annulation de votre commande #{commande.id}"
        message_statut = "Votre commande a été **annulée** à votre demande ou par nos services."
    elif statut_precedent is None or commande.statut == 'EN_ATTENTE':
        # C'est probablement la première fois que la commande est enregistrée
        sujet = f"Confirmation de votre commande #{commande.id}"
        message_statut = "Nous vous remercions pour votre achat. Votre commande est actuellement en **attente** de traitement."
    else:
        # Aucun changement ou statut non géré
        return

    # 2. Construction du message complet
    message_base = f"""
Bonjour {commande.user.username},

{message_statut}

---
Détails de votre commande :
Numéro de commande : #{commande.id}
Statut actuel : {commande.get_statut_display()}
Date de commande : {commande.date_commande.strftime('%d/%m/%Y à %H:%M')}
Montant total : {commande.total} F CFA

Articles :
"""
    # Ajout de la liste des articles
    items_list = ""
    for item in commande.items.all():
        # Assurez-vous que votre modèle Produit a bien un champ 'nom'
        items_list += f"- {item.quantite}x {item.produit.nom} ({item.prix_unitaire} F CFA / unité)\n"
        
    message_final = f"""{message_base}{items_list}
---
Merci de votre confiance.
L'équipe de [Votre Boutique/Site].
"""

    # 3. Envoi de l'email
    try:
        send_mail(
            sujet,
            message_final,
            settings.EMAIL_HOST_USER,
            [commande.user.email], # Destinataire
            fail_silently=False,
        )
        print(f"Email de statut envoyé pour la commande #{commande.id} à {commande.user.email}")
    except Exception as e:
        # Gérer les erreurs d'envoi (ex: mauvaise configuration SMTP)
        print(f"Erreur lors de l'envoi de l'email pour la commande #{commande.id} : {e}")


def generate_receipt_pdf(commande):
    """
    Génère un PDF de reçu professionnel pour une commande livrée.
    Retourne le contenu du PDF en bytes.
    """
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from datetime import datetime
    
    # Créer un buffer mémoire pour le PDF
    buffer = BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Conteneur pour les éléments du PDF
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#232526'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Style pour les informations
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4a5568'),
        spaceAfter=12
    )
    
    # Style pour les totaux
    total_style = ParagraphStyle(
        'TotalStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#232526'),
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )
    
    # En-tête du reçu
    elements.append(Paragraph("<b>REÇU DE COMMANDE</b>", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Informations de la boutique
    shop_info = f"""
    <b>Maryama Shop</b><br/>
    Boutique E-commerce<br/>
    Email: {settings.DEFAULT_FROM_EMAIL}<br/>
    Téléphone: +221 XX XXX XX XX
    """
    elements.append(Paragraph(shop_info, info_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Ligne de séparation
    elements.append(Spacer(1, 0.3*cm))
    
    # Informations de la commande
    commande_info_data = [
        ['N° Commande:', f'#{commande.id}'],
        ['Date commande:', commande.date_commande.strftime('%d/%m/%Y à %H:%M')],
        ['Statut:', 'LIVRÉE ✓'],
        ['', ''],
        ['<b>CLIENT</b>', ''],
        ['Nom:', commande.user.get_full_name() or commande.user.username],
        ['Email:', commande.user.email],
    ]
    
    # Ajouter l'adresse si disponible
    if commande.adresse_gps:
        commande_info_data.append(['Adresse:', commande.adresse_gps])
        if commande.latitude and commande.longitude:
            commande_info_data.append(
                ['Coordonnées GPS:', f"{commande.latitude}, {commande.longitude}"]
            )
    
    commande_info_table = Table(commande_info_data, colWidths=[4.5*cm, 11*cm])
    commande_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4a5568')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, 4), (-1, 4), 1, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 4), (-1, 4), 12),
    ]))
    
    elements.append(commande_info_table)
    elements.append(Spacer(1, 0.8*cm))
    
    # En-tête du tableau des articles
    elements.append(Paragraph("<b>DÉTAILS DE LA COMMANDE</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.3*cm))
    
    # Tableau des articles
    items_data = [['Article', 'Prix unitaire', 'Quantité', 'Total']]
    
    for item in commande.items.all():
        item_total = item.prix_unitaire * item.quantite
        items_data.append([
            item.produit.nom,
            f"{item.prix_unitaire:,.0f} F CFA",
            str(item.quantite),
            f"{item_total:,.0f} F CFA"
        ])
    
    items_table = Table(items_data, colWidths=[8*cm, 3*cm, 2.5*cm, 3*cm])
    items_table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#232526')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        # Corps du tableau
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#4a5568')),
        # Alignement
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#ffc107')),
        # Alternance de couleurs
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f7fafc')) 
          for i in range(2, len(items_data), 2)]
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Calcul des totaux
    subtotal = sum(item.prix_unitaire * item.quantite for item in commande.items.all())
    
    totals_data = [
        ['Sous-total:', f"{subtotal:,.0f} F CFA"],
        ['Frais de livraison:', f"{getattr(commande, 'frais_livraison', 0):,.0f} F CFA"],
        ['', ''],
        ['<b>TOTAL:</b>', f"<b>{commande.total:,.0f} F CFA</b>"],
    ]
    
    totals_table = Table(totals_data, colWidths=[13*cm, 3.5*cm])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 2), 'Helvetica'),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 11),
        ('FONTSIZE', (0, 3), (-1, 3), 14),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (-1, 2), colors.HexColor('#4a5568')),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#232526')),
        ('LINEABOVE', (0, 3), (-1, 3), 2, colors.HexColor('#ffc107')),
        ('TOPPADDING', (0, 3), (-1, 3), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(totals_table)
    elements.append(Spacer(1, 1*cm))
    
    # Pied de page
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#718096'),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("<b>Merci pour votre confiance !</b>", footer_style))
    elements.append(Paragraph(
        "Ce reçu est généré automatiquement et ne nécessite pas de signature.", 
        footer_style
    ))
    elements.append(Paragraph(
        f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 
        footer_style
    ))
    
    # Construire le PDF
    doc.build(elements)
    
    # Récupérer le contenu du PDF
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


def send_delivery_email_with_receipt(commande):
    """
    Envoie un email au client avec le reçu PDF en pièce jointe.
    """
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    from django.conf import settings
    
    if not commande.user.email:
        print(f"Erreur: L'utilisateur {commande.user.username} n'a pas d'email.")
        return False
    
    try:
        # Générer le PDF
        pdf_content = generate_receipt_pdf(commande)
        
        # Préparer le contexte pour le template email
        context = {
            'commande': commande,
            'client': commande.user,
            'items': commande.items.all(),
        }
        
        # Rendu du template HTML
        html_message = render_to_string('emails/commande_livree.html', context)
        
        # Créer l'email
        subject = f'✅ Commande #{commande.id} livrée - Votre reçu'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [commande.user.email]
        
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=from_email,
            to=recipient_list,
        )
        
        # Définir le contenu comme HTML
        email.content_subtype = 'html'
        
        # Attacher le PDF
        email.attach(
            f'Recu_Commande_{commande.id}.pdf',
            pdf_content,
            'application/pdf'
        )
        
        # Envoyer l'email
        email.send(fail_silently=False)
        
        print(f"✅ Email de livraison avec reçu PDF envoyé pour la commande #{commande.id}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email pour la commande #{commande.id} : {e}")
        import traceback
        traceback.print_exc()
        return False