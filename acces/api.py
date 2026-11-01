from django.core.exceptions import ValidationError as ErreurDjango
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from inventaire.services import supprimer_avec_historique
from .models import Acces, Badge, Porte, normaliser_uid, valider_uid
from .serializers import AccesSerializer, BadgeSerializer, PorteSerializer
from .services import verifier_acces


class LectureOuAdmin(permissions.BasePermission):
    """Lecture pour tout compte connecté; création, modification et suppression pour l'admin."""
    message = 'Réservé aux administrateurs.'

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or bool(request.user and request.user.is_staff)


class SuppressionTracee:
    def perform_destroy(self, instance):
        try:
            supprimer_avec_historique(instance, self.request.user)
        except ProtectedError:
            raise ValidationError('Suppression refusée : un historique d’accès dépend de cette fiche.')


class PorteViewSet(SuppressionTracee, viewsets.ModelViewSet):
    queryset = Porte.objects.select_related('objet')
    serializer_class = PorteSerializer
    permission_classes = [permissions.IsAuthenticated, LectureOuAdmin]


class BadgeViewSet(SuppressionTracee, viewsets.ModelViewSet):
    """Les badges sont des données sensibles : tout est réservé à l'admin."""
    queryset = Badge.objects.prefetch_related('portes')
    serializer_class = BadgeSerializer
    permission_classes = [permissions.IsAdminUser]


class JournalAccesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Acces.objects.select_related('porte', 'badge')
    serializer_class = AccesSerializer


@api_view(['POST'])
def passage_badge(request):
    """Appelé par le lecteur RFID : {"porte": 1, "uid": "A35F129C"}.
    200 = ouvrir; 403 = refuser; 400 = données invalides; 404 = porte inconnue."""
    porte_id = request.data.get('porte')
    uid = normaliser_uid(request.data.get('uid'))
    erreurs = {}
    if not str(porte_id).isdigit():
        erreurs['porte'] = ['Identifiant de porte entier requis.']
    try:
        valider_uid(uid)
    except ErreurDjango as erreur:
        erreurs['uid'] = erreur.messages
    if erreurs:
        raise ValidationError(erreurs)
    porte = get_object_or_404(Porte.objects.select_related('objet'), pk=int(porte_id))
    acces = verifier_acces(porte, uid, request.user)
    reponse = {
        'statut': 200 if acces.autorise else 403,
        'autorise': acces.autorise,
        'message': ('Accès autorisé : ' if acces.autorise else 'Accès refusé : ') + acces.raison,
        'ouvrir_secondes': porte.duree_ouverture if acces.autorise else 0,
        'acces_id': acces.id,
    }
    return Response(reponse, status=status.HTTP_200_OK if acces.autorise else status.HTTP_403_FORBIDDEN)
