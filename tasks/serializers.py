from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Semaine, Tache, SousTache, ImportLot, Notification


def _donnees_excel_pour_utilisateur(tache, request):
    """
    Renvoie les colonnes Excel additionnelles d'une tâche, filtrées selon
    le rôle de l'utilisateur :
    - admin/manager : voient toutes les colonnes importées (dashboard/suivi)
    - agent         : ne voit que les colonnes marquées "visibles mobile"
                      par le superviseur au moment de l'import
    """
    donnees = tache.donnees_excel or {}
    if not donnees:
        return {}

    user = getattr(request, 'user', None)
    if user and getattr(user, 'role', None) in ('admin', 'manager'):
        return donnees

    if tache.lot_import_id:
        colonnes_visibles = tache.lot_import.colonnes_visibles_mobile or []
        return {k: v for k, v in donnees.items() if k in colonnes_visibles}

    # Pas de lot d'import (tâche créée manuellement) : rien à filtrer
    return {}


class SemaineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semaine
        fields = [
            'id', 'numero', 'annee',
            'date_debut', 'date_fin', 'is_active'
        ]


class SousTacheSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = SousTache
        fields = [
            'id', 'tache', 'titre', 'description',
            'status', 'status_display', 'ordre', 'date_realisation'
        ]
        read_only_fields = ['tache']


class TacheListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    priorite_display = serializers.CharField(
        source='get_priorite_display', read_only=True
    )
    assigne_a_nom = serializers.CharField(
        source='assigne_a.get_full_name', read_only=True
    )
    sous_taches_count = serializers.IntegerField(
        source='sous_taches.count', read_only=True
    )
    sous_taches_terminees = serializers.SerializerMethodField()
    donnees_visibles = serializers.SerializerMethodField()

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'description', 'status', 'status_display',
            'priorite', 'priorite_display', 'semaine', 'assigne_a',
            'assigne_a_nom', 'date_creation', 'date_debut_prevue',
            'date_fin_prevue', 'date_realisation',
            'sous_taches_count', 'sous_taches_terminees', 'donnees_visibles'
        ]

    def get_sous_taches_terminees(self, obj) -> int:
        return obj.sous_taches.filter(status='completed').count()

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_donnees_visibles(self, obj):
        return _donnees_excel_pour_utilisateur(obj, self.context.get('request'))


class TacheDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    priorite_display = serializers.CharField(
        source='get_priorite_display', read_only=True
    )
    assigne_a = serializers.SerializerMethodField()
    sous_taches = SousTacheSerializer(many=True, read_only=True)
    donnees_visibles = serializers.SerializerMethodField()

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'description', 'status', 'status_display',
            'priorite', 'priorite_display', 'semaine', 'assigne_a',
            'created_by', 'date_creation', 'date_modification',
            'date_debut_prevue', 'date_fin_prevue', 'date_realisation',
            'sous_taches', 'donnees_visibles'
        ]
        read_only_fields = ['created_by', 'date_creation']

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_assigne_a(self, obj):
        return {
            'id': obj.assigne_a.id,
            'nom': obj.assigne_a.get_full_name() or obj.assigne_a.username,
            'username': obj.assigne_a.username
        }

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_donnees_visibles(self, obj):
        return _donnees_excel_pour_utilisateur(obj, self.context.get('request'))


class TacheCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'description', 'semaine',
            'assigne_a', 'status', 'priorite',
            'date_debut_prevue', 'date_fin_prevue'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ImportLotSerializer(serializers.ModelSerializer):
    importe_par_nom = serializers.CharField(
        source='importe_par.get_full_name', read_only=True, default=''
    )
    semaine_label = serializers.CharField(source='semaine.__str__', read_only=True)
    taux_reussite = serializers.SerializerMethodField()

    class Meta:
        model = ImportLot
        fields = [
            'id', 'nom_fichier', 'semaine', 'semaine_label',
            'importe_par', 'importe_par_nom', 'toutes_colonnes',
            'colonnes_obligatoires', 'colonnes_visibles_mobile', 'mapping',
            'date_import', 'nombre_taches_creees', 'nombre_erreurs',
            'taux_reussite',
        ]

    def get_taux_reussite(self, obj):
        total = obj.nombre_taches_creees + obj.nombre_erreurs
        if total == 0:
            return None
        return round(obj.nombre_taches_creees / total * 100, 1)


class NotificationSerializer(serializers.ModelSerializer):
    type_notification_display = serializers.CharField(
        source='get_type_notification_display', read_only=True
    )
    tache_titre = serializers.CharField(source='tache.titre', read_only=True, default=None)

    class Meta:
        model = Notification
        fields = [
            'id', 'type_notification', 'type_notification_display',
            'message', 'tache', 'tache_titre', 'lu', 'date_creation'
        ]
        read_only_fields = ['type_notification', 'message', 'tache', 'date_creation']