from rest_framework import serializers

from core.fabrica_painel.models.team import Team


class TeamDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields: list[str] = [
            'id',
            'team_student',
        ]


class TeamWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields: list[str] = [
            'team_student',
        ]
