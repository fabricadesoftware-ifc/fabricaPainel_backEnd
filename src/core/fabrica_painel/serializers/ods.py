from rest_framework import serializers
from core.fabrica_painel.models.ods import Ods

class OdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ods
        fields: list[str] = [
            "id",
            "name",
        ]

