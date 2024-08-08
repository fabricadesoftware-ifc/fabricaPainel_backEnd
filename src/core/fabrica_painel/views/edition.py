from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.fabrica_painel.models.edition import Edition
from core.fabrica_painel.serializers.edition import (
    EditionDetailSerializer,
    EditionWriteSerializer
)


@extend_schema(tags=["edition"])
class EditionViewSet(ModelViewSet):
    queryset = Edition.objects.all()
    serializer_class = EditionDetailSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return EditionDetailSerializer
        return EditionWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    