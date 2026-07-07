from rest_framework import serializers
from .models import RapportExecution


class RapportExecutionSerializer(serializers.ModelSerializer):
    type_rapport_display = serializers.CharField(
        source='get_type_rapport_display', read_only=True
    )
    categorie_raison_display = serializers.CharField(
        source='get_categorie_raison_display', read_only=True
    )
    agent_nom = serializers.CharField(
        source='agent.get_full_name', read_only=True
    )
    tache_titre = serializers.CharField(
        source='tache.titre', read_only=True
    )
    sous_tache_titre = serializers.CharField(
        source='sous_tache.titre', read_only=True
    )

    class Meta:
        model = RapportExecution
        fields = [
            'id', 'tache', 'tache_titre', 'sous_tache', 'sous_tache_titre',
            'agent', 'agent_nom', 'type_rapport', 'type_rapport_display',
            'commentaire', 'photo', 'raison_non_execution',
            'categorie_raison', 'categorie_raison_display',
            'date_soumission', 'latitude', 'longitude'
        ]
        read_only_fields = ['agent', 'date_soumission']

    def validate(self, data):
        # Validation: soit tache soit sous_tache doit être fourni
        if not data.get('tache') and not data.get('sous_tache'):
            raise serializers.ValidationError(
                "Vous devez fournir une tâche ou une sous-tâche."
            )

        # Si type_rapport est 'non_execution', une raison est requise
        if (data.get('type_rapport') == 'non_execution'
                and not data.get('raison_non_execution')):
            raise serializers.ValidationError(
                "Une raison est requise pour une non-exécution."
            )

        return data

    def create(self, validated_data):
        validated_data['agent'] = self.context['request'].user
        return super().create(validated_data)
