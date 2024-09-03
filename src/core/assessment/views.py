from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.assessment.models import Assessment, Assessments
from core.assessment.serializers import (
    AssessmentDetailSerializer,
    AssessmentWriteSerializer,
    AssessmentsDetailSerializer,
    AssessmentsWriteSerializer,
    
)

@extend_schema(tags=["assessment"])
class AssessmentViewSet(ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentDetailSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AssessmentDetailSerializer
        return AssessmentWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]


    from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

@extend_schema(tags=["assessments"])
class AssessmentsViewSet(ModelViewSet):
    queryset = Assessments.objects.all()
    serializer_class = AssessmentsDetailSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AssessmentsDetailSerializer
        return AssessmentsWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    