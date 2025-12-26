from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.utils import timezone

# ---------------------------
# Catégories et Produits
# ---------------------------

class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default='fas fa-folder', blank=True, null=True)  # FontAwesome (optionnel)
    image = models.ImageField(upload_to='categories/', blank=True, null=True, help_text="Image de la catégorie")

    def __str__(self):
        return self.nom


class Taille(models.Model):
    """Modèle pour les tailles de vêtements (lettres uniquement)"""
    ORDRE_TAILLES = {
        'XS': 1, 'S': 2, 'M': 3, 'L': 4, 'XL': 5, 'XXL': 6, 'XXXL': 7,
    }
    
    nom = models.CharField(max_length=20, unique=True)
    ordre = models.PositiveIntegerField(default=0, help_text="Ordre d'affichage")
    
    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Taille"
        verbose_name_plural = "Tailles"
    
    def __str__(self):
        return self.nom
    
    def save(self, *args, **kwargs):
        # Auto-définir l'ordre basé sur le nom si non défini
        if self.ordre == 0 and self.nom in self.ORDRE_TAILLES:
            self.ordre = self.ORDRE_TAILLES[self.nom]
        super().save(*args, **kwargs)


class Produit(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=0)
    prix_promo = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0, help_text="Stock total (somme des stocks par taille si tailles actives)")
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    categories = models.ManyToManyField(Categorie, related_name='produits')
    date_creation = models.DateTimeField(auto_now_add=True)
    # Nouveau champ pour activer/désactiver les tailles
    a_tailles = models.BooleanField(default=False, help_text="Cocher si ce produit est disponible en plusieurs tailles")

    def __str__(self):
        return self.nom

    @property
    def note_moyenne(self):
        # Utilise 'avis_recus' qui est la relation depuis AvisProduit
        avg = self.avis_recus.aggregate(Avg('note'))['note__avg']
        return avg if avg is not None else 0

    @property
    def nombre_notes(self):
        # Utilise 'avis_recus' qui est la relation depuis AvisProduit
        return self.avis_recus.count()
    
    @property
    def tailles_disponibles(self):
        """Retourne les tailles disponibles (avec stock > 0)"""
        if not self.a_tailles:
            return []
        return self.produit_tailles.filter(stock__gt=0).select_related('taille').order_by('taille__ordre')
    
    @property
    def tailles_en_rupture(self):
        """Retourne le nombre de tailles en rupture de stock"""
        if not self.a_tailles:
            return 0
        return self.produit_tailles.filter(stock=0).count()
    
    @property
    def tailles_stock_bas(self):
        """Retourne le nombre de tailles avec stock bas (entre 1 et 4)"""
        if not self.a_tailles:
            return 0
        return self.produit_tailles.filter(stock__gt=0, stock__lt=5).count()
    
    @property
    def liste_tailles_rupture(self):
        """Retourne la liste des noms de tailles en rupture"""
        if not self.a_tailles:
            return []
        return list(self.produit_tailles.filter(stock=0).values_list('taille__nom', flat=True))
    
    @property
    def liste_tailles_stock_bas(self):
        """Retourne la liste des noms de tailles avec stock bas"""
        if not self.a_tailles:
            return []
        return list(self.produit_tailles.filter(stock__gt=0, stock__lt=5).values_list('taille__nom', flat=True))
    
    @property
    def stock_total(self):
        """Calcule le stock total basé sur les tailles si activé"""
        if self.a_tailles:
            from django.db.models import Sum
            total = self.produit_tailles.aggregate(total=Sum('stock'))['total']
            return total or 0
        return self.stock
    
    def get_stock_pour_taille(self, taille):
        """Retourne le stock pour une taille spécifique"""
        if not self.a_tailles:
            return self.stock
        try:
            pt = self.produit_tailles.get(taille=taille)
            return pt.stock
        except ProduitTaille.DoesNotExist:
            return 0


