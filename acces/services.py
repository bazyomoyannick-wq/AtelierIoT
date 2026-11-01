from django.utils import timezone
from .models import Acces, Badge


def verifier_acces(porte, uid, lecteur):
    """Décide si le badge ouvre la porte et inscrit la tentative au journal.
    L'UID doit déjà être normalisé et valide."""
    badge = Badge.objects.filter(uid=uid).first()
    if not porte.objet.actif:
        autorise, raison = False, 'Salle fermée : objet désactivé.'
    elif badge is None:
        autorise, raison = False, 'Badge inconnu.'
    elif not badge.actif:
        autorise, raison = False, 'Badge désactivé.'
    elif badge.expire:
        autorise, raison = False, 'Badge expiré.'
    elif not badge.portes.filter(pk=porte.pk).exists():
        autorise, raison = False, 'Badge non autorisé pour cette porte.'
    else:
        autorise, raison = True, f'Bienvenue {badge.titulaire}.'
    return Acces.objects.create(porte=porte, badge=badge, uid_lu=uid, autorise=autorise,
                                raison=raison, lecteur=lecteur)


def refus_derniere_24h():
    return Acces.objects.filter(autorise=False, date__gte=timezone.now() - timezone.timedelta(hours=24)).count()
