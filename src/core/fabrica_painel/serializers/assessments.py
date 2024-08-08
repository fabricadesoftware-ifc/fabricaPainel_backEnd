from rest_framework import serializers
from core.fabrica_painel.models.assessments import Assessments


class AssessmentsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessments
        fields: list[str] = [
            "id",
            "registration",
            "work",
        ]


class AssessmentsWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessments
        fields: list[str] = [
            "registration",
            "work",
        ]