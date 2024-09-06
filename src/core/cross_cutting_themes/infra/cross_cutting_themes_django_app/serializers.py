from rest_framework import serializers
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme

class CrossCuttingThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrossCuttingTheme
        fields: list[str] = [
            "id",
            "name",
            "advisor",
        ]

