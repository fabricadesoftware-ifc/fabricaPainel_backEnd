from rest_framework import serializers
from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.cross_cutting_themes.domain.validations.validate_cross_cutting_themes_date import validate_cross_cutting_themes_date_is_valid

class CrossCuttingThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrossCuttingTheme
        fields: list[str] = [
            "id",
            "name",
            "advisor",
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.method == 'PATCH':
            if validate_cross_cutting_themes_date_is_valid():
                raise serializers.ValidationError("Fora da data de inscrição de temas transversais")
        return super().validate(attrs)