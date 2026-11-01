from rest_framework import serializers
from inventaire.serializers import SerializerValide
from .models import Acces, Badge, Porte, normaliser_uid


class PorteSerializer(SerializerValide):
    class Meta:
        model = Porte
        fields = ['id', 'nom', 'objet', 'duree_ouverture']


class BadgeSerializer(SerializerValide):
    # Accepte « 04 A2 3B ... » (avec espaces) : la longueur est vérifiée après normalisation.
    uid = serializers.CharField(max_length=30)
    portes = serializers.PrimaryKeyRelatedField(queryset=Porte.objects.all(), many=True, required=False)

    class Meta:
        model = Badge
        fields = ['id', 'uid', 'titulaire', 'actif', 'expiration', 'portes']

    def validate_uid(self, valeur):
        return normaliser_uid(valeur)

    def validate(self, attrs):
        portes = attrs.pop('portes', None)   # full_clean() ne gère pas le ManyToMany
        attrs = super().validate(attrs)
        if portes is not None:
            attrs['portes'] = portes
        return attrs


class AccesSerializer(serializers.ModelSerializer):
    porte_nom = serializers.CharField(source='porte.nom', read_only=True)
    titulaire = serializers.CharField(source='badge.titulaire', read_only=True, default=None)

    class Meta:
        model = Acces
        fields = ['id', 'porte', 'porte_nom', 'uid_lu', 'titulaire', 'autorise', 'raison', 'date']
        read_only_fields = fields