class ProduitTaille(models.Model):
    """Association entre un produit et ses tailles avec le stock par taille"""
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='produit_tailles')
    taille = models.ForeignKey(Taille, on_delete=models.CASCADE, related_name='produit_tailles')
    stock = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('produit', 'taille')
        ordering = ['taille__ordre']
        verbose_name = "Stock par taille"
        verbose_name_plural = "Stocks par taille"
    
    def __str__(self):
        return f"{self.produit.nom} - {self.taille.nom} ({self.stock} en stock)"


# ---------------------------
# UserProfile
# ---------------------------

class RoleChoices(models.TextChoices):
    CLIENT = 'CLIENT', 'Client'
    LIVREUR = 'LIVREUR', 'Livreur'
    STAFF = 'STAFF', 'Staff'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, default='CLIENT', editable=False)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.CLIENT)
    
    # Champs pour les livreurs - informations véhicule
    vehicle_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Type de véhicule")
    vehicle_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name="Immatriculation")
    vehicle_model = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modèle du véhicule")
    vehicle_color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Couleur du véhicule")

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"


# ---------------------------
# Notes sur produits
# ---------------------------

class Note(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    valeur = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    commentaire = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('produit', 'user')


# ---------------------------
# Commandes et CommandeItem
# ---------------------------

class Commande(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('EN_COURS', 'En cours'),
        ('LIVREE', 'Livrée'),
        ('ANNULEE', 'Annulée'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commandes_client")
    date_commande = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    livreur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commandes_livrees"
    )
    
    # Adresse de livraison (relation vers le modèle Adresse)
    adresse = models.ForeignKey(
        'Adresse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commandes"
    )

    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Latitude GPS du client")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Longitude GPS du client")
    adresse_gps = models.CharField(max_length=255, blank=True, null=True, help_text="Adresse GPS ou texte brut")

    def __str__(self):
        return f"Commande #{self.id} de {self.user.username}"
    
    @property
    def numero_commande(self):
        """Retourne un numéro de commande unique"""
        return f"CMD-{self.id}"
    
    @property
    def type_commande(self):
        """Retourne le type de commande pour les URLs"""
        return "user"

    @property
    def livreur_avis_donne(self):
        """Retourne True si le client a déjà donné un avis sur ce livreur."""
        from .models import AvisLivreur
        if not self.livreur:
            return True  # Pas de livreur => pas d'avis à donner
        return AvisLivreur.objects.filter(client=self.user, livreur=self.livreur).exists()

    @property
    def adresse_livraison_formatee(self):
        """Retourne l'adresse de livraison formatée pour affichage"""
        if self.adresse:
            parts = [self.adresse.ligne1]
            if self.adresse.ligne2:
                parts.append(self.adresse.ligne2)
            parts.append(f"{self.adresse.ville}")
            if self.adresse.region:
                parts.append(self.adresse.region)
            parts.append(self.adresse.pays)
            return ", ".join(parts)
        elif self.adresse_gps:
            return self.adresse_gps
        return "Adresse non renseignée"
    
    @property
    def telephone_client(self):
        """Retourne le téléphone du client (depuis l'adresse ou le profil)"""
        if self.adresse and self.adresse.telephone:
            return self.adresse.telephone
        # Fallback sur le profil utilisateur
        if hasattr(self.user, 'userprofile') and self.user.userprofile.phone:
            return self.user.userprofile.phone
        return None


class CommandeItem(models.Model):
    commande = models.ForeignKey(Commande, related_name='items', on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taille = models.ForeignKey('Taille', on_delete=models.SET_NULL, null=True, blank=True, help_text="Taille sélectionnée pour ce produit")

    def __str__(self):
        taille_str = f" - Taille {self.taille.nom}" if self.taille else ""
        return f"{self.quantite}x {self.produit.nom}{taille_str}"


# ---------------------------
# Commande Invité
# ---------------------------

class CommandeInvite(models.Model):
    """Commandes passées par des visiteurs sans compte"""
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('EN_COURS', 'En cours'),
        ('LIVREE', 'Livrée'),
        ('ANNULEE', 'Annulée'),
    ]
    
    # Informations personnelles
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    
    # Informations de livraison
    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10, blank=True)
    complement_adresse = models.CharField(max_length=255, blank=True)
    
    # Informations GPS
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    adresse_gps = models.CharField(max_length=255, blank=True, null=True)
    
    # Informations de commande
    date_commande = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    
    # Livreur
    livreur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commandes_invites_livrees"
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text="Instructions de livraison ou notes spéciales")
    
    def __str__(self):
        return f"Commande Invité #{self.id} - {self.prenom} {self.nom}"
    
    @property
    def numero_commande(self):
        """Retourne un numéro de commande unique avec préfixe INV"""
        return f"INV-{self.id}"
    
    @property
    def type_commande(self):
        """Retourne le type de commande pour les URLs"""
        return "guest"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def adresse_livraison_formatee(self):
        """Retourne l'adresse de livraison formatée pour affichage"""
        parts = [self.adresse]
        if self.complement_adresse:
            parts.append(self.complement_adresse)
        parts.append(self.ville)
        if self.code_postal:
            parts.append(self.code_postal)
        return ", ".join(parts)
    
    @property
    def telephone_client(self):
        """Retourne le téléphone du client"""
        return self.telephone


