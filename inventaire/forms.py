from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Objet, Capteur, Actionneur, Mesure


class ObjetForm(forms.ModelForm):
    class Meta:
        model = Objet
        fields = ['nom', 'emplacement', 'description', 'actif']
        # Validation côté utilisateur : le navigateur bloque un nom vide ou trop long.
        widgets = {'nom': forms.TextInput(attrs={'required': True, 'maxlength': 80})}


class CapteurForm(forms.ModelForm):
    class Meta:
        model = Capteur
        fields = ['objet', 'nom', 'type_mesure', 'seuil_alerte']
        widgets = {'seuil_alerte': forms.NumberInput(attrs={'min': 0, 'max': 10000, 'step': '0.01'})}


class ActionneurForm(forms.ModelForm):
    class Meta:
        model = Actionneur
        fields = ['objet', 'nom', 'type_action']


class MesureForm(forms.ModelForm):
    class Meta:
        model = Mesure
        fields = ['capteur', 'valeur']
        # min/max sont ajustés en JavaScript selon le capteur choisi (voir mesures.html).
        widgets = {'valeur': forms.NumberInput(attrs={'min': 0, 'max': 10000, 'step': '0.01'})}


class InscriptionForm(UserCreationForm):
    """Création d'un compte. Seul un administrateur connecté peut cocher « administrateur »."""
    administrateur = forms.BooleanField(required=False, label='Compte administrateur')

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'email']

    def __init__(self, *args, peut_creer_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not peut_creer_admin:
            del self.fields['administrateur']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data.get('administrateur', False)
        if commit:
            user.save()
        return user
