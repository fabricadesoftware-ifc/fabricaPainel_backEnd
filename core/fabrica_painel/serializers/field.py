from rest_framework import serializers
from core.fabrica_painel.models.field import Field


class FieldDetailSerializer(serializers.ModelSerializer):
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