class CommandeInviteItem(models.Model):
    """Produits d'une commande invité"""
    commande = models.ForeignKey(CommandeInvite, related_name='items', on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taille = models.ForeignKey('Taille', on_delete=models.SET_NULL, null=True, blank=True, help_text="Taille sélectionnée pour ce produit")

    def __str__(self):
        taille_str = f" - Taille {self.taille.nom}" if self.taille else ""
        return f"{self.quantite}x {self.produit.nom}{taille_str} (Invité)"


# ---------------------------
# Panier
# ---------------------------

class PanierItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='panier_items')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    date_ajout = models.DateTimeField(auto_now_add=True)
    taille = models.ForeignKey('Taille', on_delete=models.SET_NULL, null=True, blank=True, help_text="Taille sélectionnée pour ce produit")

    class Meta:
        # Un utilisateur peut avoir le même produit plusieurs fois s'il a des tailles différentes
        unique_together = ('user', 'produit', 'taille')

    def __str__(self):
        taille_str = f" - Taille {self.taille.nom}" if self.taille else ""
        return f"{self.user.username} - {self.produit.nom}{taille_str} ({self.quantite})"

    def prix_total(self):
        prix = self.produit.prix_promo if self.produit.prix_promo else self.produit.prix
        return prix * self.quantite

    def prix_unitaire(self):
        return self.produit.prix_promo if self.produit.prix_promo else self.produit.prix
    
    @property
    def taille_nom(self):
        """Retourne le nom de la taille ou None"""
        return self.taille.nom if self.taille else None


# ---------------------------
# Adresses
# ---------------------------

class Adresse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='adresses')
    nom = models.CharField(max_length=100, blank=True)
    destinataire = models.CharField(max_length=150, blank=True)
    ligne1 = models.CharField(max_length=255)
    ligne2 = models.CharField(max_length=255, blank=True)
    ville = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True)
    code_postal = models.CharField(max_length=20, blank=True)
    pays = models.CharField(max_length=120, default='Sénégal')
    telephone = models.CharField(max_length=30, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Latitude GPS du client")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Longitude GPS du client")

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        label = self.nom or self.destinataire
        return f"{label} - {self.ligne1}, {self.ville}"


# ---------------------------
# Avis
# ---------------------------

