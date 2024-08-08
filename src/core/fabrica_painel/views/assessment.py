from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.fabrica_painel.models.assessment import Assessment
from core.fabrica_painel.serializers.assessment import (
    AssessmentDetailSerializer,
    AssessmentWriteSerializer 
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