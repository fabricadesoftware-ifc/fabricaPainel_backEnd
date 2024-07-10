from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.fabrica_painel.models.assessments import Assessments
from core.fabrica_painel.serializers.assessments import (
    AssessmentsDetailSerializer,
    AssessmentsWriteSerializer
)


@extend_schema(tags=["assessments"])
class AssessmentsViewSet(ModelViewSet):
    queryset = Assessments.objects.all()
    serializer_class = AssessmentsDetailSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AssessmentsDetailSerializer
        return AssessmentsWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    