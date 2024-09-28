from rest_framework import serializers
from core.field.infra.field_django_app.models import Field

class FieldRetriveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields: list[str] = [
            "id",
            "name",
        ]
        depth = 1


class FieldWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields: list[str] = [
            "name",
        ]
    depth = 1