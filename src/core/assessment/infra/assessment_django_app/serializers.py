from rest_framework import serializers
from core.assessment.domain.validations import validate_grade_range, validate_assessment_creator
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
        
class StudentAssessmentsWriteSerializer(serializers.ModelSerializer):
    grade = serializers.DecimalField(
        max_digits=4, decimal_places=2, validators=[validate_grade_range]
    )

    class Meta:
        model = StudentAssessments
        fields: list[str] = [
            "grade",
            "work",
            "date_time",
            "student",
        ]
        
    def validate(self, attrs):
       
        try:
            validate_assessment_creator(self.context["request"].user, attrs)
        except serializers.ValidationError as e:
            raise serializers.ValidationError({"detail": str(e)})
        
        return attrs
