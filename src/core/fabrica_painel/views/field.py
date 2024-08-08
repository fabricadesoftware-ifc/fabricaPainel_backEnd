from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.fabrica_painel.models.field import Field
from core.fabrica_painel.serializers.field import (
    FieldDetailSerializer,
    FieldWriteSerializer
)


@extend_schema(tags=["field"])
class FieldViewSet(ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldDetailSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return FieldDetailSerializer
        return FieldWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    