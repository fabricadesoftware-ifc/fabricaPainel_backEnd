from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    NumberFilter,
)
from core.assessment.infra.assessment_django_app.models import Assessment, StudentAssessments

class AssessmentFilterSet(FilterSet):
    work = CharFilter(field_name="work__id", lookup_expr="icontains")
    grade = NumberFilter()
    evaluator = CharFilter(field_name="evaluator__name", lookup_expr="icontains")
    

    class Meta:
        model = Assessment
        fields = [
            "work",
            "grade",
            "evaluator",
        ]
        
class StudentAssessmentFilterSet(FilterSet):
    work = CharFilter(field_name="work__id", lookup_expr="icontains")
    grade = NumberFilter()
    student = CharFilter(field_name="student__name", lookup_expr="icontains")

    class Meta:
        model = StudentAssessments
        fields = [
            "work",
            "grade",
            "student",
        ]