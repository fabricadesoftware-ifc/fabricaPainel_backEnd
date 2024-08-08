from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema

from core.fabrica_painel.models.keyword import Keyword
from core.fabrica_painel.serializers.keyword import (
    KeywordDetailSerializer,
    KeywordWriteSerializer
)


@extend_schema(tags=["keyword"])
class KeywordViewSet(ModelViewSet):
    queryset = Keyword.objects.all()
    serializer_class = KeywordDetailSerializer

    def get_serializer_class(self):
        if self.action not in ["list", "retrieve"]:
            return KeywordDetailSerializer
        return KeywordWriteSerializer
    http_method_names = ["get", "post", "patch", "delete"]
