from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Actionneur, Commande, HistoriqueSuppression

TYPES_ELEMENTS = {'Objet': 'objets', 'Capteur': 'capteurs', 'Actionneur': 'actionneurs'}


@transaction.atomic
def commander(actionneur_id, utilisateur, etat):
    actionneur = Actionneur.objects.select_for_update().get(pk=actionneur_id)
    if not actionneur.objet.actif:
        raise ValidationError('Objet désactivé : commande refusée.')
    actionneur.etat = etat
    actionneur.save(update_fields=['etat'])
    Commande.objects.create(actionneur=actionneur, utilisateur=utilisateur, etat_demande=etat)
    return actionneur


@transaction.atomic
def supprimer_avec_historique(element, utilisateur):
    """Supprime une fiche et garde une trace (données, auteur, date).
    Si la suppression est bloquée (ProtectedError), rien n'est écrit dans l'historique."""
    donnees = json.loads(json.dumps(model_to_dict(element), cls=DjangoJSONEncoder))
    type_element = TYPES_ELEMENTS.get(type(element).__name__, type(element).__name__)
    element_id, nom = element.pk, str(getattr(element, 'nom', element))
    element.delete()
    return HistoriqueSuppression.objects.create(
        type_element=type_element, element_id=element_id, nom=nom, donnees=donnees,
        utilisateur=utilisateur, nom_utilisateur=utilisateur.username,
    )
