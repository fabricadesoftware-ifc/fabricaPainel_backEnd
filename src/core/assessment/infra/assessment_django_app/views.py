from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.assessment.infra.assessment_django_app.models import Assessment, Assessments, StudentAssessments
from core.assessment.infra.assessment_django_app.serializers import (
    AssessmentDetailSerializer,
    AssessmentWriteSerializer,
    StudentAssessmentsSerializer
    
)
from core.assessment.infra.assessment_django_app.filters import AssessmentFilterSet

@extend_schema(tags=["assessment"])
class AssessmentViewSet(ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentDetailSerializer
    filterset_class = AssessmentFilterSet

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AssessmentDetailSerializer
        return AssessmentWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]

class StudentAssessmentsViewSet(ModelViewSet):
    queryset = StudentAssessments.objects.all()
    serializer_class = StudentAssessmentsSerializer

