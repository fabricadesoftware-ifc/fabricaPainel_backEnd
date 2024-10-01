from rest_framework import serializers
from core.assessment.infra.assessment_django_app.models import Assessments, Assessment, StudentAssessments

class AssessmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields: list[str] = [
            "id",
            "evaluator",
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
            "evaluator",
            "work",
            "grade",
            "evaluator",
            "date_time",
            "committee_feedback",
            "student_feedback",
        ]

class StudentAssessmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAssessments
        fields: list[str] = [
            "id",
            "grade",
            "work",
            "date_time",
            "student",
        ]
