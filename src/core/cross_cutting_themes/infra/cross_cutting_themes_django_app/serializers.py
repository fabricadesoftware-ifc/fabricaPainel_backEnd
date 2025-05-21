from rest_framework import serializers

from core.cross_cutting_themes.infra.cross_cutting_themes_django_app.models import CrossCuttingTheme
from core.cross_cutting_themes.domain.validations import validate_cross_cutting_themes_date_is_valid, validate_cross_cutting_themes_is_advisor


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
            try:
                validate_cross_cutting_themes_date_is_valid()
            except Exception as e:
                raise e
            try:
                validate_cross_cutting_themes_is_advisor(attrs.get('advisor'))
            except Exception as e:
                raise e
        return super().validate(attrs)
