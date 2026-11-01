from django import forms
from .models import Badge, Porte, normaliser_uid, valider_uid

MOTIF_UID = r'^\s*([0-9A-Fa-f]{2}[\s:]?){3}[0-9A-Fa-f]{2}\s*$|^\s*([0-9A-Fa-f]{2}[\s:]?){6}[0-9A-Fa-f]{2}\s*$'
AIDE_UID = 'Ex. A35F129C ou A3 5F 12 9C (4 ou 7 octets en hexadécimal).'


class BadgeForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = ['uid', 'titulaire', 'actif', 'expiration', 'portes']
        widgets = {
            # Validation côté utilisateur : le navigateur refuse un UID mal formé.
            'uid': forms.TextInput(attrs={'pattern': MOTIF_UID, 'title': AIDE_UID, 'required': True}),
            'expiration': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'portes': forms.CheckboxSelectMultiple,
        }
        help_texts = {'uid': AIDE_UID}


class PorteForm(forms.ModelForm):
    class Meta:
        model = Porte
        fields = ['nom', 'objet', 'duree_ouverture']
        widgets = {'duree_ouverture': forms.NumberInput(attrs={'min': 1, 'max': 30})}


class TestBadgeForm(forms.Form):
    porte = forms.ModelChoiceField(queryset=Porte.objects.all())
    uid = forms.CharField(label='UID lu par le lecteur', help_text=AIDE_UID,
                          widget=forms.TextInput(attrs={'pattern': MOTIF_UID, 'title': AIDE_UID}))

    def clean_uid(self):
        uid = normaliser_uid(self.cleaned_data['uid'])
        valider_uid(uid)
        return uid
