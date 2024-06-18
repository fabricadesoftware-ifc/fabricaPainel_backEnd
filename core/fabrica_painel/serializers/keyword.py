from rest_framework import serializers

from core.fabrica_painel.models.keyword import Keyword


class KeywordDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields: list[str] = [
            'id',
            'name',
            'work'
        ]


class KeywordWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields: list[str] = [
            'name',
            'work',
        ]
