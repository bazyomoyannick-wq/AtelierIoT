from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Objet(models.Model):
    nom = models.CharField(max_length=80, unique=True)
    emplacement = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Capteur(models.Model):
    # Pas de température ni d'humidité : luminosité (photorésistance) et distance (HC-SR04).
    TYPES = [('luminosite', 'Luminosité'), ('distance', 'Distance')]
    UNITES = {'luminosite': 'lux', 'distance': 'cm'}
    BORNES = {'luminosite': (0, 10000), 'distance': (2, 400)}

    objet = models.ForeignKey(Objet, on_delete=models.PROTECT, related_name='capteurs')
    nom = models.CharField(max_length=80, unique=True)
    type_mesure = models.CharField(max_length=20, choices=TYPES)
    seuil_alerte = models.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        ordering = ['nom']

    @property
    def unite(self):
        return self.UNITES.get(self.type_mesure, '')

    @property
    def bornes(self):
        return self.BORNES.get(self.type_mesure, (0, 0))

    def clean(self):
        if self.seuil_alerte is not None and self.type_mesure:
            bas, haut = self.bornes
            if not bas <= self.seuil_alerte <= haut:
                raise ValidationError({'seuil_alerte': f'Choisir une valeur entre {bas} et {haut}.'})
        if self.pk and self.mesures.exists():
            ancien = Capteur.objects.get(pk=self.pk)
            if ancien.type_mesure != self.type_mesure or ancien.objet_id != self.objet_id:
                raise ValidationError('Avec un historique, le type et l’objet du capteur sont fixes.')

    def __str__(self):
        return f'{self.nom} ({self.unite})'


class Actionneur(models.Model):
    objet = models.ForeignKey(Objet, on_delete=models.PROTECT, related_name='actionneurs')
    nom = models.CharField(max_length=80, unique=True)
    type_action = models.CharField(max_length=20, choices=[
        ('lampe', 'Lampe (DEL)'), ('barriere', 'Barrière (servomoteur)'), ('avertisseur', 'Avertisseur'),
    ])
    etat = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ['nom']

    def clean(self):
        if self.pk and self.commandes.exists():
            ancien = Actionneur.objects.get(pk=self.pk)
            if ancien.objet_id != self.objet_id or ancien.type_action != self.type_action:
                raise ValidationError('Avec un historique, le type et l’objet de l’actionneur sont fixes.')

    def __str__(self):
        return self.nom


class Mesure(models.Model):
    capteur = models.ForeignKey(Capteur, on_delete=models.PROTECT, related_name='mesures')
    valeur = models.DecimalField(max_digits=7, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    @property
    def en_alerte(self):
        return self.valeur < self.capteur.seuil_alerte

    def clean(self):
        if self.capteur_id:
            if not self.capteur.objet.actif:
                raise ValidationError({'capteur': 'Cet objet est désactivé.'})
            bas, haut = self.capteur.bornes
            if self.valeur is not None and not bas <= self.valeur <= haut:
                raise ValidationError({'valeur': f'Valeur attendue entre {bas} et {haut} {self.capteur.unite}.'})


class Commande(models.Model):
    actionneur = models.ForeignKey(Actionneur, on_delete=models.PROTECT, related_name='commandes')
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    etat_demande = models.BooleanField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']


class HistoriqueSuppression(models.Model):
    """Trace de chaque suppression : quoi, quelles données, qui et quand."""
    type_element = models.CharField(max_length=20)
    element_id = models.PositiveIntegerField()
    nom = models.CharField(max_length=80)
    donnees = models.JSONField()
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                    on_delete=models.SET_NULL, related_name='suppressions')
    nom_utilisateur = models.CharField(max_length=150)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f'{self.type_element} « {self.nom} » supprimé par {self.nom_utilisateur}'
