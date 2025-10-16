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
    icon = models.CharField(max_length=50, default='fas fa-folder')  # FontAwesome par défaut

    def __str__(self):
        return self.nom


class Produit(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=0)
    prix_promo = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    categories = models.ManyToManyField(Categorie, related_name='produits')
    date_creation = models.DateTimeField(auto_now_add=True)

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


    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Latitude GPS du client")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Longitude GPS du client")
    adresse_gps = models.CharField(max_length=255, blank=True, null=True, help_text="Adresse GPS ou texte brut")

    def __str__(self):
        return f"Commande #{self.id} de {self.user.username}"

    @property
    def livreur_avis_donne(self):
        """Retourne True si le client a déjà donné un avis sur ce livreur."""
        from .models import AvisLivreur
        if not self.livreur:
            return True  # Pas de livreur => pas d'avis à donner
        return AvisLivreur.objects.filter(client=self.user, livreur=self.livreur).exists()



class CommandeItem(models.Model):
    commande = models.ForeignKey(Commande, related_name='items', on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantite}x {self.produit.nom}"


# ---------------------------
# Panier
# ---------------------------

class PanierItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='panier_items')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'produit')

    def __str__(self):
        return f"{self.user.username} - {self.produit.nom} ({self.quantite})"

    def prix_total(self):
        prix = self.produit.prix_promo if self.produit.prix_promo else self.produit.prix
        return prix * self.quantite

    def prix_unitaire(self):
        return self.produit.prix_promo if self.produit.prix_promo else self.produit.prix


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
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_support")
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
        return f"{self.sujet} - {self.client.username} ({self.statut})"

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