class AvisLivreur(models.Model):
    livreur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avis_recus_livreur")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avis_donnes_livreur")
    note = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    commentaire = models.TextField(blank=True)
    date_avis = models.DateTimeField(default=timezone.now)
    examine = models.BooleanField(default=False, help_text="Marqué comme examiné par l'administrateur")

    class Meta:
        unique_together = ('livreur', 'client')

    def __str__(self):
        return f"Avis de {self.client.username} sur {self.livreur.username} ({self.note}★)"


class AvisProduit(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avis_produits_donnes")
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="avis_recus")
    note = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    commentaire = models.TextField(blank=True)
    date_avis = models.DateTimeField(default=timezone.now)
    examine = models.BooleanField(default=False, help_text="Marqué comme examiné par l'administrateur")

    def __str__(self):
        return f"Avis de {self.client.username} sur {self.produit.nom} ({self.note}★)"

# ---------------------------
# Messagerie Support Client
# ---------------------------

class MessageSupport(models.Model):
    STATUT_CHOICES = [
        ('NOUVEAU', 'Nouveau'),
        ('EN_COURS', 'En cours'),
        ('RESOLU', 'Résolu'),
        ('FERME', 'Fermé'),
    ]
    
    PRIORITE_CHOICES = [
        ('BASSE', 'Basse'),
        ('NORMALE', 'Normale'),
        ('HAUTE', 'Haute'),
        ('URGENTE', 'Urgente'),
    ]
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_support", null=True, blank=True)
    # Pour les visiteurs non connectés
    nom_visiteur = models.CharField(max_length=100, blank=True, null=True)
    sujet = models.CharField(max_length=200)
    message = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='NOUVEAU')
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='NORMALE')
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    lu = models.BooleanField(default=False)
    
    # Informations de contact
    email_contact = models.EmailField(blank=True, null=True)
    telephone_contact = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Message Support"
        verbose_name_plural = "Messages Support"
    
    def __str__(self):
        if self.client:
            return f"{self.sujet} - {self.client.username} ({self.statut})"
        return f"{self.sujet} - {self.nom_visiteur or 'Visiteur'} ({self.statut})"
    
    def get_client_name(self):
        """Retourne le nom du client ou visiteur"""
        if self.client:
            return self.client.get_full_name() or self.client.username
        return self.nom_visiteur or 'Visiteur'

class ReponseSupport(models.Model):
    message = models.ForeignKey(MessageSupport, on_delete=models.CASCADE, related_name="reponses")
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_reponse = models.DateTimeField(default=timezone.now)
    est_admin = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['date_reponse']
        verbose_name = "Réponse Support"
        verbose_name_plural = "Réponses Support"
    
    def __str__(self):
        return f"Réponse de {self.auteur.username} le {self.date_reponse.strftime('%d/%m/%Y')}"


# ---------------------------
# Notifications Admin Vues
# ---------------------------

class NotificationAdminVue(models.Model):
    """
    Modèle pour tracker les notifications vues par les administrateurs
    """
    TYPE_CHOICES = [
        ('NOUVEAU_CLIENT', 'Nouveau Client'),
        ('NOUVELLE_COMMANDE', 'Nouvelle Commande'),
        ('NOUVELLE_COMMANDE_INVITE', 'Nouvelle Commande Invité'),
        ('NOUVEAU_MESSAGE', 'Nouveau Message'),
        ('AVIS_PRODUIT', 'Avis Produit'),
        ('AVIS_LIVREUR', 'Avis Livreur'),
        ('RUPTURE_STOCK', 'Rupture de Stock'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_vues')
    type_notification = models.CharField(max_length=30, choices=TYPE_CHOICES)
    objet_id = models.IntegerField(help_text="ID de l'objet concerné (User, Commande, etc.)")
    date_vue = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['admin', 'type_notification', 'objet_id']
        ordering = ['-date_vue']
        verbose_name = "Notification Admin Vue"
        verbose_name_plural = "Notifications Admin Vues"
    
    def __str__(self):
        return f"{self.admin.username} - {self.type_notification} #{self.objet_id}"

