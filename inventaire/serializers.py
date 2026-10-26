from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ErreurDjango
from rest_framework import serializers
from .models import Objet, Capteur, Actionneur, Mesure, Commande, HistoriqueSuppression


class SerializerValide(serializers.ModelSerializer):
    """Validation côté serveur : réutilise les règles clean() des modèles pour l'API."""
    def validate(self, attrs):
        model = self.Meta.model
        instance = self.instance or model()
        for cle, valeur in attrs.items():
            setattr(instance, cle, valeur)
        try:
            instance.full_clean()
        except ErreurDjango as erreur:
            detail = erreur.message_dict if hasattr(erreur, 'message_dict') else erreur.messages
            raise serializers.ValidationError(detail)
        return attrs


class ObjetSerializer(SerializerValide):
    class Meta:
        model = Objet
        fields = ['id', 'nom', 'emplacement', 'description', 'actif']


class CapteurSerializer(SerializerValide):
    unite = serializers.ReadOnlyField()

    class Meta:
        model = Capteur
        fields = ['id', 'objet', 'nom', 'type_mesure', 'seuil_alerte', 'unite']


class ActionneurSerializer(SerializerValide):
    class Meta:
        model = Actionneur
        fields = ['id', 'objet', 'nom', 'type_action', 'etat']
        read_only_fields = ['etat']


class MesureSerializer(SerializerValide):
    en_alerte = serializers.ReadOnlyField()

    class Meta:
        model = Mesure
        fields = ['id', 'capteur', 'valeur', 'date', 'en_alerte']
        read_only_fields = ['date']


class CommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = ['id', 'actionneur', 'utilisateur', 'etat_demande', 'date']
        read_only_fields = fields


class SuppressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriqueSuppression
        fields = ['id', 'type_element', 'element_id', 'nom', 'donnees', 'nom_utilisateur', 'date']
        read_only_fields = fields


class InscriptionSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password']

    def validate_password(self, valeur):
        try:
            validate_password(valeur)
        except ErreurDjango as erreur:
            raise serializers.ValidationError(erreur.messages)
        return valeur

    def create(self, donnees):
        return get_user_model().objects.create_user(**donnees)
