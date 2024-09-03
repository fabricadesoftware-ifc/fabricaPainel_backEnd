from rest_framework import serializers
from core.assessment.models import Assessments, Assessment


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


