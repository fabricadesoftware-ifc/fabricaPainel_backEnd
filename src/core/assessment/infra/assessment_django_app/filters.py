from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
    NumberFilter,
)
from core.assessment.infra.assessment_django_app.models import Assessment

class AssessmentFilterSet(FilterSet):
    work = CharFilter(field_name="work__title", lookup_expr="icontains")
    grade = NumberFilter()
    evaluator = CharFilter(field_name="evaluator__name", lookup_expr="icontains")
    

    class Meta:
        model = Assessment
        fields = [
            "work",
            "grade",
            "evaluator",
        ]