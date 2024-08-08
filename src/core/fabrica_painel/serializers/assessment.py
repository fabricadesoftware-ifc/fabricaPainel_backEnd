from rest_framework import serializers
from core.fabrica_painel.models.assessment import Assessment


class AssessmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields: list[str] = [
            "id",
            "registration",
            "work",
            "grade",
            "evaluator",
            "date_time",
            "committee_feedback",
            "student_feedback",
        ]

class AssessmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields: list[str] = [
            "registration",
            "work",
            "grade",
            "evaluator",
            "date_time",
            "committee_feedback",
            "student_feedback",
        ]


