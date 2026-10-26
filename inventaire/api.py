from django.core.exceptions import ValidationError as ErreurDjango
from django.db.models.deletion import ProtectedError
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler
from .models import Objet, Capteur, Actionneur, Mesure, Commande, HistoriqueSuppression
from .serializers import (
    ObjetSerializer, CapteurSerializer, ActionneurSerializer, MesureSerializer,
    CommandeSerializer, SuppressionSerializer, InscriptionSerializer,
)
from .services import commander, supprimer_avec_historique

MESSAGES_HTTP = {
    400: 'Données refusées : voir le détail.',
    401: 'Authentification requise : jeton absent ou invalide.',
    403: 'Action interdite pour ce compte.',
    404: 'Ressource introuvable.',
    405: 'Méthode HTTP non autorisée sur cette adresse.',
}


def gestion_erreurs(exc, context):
    """Feedback : chaque erreur JSON contient le code HTTP, un message clair et le détail."""
    reponse = exception_handler(exc, context)
    if reponse is not None:
        reponse.data = {
            'statut': reponse.status_code,
            'message': MESSAGES_HTTP.get(reponse.status_code, 'Erreur.'),
            'detail': reponse.data,
        }
    return reponse


class SuppressionAdminSeulement(permissions.BasePermission):
    """Tout compte connecté peut lire et écrire; seul un administrateur peut supprimer (sinon 403)."""
    message = 'Seul un administrateur peut supprimer.'

    def has_permission(self, request, view):
        if request.method == 'DELETE':
            return bool(request.user and request.user.is_staff)
        return True


class InventaireViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, SuppressionAdminSeulement]

    def create(self, request, *args, **kwargs):
        reponse = super().create(request, *args, **kwargs)
        reponse.data = {'message': 'Fiche créée.', 'donnees': reponse.data}
        return reponse

    def perform_destroy(self, instance):
        try:
            supprimer_avec_historique(instance, self.request.user)
        except ProtectedError:
            raise ValidationError('Suppression refusée : des éléments ou un historique dépendent de cette fiche.')


class ObjetViewSet(InventaireViewSet):
    queryset = Objet.objects.all()
    serializer_class = ObjetSerializer


class CapteurViewSet(InventaireViewSet):
    queryset = Capteur.objects.select_related('objet').all()
    serializer_class = CapteurSerializer


class ActionneurViewSet(InventaireViewSet):
    queryset = Actionneur.objects.select_related('objet').all()
    serializer_class = ActionneurSerializer

    @action(detail=True, methods=['post'])
    def commander(self, request, pk=None):
        element = self.get_object()
        valeur = request.data.get('etat')
        if valeur not in ('on', 'off'):
            raise ValidationError({'etat': 'Utiliser on ou off.'})
        try:
            element = commander(element.pk, request.user, valeur == 'on')
        except ErreurDjango as erreur:
            raise ValidationError(erreur.messages)
        return Response({
            'message': f"{element.nom} : {'Marche' if element.etat else 'Arrêt'} (simulé).",
            **self.get_serializer(element).data,
        })


class MesureViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                    mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Mesure.objects.select_related('capteur', 'capteur__objet').all()
    serializer_class = MesureSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        capteur = self.request.query_params.get('capteur')
        return qs.filter(capteur_id=capteur) if capteur and capteur.isdigit() else qs


class CommandeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Commande.objects.select_related('actionneur', 'utilisateur').all()
    serializer_class = CommandeSerializer


class SuppressionViewSet(viewsets.ReadOnlyModelViewSet):
    """Historique des suppressions : lecture seule, administrateurs uniquement."""
    queryset = HistoriqueSuppression.objects.all()
    serializer_class = SuppressionSerializer
    permission_classes = [permissions.IsAdminUser]


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def inscription(request):
    """Crée un compte UTILISATEUR et renvoie son jeton. Les admins se créent avec createsuperuser
    ou par la page web « Créer un compte » d'un administrateur."""
    serializer = InscriptionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    compte = serializer.save()
    jeton = Token.objects.create(user=compte)
    return Response({'message': f'Compte utilisateur « {compte.username} » créé.',
                     'username': compte.username, 'role': 'utilisateur', 'token': jeton.key},
                    status=status.HTTP_201_CREATED)
