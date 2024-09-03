from rest_framework import serializers
from core.field.models import Field

class FieldRetriveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields: list[str] = [
            "id",
            "name",
        ]


class FieldWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields: list[str] = [
            "name",
        ]
