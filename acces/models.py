import re
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from inventaire.models import Objet

# Un UID MIFARE fait 4 ou 7 octets : 8 ou 14 caractères hexadécimaux.
FORMAT_UID = re.compile(r'^([0-9A-F]{8}|[0-9A-F]{14})$')


def normaliser_uid(uid):
    """« a3 5f:12 9c » devient « A35F129C » (espaces et deux-points retirés, majuscules)."""
    return re.sub(r'[\s:]', '', str(uid or '')).upper()


def valider_uid(uid):
    if not FORMAT_UID.match(uid):
        raise ValidationError('UID invalide : 4 ou 7 octets en hexadécimal (ex. A35F129C).')


class Porte(models.Model):
    nom = models.CharField(max_length=80, unique=True)
    objet = models.ForeignKey(Objet, on_delete=models.PROTECT, related_name='portes',
                              help_text='Salle ou objet protégé par cette porte.')
    duree_ouverture = models.PositiveSmallIntegerField(default=5, help_text='Secondes (1 à 30).')

    class Meta:
        ordering = ['nom']

    def clean(self):
        if self.duree_ouverture is not None and not 1 <= self.duree_ouverture <= 30:
            raise ValidationError({'duree_ouverture': 'Choisir entre 1 et 30 secondes.'})

    def __str__(self):
        return self.nom


class Badge(models.Model):
    uid = models.CharField('UID', max_length=14, unique=True)
    titulaire = models.CharField(max_length=80)
    actif = models.BooleanField(default=True)
    expiration = models.DateField(null=True, blank=True, help_text='Vide = sans expiration.')
    portes = models.ManyToManyField(Porte, blank=True, related_name='badges',
                                    help_text='Portes que ce badge peut ouvrir.')

    class Meta:
        ordering = ['titulaire']

    @property
    def nom(self):
        return f'{self.titulaire} ({self.uid})'

    @property
    def expire(self):
        return self.expiration is not None and self.expiration < timezone.localdate()

    def clean(self):
        self.uid = normaliser_uid(self.uid)
        valider_uid(self.uid)

    def __str__(self):
        return self.nom


class Acces(models.Model):
    """Journal de chaque passage de badge, accepté ou refusé."""
    porte = models.ForeignKey(Porte, on_delete=models.PROTECT, related_name='acces')
    badge = models.ForeignKey(Badge, null=True, blank=True, on_delete=models.SET_NULL, related_name='acces')
    uid_lu = models.CharField(max_length=14)
    autorise = models.BooleanField()
    raison = models.CharField(max_length=120)
    lecteur = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name_plural = 'accès'
