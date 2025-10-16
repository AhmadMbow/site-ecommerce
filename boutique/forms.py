from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Produit, Categorie, UserProfile, RoleChoices, Adresse

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Adresse e-mail', widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'ex: nom@domaine.com'
    }))
    phone = forms.CharField(max_length=15, required=True, label='Téléphone', widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'ex: 77 123 45 67'
    }))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Adresse (facultatif)'}), required=False, label='Adresse')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone', 'address')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("L'adresse e-mail est obligatoire.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cet e-mail.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError("Le numéro de téléphone est obligatoire.")
        # Nettoyer le numéro de téléphone (enlever les espaces)
        phone = phone.replace(' ', '').replace('-', '')
        if len(phone) < 9:
            raise forms.ValidationError("Le numéro de téléphone doit contenir au moins 9 chiffres.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        # Assure que l'email est bien enregistré et requis
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone': self.cleaned_data.get('phone'),
                    'address': self.cleaned_data.get('address', ''),
                }
            )
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'photo']
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}

class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            cls = f.widget.attrs.get('class', '')
            if isinstance(f.widget, (forms.CheckboxInput,)):
                f.widget.attrs['class'] = (cls + ' form-check-input').strip()
            elif isinstance(f.widget, (forms.Select,)):
                f.widget.attrs['class'] = (cls + ' form-select').strip()
            else:
                f.widget.attrs['class'] = (cls + ' form-control').strip()

class ProduitForm(BootstrapModelForm):
    class Meta:
        model = Produit
        fields = ['nom', 'description', 'prix', 'prix_promo', 'stock', 'image', 'categories']
        labels = {
            'nom': 'Nom du Produit',
            'description': 'Description',
            'prix': 'Prix Normal (FCFA)',
            'prix_promo': 'Prix Promotionnel (FCFA)',
            'stock': 'Quantité en Stock',
            'image': 'Image du Produit',
            'categories': 'Catégories',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Décrivez votre produit...'}),
            'prix': forms.NumberInput(attrs={'min': 0, 'step': 1, 'class': 'form-control', 'placeholder': '0'}),
            'prix_promo': forms.NumberInput(attrs={'min': 0, 'step': 1, 'class': 'form-control', 'placeholder': '0 (optionnel)'}),
            'stock': forms.NumberInput(attrs={'min': 0, 'step': 1, 'class': 'form-control', 'placeholder': '0'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'categories': forms.SelectMultiple(attrs={'size': 6, 'class': 'form-select'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: T-shirt Premium'}),
        }
        help_texts = {
            'prix_promo': 'Laissez vide si pas de promotion',
            'stock': 'Nombre d\'unités disponibles',
            'categories': 'Maintenez Ctrl pour sélectionner plusieurs catégories',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordonner les catégories par nom
        self.fields['categories'].queryset = Categorie.objects.all().order_by('nom')
    
    def clean(self):
        cleaned_data = super().clean()
        prix = cleaned_data.get('prix')
        prix_promo = cleaned_data.get('prix_promo')
        
        # Vérifier que le prix promo est inférieur au prix normal
        if prix and prix_promo and prix_promo >= prix:
            raise forms.ValidationError('Le prix promotionnel doit être inférieur au prix normal.')
        
        return cleaned_data

    def clean(self):
        cleaned = super().clean()
        prix = cleaned.get('prix')
        prix_promo = cleaned.get('prix_promo')
        if prix is not None and prix < 0:
            self.add_error('prix', 'Le prix doit être positif.')
        if prix_promo is not None:
            if prix_promo < 0:
                self.add_error('prix_promo', 'Le prix promo doit être positif.')
            if prix is not None and prix_promo > prix:
                self.add_error('prix_promo', 'Le prix promo ne peut pas dépasser le prix.')
        return cleaned

class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'description', 'icon']
        labels = {
            'nom': 'Nom',
            'description': 'Description',
            'icon': 'Icône (classe FontAwesome)',
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: fa-solid fa-tag'}),
        }

class LivreurCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False, label='Téléphone')
    address = forms.CharField(required=False, label='Adresse', widget=forms.Textarea(attrs={'rows': 2}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone', 'address']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'LIVREUR'
            profile.phone = self.cleaned_data.get('phone') or profile.phone
            profile.address = self.cleaned_data.get('address') or profile.address
            profile.save()
        return user

class DelivererUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class DelivererProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'photo']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

# Formulaires pour la page “Profil Livreur”
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class DelivererProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'photo']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

# Si pas encore présent
class DelivererCreateForm(UserCreationForm):
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}))
    photo = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.create(
                user=user,
                role=RoleChoices.LIVREUR,
                phone=self.cleaned_data.get('phone'),
                address=self.cleaned_data.get('address'),
                photo=self.cleaned_data.get('photo'),
            )
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'photo']  # adapte selon tes champs UserProfile
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse complète'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and photo.size > 2 * 1024 * 1024:
            raise forms.ValidationError("La photo ne peut pas dépasser 2 Mo.")
        return photo

class AdresseForm(forms.ModelForm):
    class Meta:
        model = Adresse
        fields = ['ligne1', 'ligne2', 'ville', 'region', 'code_postal', 'pays', 'telephone']
        widgets = {
            'ligne1': forms.TextInput(attrs={'class': 'form-control'}),
            'ligne2': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'code_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
        }



from .models import AvisLivreur
# ---------------------------
# Formulaire pour AvisLivreur
# ---------------------------
class AvisLivreurForm(forms.ModelForm):
    class Meta:
        model = AvisLivreur
        fields = ['note', 'commentaire']
        widgets = {
            'note': forms.Select(choices=[(i, f"{i}★") for i in range(1, 6)], attrs={'class': 'form-select'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Votre commentaire…'}),
        }