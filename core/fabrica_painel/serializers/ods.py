from rest_framework import serializers
from core.fabrica_painel.models.ods import SustainableGoals

class SustainableGoalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SustainableGoals
        fields: list[str] = [
            "id",
            "name",
        ]

