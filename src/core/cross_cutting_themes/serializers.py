from rest_framework import serializers
from core.cross_cutting_themes.models import CrossCuttingTheme

class CrossCuttingThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrossCuttingTheme
        fields: list[str] = [
            "id",
            "name",
            "advisor",
        ]

