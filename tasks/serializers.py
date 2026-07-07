from rest_framework import serializers
from .models import Semaine, Tache, SousTache


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

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'description', 'status', 'status_display',
            'priorite', 'priorite_display', 'semaine', 'assigne_a',
            'assigne_a_nom', 'date_creation', 'date_debut_prevue',
            'date_fin_prevue', 'date_realisation',
            'sous_taches_count', 'sous_taches_terminees'
        ]

    def get_sous_taches_terminees(self, obj):
        return obj.sous_taches.filter(status='completed').count()


class TacheDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    priorite_display = serializers.CharField(
        source='get_priorite_display', read_only=True
    )
    assigne_a = serializers.SerializerMethodField()
    sous_taches = SousTacheSerializer(many=True, read_only=True)

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'description', 'status', 'status_display',
            'priorite', 'priorite_display', 'semaine', 'assigne_a',
            'created_by', 'date_creation', 'date_modification',
            'date_debut_prevue', 'date_fin_prevue', 'date_realisation',
            'sous_taches'
        ]
        read_only_fields = ['created_by', 'date_creation']

    def get_assigne_a(self, obj):
        return {
            'id': obj.assigne_a.id,
            'nom': obj.assigne_a.get_full_name() or obj.assigne_a.username,
            'username': obj.assigne_a.username
        }


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
